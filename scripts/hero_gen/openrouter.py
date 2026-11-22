"""OpenRouter Image API client with a hard spend guard and a JSONL cost log.

API (checked 2026-11-22 against openrouter.ai/docs image-generation page):
    POST https://openrouter.ai/api/v1/images
      {model, prompt, aspect_ratio?, resolution?, n?, seed?, quality?,
       output_format?, input_references?: [{type:"image_url", image_url:{url}}]}
    -> {data: [{b64_json, media_type}], usage: {..., cost}}
    GET /api/v1/images/models            capabilities per model
    GET /api/v1/key                      key usage (lifetime USD, lags a little)

The key is read from $OPENROUTER_API_KEY, else ~/.pi/agent/auth.json
("openrouter".key, the lab devcontainer's mount). It is never printed or
logged. Spend is capped per call (SpendGuard) and every request is logged
to hero-work/cost_log.jsonl.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image

from .site import REPO, WORK

API = "https://openrouter.ai/api/v1"
DEFAULT_ESTIMATE = 0.25  # USD per image when a model has no logged cost yet


def _key() -> str:
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"]
    auth = json.loads((Path.home() / ".pi/agent/auth.json").read_text())
    entry = auth["openrouter"]
    return entry if isinstance(entry, str) else entry["key"]


def _headers() -> dict:
    # Generic app title: don't identify the site to the outside service.
    return {"Authorization": f"Bearer {_key()}", "X-Title": "hero-gen"}


def image_models() -> list[dict]:
    r = requests.get(f"{API}/images/models", timeout=30)
    r.raise_for_status()
    d = r.json()
    return d.get("data", d)


class SpendCapError(RuntimeError):
    pass


@dataclass
class CostLog:
    """Append-only JSONL log of every generation (one line per request)."""
    path: Path = WORK / "cost_log.jsonl"

    def append(self, rec: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out

    def total(self, since: str | None = None) -> float:
        return sum(r.get("cost") or 0.0 for r in self.records()
                   if since is None or r.get("time", "") >= since)

    def estimate(self, model: str) -> float:
        """Per-image estimate: the max cost per image seen for this model."""
        seen = [(r.get("cost") or 0.0) / max(r.get("n_images", 1), 1)
                for r in self.records() if r.get("model") == model and r.get("cost")]
        return max(seen) if seen else DEFAULT_ESTIMATE


@dataclass
class SpendGuard:
    """Per-call spend cap: refuses a request whose expected cost exceeds `cap`
    (USD) before anything is sent. Expected cost comes from the log's highest
    seen per-image cost for the model (DEFAULT_ESTIMATE if none)."""
    cap: float
    log: CostLog = field(default_factory=CostLog)

    def check(self, expected: float) -> None:
        if expected > self.cap:
            raise SpendCapError(
                f"spend cap: expected ${expected:.4f} > cap ${self.cap:.2f} "
                f"(raise --max-cost to allow it)")


@dataclass
class Generation:
    images: list[Image.Image]
    paths: list[Path]
    cost: float | None
    model: str
    prompt: str
    params: dict
    id: str | None = None
    seconds: float = 0.0

    def show(self):
        return self.images[0] if len(self.images) == 1 else self.images


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def to_data_url(img: Image.Image | str | Path, max_side: int = 2048) -> str:
    """Encode an image (or path) as a PNG data URL for input_references."""
    if not isinstance(img, Image.Image):
        img = Image.open(img)
    img = img.convert("RGB")
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _lookup_cost(gen_id: str, tries: int = 4) -> float | None:
    for i in range(tries):
        time.sleep(1.5 * (i + 1))
        r = requests.get(f"{API}/generation", params={"id": gen_id},
                         headers=_headers(), timeout=30)
        if r.ok:
            c = r.json().get("data", {}).get("total_cost")
            if c is not None:
                return float(c)
    return None


def generate(prompt: str, model: str, guard: SpendGuard, *, aspect_ratio: str | None = None,
             resolution: str | None = None, n: int = 1, seed: int | None = None,
             references: list | None = None, tag: str = "", extra: dict | None = None,
             expected: float | None = None, timeout: int = 300,
             out_dir: Path | None = None) -> Generation:
    """Generate image(s). Checks the spend guard first, logs cost after.

    references: images/paths/data-URLs passed as input_references (edits).
    """
    expected = (guard.log.estimate(model) * n) if expected is None else expected
    guard.check(expected)

    body = {"model": model, "prompt": prompt, "n": n}
    if aspect_ratio:
        body["aspect_ratio"] = aspect_ratio
    if resolution:
        body["resolution"] = resolution
    if seed is not None:
        body["seed"] = seed
    if references:
        body["input_references"] = [
            {"type": "image_url",
             "image_url": {"url": r if isinstance(r, str) and r.startswith(("data:", "http"))
                           else to_data_url(r)}}
            for r in references]
    body.update(extra or {})
    params = {k: v for k, v in body.items() if k not in ("prompt", "input_references")}
    params["n_references"] = len(references or [])

    t0 = time.time()
    r = requests.post(f"{API}/images", headers=_headers(), json=body, timeout=timeout)
    dt = time.time() - t0
    if not r.ok:
        # failed generations are not billed; log the failure for the record
        guard.log.append({"time": _now(), "model": model, "tag": tag, "params": params,
                          "prompt": prompt, "cost": 0.0, "n_images": 0,
                          "error": f"{r.status_code}: {r.text[:300]}"})
        raise RuntimeError(f"OpenRouter {r.status_code}: {r.text[:500]}")
    d = r.json()
    gen_id = d.get("id")
    cost = (d.get("usage") or {}).get("cost")
    if cost is None and gen_id:
        cost = _lookup_cost(gen_id)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    gdir = out_dir or (WORK / "gen")
    gdir.mkdir(parents=True, exist_ok=True)
    images, paths = [], []
    for i, item in enumerate(d.get("data", [])):
        if item.get("b64_json"):
            raw = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            raw = requests.get(item["url"], timeout=60).content
        else:
            continue
        img = Image.open(io.BytesIO(raw))
        img.load()
        ext = (item.get("media_type") or "image/png").split("/")[-1].replace("jpeg", "jpg")
        p = gdir / f"{stamp}_{_slug(model)}_{_slug(tag) or 'img'}_{i}.{ext}"
        p.write_bytes(raw)
        images.append(img)
        paths.append(p)

    guard.log.append({"time": _now(), "model": model, "tag": tag, "params": params,
                      "prompt": prompt, "cost": cost, "n_images": len(images),
                      "id": gen_id, "seconds": round(dt, 1),
                      "sizes": [im.size for im in images],
                      "paths": [_rel(p) for p in paths]})
    return Generation(images, paths, cost, model, prompt, params, gen_id, dt)
