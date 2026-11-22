# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=13.0.0", "numpy", "requests>=2.34.2"]
# ///
"""Tests for scripts/hero_gen and scripts/hero.py. No network, no spend.

Run with:  uv run tests/test_hero_gen.py   (scripts/check does)

The first part is the lab's test suite (~/lab/or-img-gen), ported from
pytest to unittest; the rest covers the site port and the CLI. Every test
that could reach the API stubs requests.post/get.
"""

import base64
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import hero  # noqa: E402
from hero_gen import contrast, crop, export, openrouter, preview, prompts, site  # noqa: E402


def tmpdir(test):
    d = tempfile.TemporaryDirectory()
    test.addCleanup(d.cleanup)
    return Path(d.name)


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = hero.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def no_network(test):
    """Patch requests in openrouter so any call fails the test."""
    for name in ("post", "get"):
        p = mock.patch.object(openrouter.requests, name,
                              side_effect=AssertionError(f"network call: requests.{name}"))
        test.addCleanup(p.stop)
        p.start()


# --- ported from the lab ------------------------------------------------------

class LabContrast(unittest.TestCase):

    def test_luminance_endpoints(self):
        self.assertAlmostEqual(contrast.luminance("#000000"), 0.0)
        self.assertAlmostEqual(contrast.luminance("#FFFFFF"), 1.0)
        self.assertAlmostEqual(contrast.contrast("#000", "#fff"), 21.0)

    def test_site_pairs_pass_aa(self):
        for m in site.MODES.values():
            self.assertGreaterEqual(contrast.contrast(m["fg"], m["bg"]), 4.5)

    def test_luminance_array_matches_scalar(self):
        arr = np.array([[[230, 180, 80], [143, 80, 0]]], dtype=np.uint8)
        lum = contrast.luminance(arr)
        self.assertAlmostEqual(lum[0, 0], contrast.luminance("#E6B450"))
        self.assertAlmostEqual(lum[0, 1], contrast.luminance("#8F5000"))

    def test_no_single_background_passes_both_modes(self):
        for ratio in (site.AA_NORMAL, site.AA_LARGE):
            dark_max, _ = contrast.luminance_limits(site.MODES["dark"]["fg"], ratio)
            _, light_min = contrast.luminance_limits(site.MODES["light"]["fg"], ratio)
            self.assertLess(dark_max, light_min)

    def test_region_stats_flat_background(self):
        img = Image.new("RGB", (100, 50), site.MODES["dark"]["bg"])
        s = contrast.region_stats(img, site.Box(10, 10, 60, 40), site.MODES["dark"]["fg"], 4.5)
        self.assertTrue(s["ok"])
        self.assertEqual(s["pass_share"], 1.0)
        self.assertAlmostEqual(
            s["p05"], contrast.contrast(site.MODES["dark"]["fg"], site.MODES["dark"]["bg"]),
            delta=0.01)

    def test_tone_zone_reaches_target(self):
        for mode, start in [("dark", (200, 200, 200)), ("light", (20, 40, 60))]:
            with self.subTest(mode=mode):
                img = Image.new("RGB", (200, 100), start)
                box = site.Box(50, 30, 150, 70)
                out = contrast.tone_zone(img, mode, box, feather=10)
                s = contrast.region_stats(out, box, site.MODES[mode]["fg"], site.AA_NORMAL)
                self.assertTrue(s["ok"])
                self.assertEqual(out.getpixel((0, 0)), start)  # far corner untouched


class LabCrop(unittest.TestCase):

    def test_cover_box_wide_image_on_phone_crops_sides(self):
        b = crop.cover_box(4000, 1000, 390, 190)  # 4:1 into ~2:1
        self.assertAlmostEqual(b.h, 1000)
        self.assertAlmostEqual(b.w, 1000 * 390 / 190)
        self.assertAlmostEqual((b.x0 + b.x1) / 2, 2000)

    def test_cover_box_on_very_wide_viewport_crops_height(self):
        b = crop.cover_box(2400, 400, 2560, 190)  # 6:1 into 13.5:1
        self.assertAlmostEqual(b.w, 2400)
        self.assertAlmostEqual(b.h, 2400 * 190 / 2560)
        self.assertAlmostEqual((b.y0 + b.y1) / 2, 200)

    def test_cover_view_size(self):
        img = Image.new("RGB", (2400, 400))
        self.assertEqual(crop.cover_view(img, 390).size, (390, site.HERO_HEIGHT))
        self.assertEqual(crop.cover_view(img, 390, scale=2).size, (780, 2 * site.HERO_HEIGHT))

    def test_always_visible_inside_every_view(self):
        av = crop.always_visible(2400, 400)
        for w in site.VIEWPORTS.values():
            b = crop.cover_box(2400, 400, w, site.HERO_HEIGHT)
            self.assertTrue(b.x0 <= av.x0 + 1e-9 and av.x1 <= b.x1 + 1e-9)
            self.assertTrue(b.y0 <= av.y0 + 1e-9 and av.y1 <= b.y1 + 1e-9)

    def test_center_crop_aspect(self):
        for size, aspect in [((2048, 1024), 6.0), ((1000, 1000), 3.0), ((4096, 512), 6.0)]:
            with self.subTest(size=size, aspect=aspect):
                out = crop.center_crop(Image.new("RGB", size), aspect)
                self.assertAlmostEqual(out.width / out.height, aspect, delta=aspect * 0.01)

    def test_fit_width_never_upsamples(self):
        self.assertEqual(crop.fit_width(Image.new("RGB", (800, 100)), 2400).size, (800, 100))
        self.assertEqual(crop.fit_width(Image.new("RGB", (4800, 800)), 2400).size, (2400, 400))

    def test_text_zone_is_centred(self):
        tz = crop.text_zone(2400, 400)
        self.assertTrue(tz.x0 < 1200 < tz.x1)


class LabSite(unittest.TestCase):

    def test_hero_height_and_column(self):
        self.assertTrue(185 <= site.HERO_HEIGHT <= 195)
        self.assertEqual(site.column(1920).w, site.MEASURE)
        self.assertEqual(site.column(390).w, 390 - 2 * site.PAD_SIDE)
        self.assertAlmostEqual(site.column(1920).x0, (1920 - 672) / 2)

    def test_front_matter_parsing(self):
        p = tmpdir(self) / "post.md"
        p.write_text('+++\ntitle = "T"\ndescription = "D"\n[extra]\nmath = true\n+++\nbody\n')
        fm = site.read_front_matter(p)
        self.assertEqual(fm["title"], "T")
        self.assertIs(fm["extra"]["math"], True)

    def test_from_post_uses_title_and_description(self):
        p = tmpdir(self) / "post.md"
        p.write_text('+++\ntitle = "Heat engines"\ndescription = "Carnot"\n+++\n')
        text = prompts.from_post(p).text()
        self.assertIn("Heat engines", text)
        self.assertIn("Carnot", text)
        self.assertEqual(prompts.from_post(p).status, prompts.DRAFT)


class LabExport(unittest.TestCase):

    def test_prepare_shape(self):
        self.assertEqual(export.prepare(Image.new("RGB", (5856, 704))).size, (2880, 360))
        self.assertEqual(export.prepare(Image.new("RGB", (4096, 1024)), aspect=6.0,
                                        width=2400).size, (2400, 400))

    def test_encode_formats_roundtrip(self):
        img = Image.new("RGB", (240, 40), (19, 23, 33))
        for fmt, o in [("webp", {}), ("jpeg", {}), ("png", {"colors": 16})]:
            self.assertGreater(len(export.encode(img, fmt, **o)), 0)

    def test_save_does_not_overwrite(self):
        d = tmpdir(self)
        img = Image.new("RGB", (80, 10))
        p1, line1 = export.save(img, "x", directory=d)
        p2, _ = export.save(img, "x", directory=d)
        p3, _ = export.save(img, "x", directory=d, overwrite=True)
        self.assertEqual((p1.name, p2.name), ("x.webp", "x-2.webp"))
        self.assertEqual(p3, p1)
        self.assertEqual(line1, 'hero_image = "img/x.webp"')


class LabCost(unittest.TestCase):

    def test_cost_log_total_and_estimate(self):
        path = tmpdir(self) / "log.jsonl"
        log = openrouter.CostLog(path)
        log.append({"time": "2026-01-01T00:00:00", "model": "m", "cost": 0.04, "n_images": 1})
        log.append({"time": "2026-01-02T00:00:00", "model": "m", "cost": 0.10, "n_images": 2})
        with path.open("a") as f:
            f.write("{truncated\n")
        self.assertAlmostEqual(log.total(), 0.14)
        self.assertAlmostEqual(log.total(since="2026-01-02"), 0.10)
        self.assertAlmostEqual(log.estimate("m"), 0.05)
        self.assertEqual(log.estimate("other"), openrouter.DEFAULT_ESTIMATE)

    def test_spend_guard_blocks_over_cap(self):
        # Adapted: the site port caps each call, not a persistent window.
        g = openrouter.SpendGuard(cap=0.10, log=openrouter.CostLog(tmpdir(self) / "l"))
        g.check(0.05)
        with self.assertRaises(openrouter.SpendCapError):
            g.check(0.2)


# --- site port ----------------------------------------------------------------

def css_hero_colors():
    """{'dark': (fg, bg), 'light': (fg, bg)} from static/style.css."""
    css = (REPO / "static" / "style.css").read_text(encoding="utf-8")
    light = re.search(r"@media\s*\(\s*prefers-color-scheme\s*:\s*light\s*\)\s*\{\s*:root\s*\{"
                      r"(?P<body>[^}]*)\}", css)
    dark = re.search(r"(?<![\w-]):root\s*\{(?P<body>[^}]*)\}", css)

    def pick(body):
        get = lambda n: re.search(rf"{n}:\s*(#[0-9A-Fa-f]+)", body).group(1).upper()  # noqa: E731
        return get("--hero-fg"), get("--hero-bg")
    return {"dark": pick(dark["body"]), "light": pick(light["body"])}


class SitePort(unittest.TestCase):

    def test_modes_match_style_css(self):
        css = css_hero_colors()
        for mode in ("dark", "light"):
            self.assertEqual((site.MODES[mode]["fg"].upper(), site.MODES[mode]["bg"].upper()),
                             css[mode], mode)

    def test_hero_title_from_config(self):
        self.assertEqual(site.hero_title(), "Jef with one f")

    def test_title_box_tracks_title_length(self):
        default = site.title_box(1920)
        self.assertAlmostEqual(default.w, len(site.hero_title()) * site.TITLE_EM_PER_CHAR
                               * site.TITLE_PX)
        self.assertLess(site.title_box(1920, 100).w, site.title_box(1920, 400).w)
        self.assertLessEqual(site.title_box(390, 10000).x1, site.column(390).x1)

    def test_from_post_reads_repo_posts(self):
        text = prompts.from_post("thermo").text()
        self.assertIn("Basics of thermodynamics", text)

    def test_configured_pair_passes_contrast(self):
        import tomllib
        extra = tomllib.loads((REPO / "config.toml").read_text(encoding="utf-8"))["extra"]
        for key, mode in [("hero_image", "dark"), ("hero_image_light", "light")]:
            with self.subTest(key=key):
                self.assertTrue(extra.get(key), f"{key} not set in config.toml")
                path = REPO / "static" / extra[key]
                self.assertLess(path.stat().st_size, 150 * 1024, f"{path.name} too large")
                _, stats = preview.sheet(Image.open(path), modes=(mode,), scale=0.25)
                self.assertTrue(all(s["ok"] for s in stats.values()),
                                f"{path.name} fails {mode}: {preview.worst(stats)}")

    def test_hero_work_gitignored(self):
        r = subprocess.run(["git", "check-ignore", "-q", "hero-work/x.png"], cwd=REPO)
        self.assertEqual(r.returncode, 0, "hero-work/ is not gitignored")


# --- API client (stubbed) -------------------------------------------------------

def png_b64(color=(19, 23, 33)):
    buf = io.BytesIO()
    Image.new("RGB", (64, 8), color).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


class FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code, self.ok = status, 200 <= status < 300
        self._payload, self.text = payload, text

    def json(self):
        return self._payload


class Client(unittest.TestCase):

    def setUp(self):
        self.work = tmpdir(self)
        self.log = openrouter.CostLog(self.work / "cost_log.jsonl")

    def test_max_cost_blocks_before_request(self):
        no_network(self)
        guard = openrouter.SpendGuard(cap=0.01, log=self.log)
        with self.assertRaises(openrouter.SpendCapError):
            openrouter.generate("p", "some/model", guard, out_dir=self.work / "gen")
        self.assertEqual(self.log.records(), [])

    def test_failed_request_logged_zero_cost(self):
        guard = openrouter.SpendGuard(cap=1.0, log=self.log)
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "k"}), \
                mock.patch.object(openrouter.requests, "post",
                                  return_value=FakeResponse(400, text="bad request")):
            with self.assertRaises(RuntimeError):
                openrouter.generate("p", "some/model", guard, out_dir=self.work / "gen")
        (rec,) = self.log.records()
        self.assertEqual(rec["cost"], 0.0)
        self.assertIn("400", rec["error"])

    def test_key_not_logged_or_printed(self):
        sentinel = "sk-or-SENTINEL-0123456789"
        seen = {}

        def fake_post(url, headers, json, timeout):
            seen.update(headers)
            return FakeResponse(200, {"id": "gen-1", "usage": {"cost": 0.01},
                                      "data": [{"b64_json": png_b64(),
                                                "media_type": "image/png"}]})
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": sentinel}), \
                mock.patch.object(openrouter.requests, "post", side_effect=fake_post):
            code, out, err = run_cli("--work-dir", str(self.work), "generate",
                                     "--subject", "a test scene", "--max-cost", "1")
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["Authorization"], f"Bearer {sentinel}")  # the key was used
        self.assertEqual(seen["X-Title"], "hero-gen")
        for name, text in [("stdout", out), ("stderr", err),
                           ("cost log", (self.work / "cost_log.jsonl").read_text())]:
            self.assertNotIn(sentinel, text, name)
        self.assertEqual(len(list((self.work / "gen").iterdir())), 1)


# --- CLI (offline commands) -----------------------------------------------------

DARK_BG = site.MODES["dark"]["bg"]
LIGHT_BG = site.MODES["light"]["bg"]


class Cli(unittest.TestCase):

    def setUp(self):
        no_network(self)
        self.work = tmpdir(self)
        self.static = tmpdir(self)
        self.src = self.work / "src.png"

    def image(self, color, size=(5856, 704)):
        Image.new("RGB", size, color).save(self.src)
        return str(self.src)

    def cli(self, *argv):
        return run_cli("--work-dir", str(self.work), "--static-dir", str(self.static), *argv)

    def test_cli_check_reports_modes(self):
        code, out, _ = self.cli("check", self.image(DARK_BG), "--mode", "dark")
        self.assertEqual(code, 0)
        for view in site.VIEWPORTS:
            self.assertIn(view, out)
        self.assertTrue((self.work / "previews" / "src_dark.jpg").is_file())
        code, out, _ = self.cli("check", self.image(LIGHT_BG), "--mode", "dark")
        self.assertEqual(code, 1)
        self.assertIn("NO", out)

    def test_cli_export_writes_static(self):
        code, out, err = self.cli("export", self.image(DARK_BG), "--name", "hero-x-night",
                                  "--mode", "dark")
        self.assertEqual(code, 0, err)
        path = self.static / "img" / "hero-x-night.webp"
        self.assertEqual(Image.open(path).size, (2880, 360))
        self.assertIn('hero_image = "img/hero-x-night.webp"', out)
        code, out, err = self.cli("export", self.image(LIGHT_BG), "--name", "hero-x-day",
                                  "--mode", "light")
        self.assertEqual(code, 0, err)
        self.assertIn('hero_image_light = "img/hero-x-day.webp"', out)

    def test_cli_export_refuses_overwrite(self):
        self.assertEqual(self.cli("export", self.image(DARK_BG), "--name", "n",
                                  "--mode", "dark")[0], 0)
        path = self.static / "img" / "n.webp"
        before = path.read_bytes()
        code, _, err = self.cli("export", self.image((0, 0, 0)), "--name", "n", "--mode", "dark")
        self.assertEqual(code, 1)
        self.assertIn("exists", err)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["n.webp"])

    def test_cli_export_contrast_gate(self):
        pale = self.image(LIGHT_BG)
        code, _, err = self.cli("export", pale, "--name", "bad", "--mode", "dark")
        self.assertEqual(code, 1)
        self.assertIn("contrast", err)
        self.assertFalse((self.static / "img" / "bad.webp").exists())
        code, _, err = self.cli("export", pale, "--name", "bad", "--mode", "dark", "--force")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.static / "img" / "bad.webp").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
