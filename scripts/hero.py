# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=13.0.0", "numpy", "requests>=2.34.2"]
# ///
"""Generate, check, and export hero banners (OpenRouter image models).

Usage:  uv run scripts/hero.py COMMAND ...   (see notes/hero-images.md)

  models     image models and their widest aspect ratio (free)
  generate   new image from a theme, a post, or a subject  (costs money)
  twin       redraw an image as its day/night twin          (costs money)
  check      contrast of the hero text per viewport + preview sheet (offline)
  export     crop/resize/WebP into static/img/, gated on contrast (offline)
  spend      total logged OpenRouter cost

Paid commands refuse before sending if the expected cost exceeds --max-cost.
Raw generations, previews, and the cost log go to hero-work/ (gitignored).
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

from hero_gen import crop, export, openrouter, preview, prompts, site

DEFAULT_MODEL = "google/gemini-nano-banana-2.1"


def _ratio(ar: str) -> float:
    w, _, h = ar.partition(":")
    try:
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        return 0.0


def cmd_models(args):
    rows = []
    for m in openrouter.image_models():
        ars = ((m.get("supported_parameters") or {}).get("aspect_ratio") or {}).get("values", [])
        widest = max(ars, key=_ratio, default="")
        rows.append((_ratio(widest), m.get("id", "?"), widest or "-"))
    for _, mid, widest in sorted(rows, reverse=True):
        print(f"{widest:>6}  {mid}")
    return 0


def _generate(args, prompt_text, references=None):
    work = Path(args.work_dir)
    log = openrouter.CostLog(work / "cost_log.jsonl")
    guard = openrouter.SpendGuard(cap=args.max_cost, log=log)
    try:
        gen = openrouter.generate(
            prompt_text, args.model, guard, aspect_ratio=args.aspect,
            resolution=args.resolution, n=args.n, references=references,
            tag=args.tag, out_dir=work / "gen")
    except openrouter.SpendCapError as err:
        print(f"hero: {err}", file=sys.stderr)
        return 1
    except RuntimeError as err:
        print(f"hero: generation failed: {err}", file=sys.stderr)
        return 1
    cost = "unknown" if gen.cost is None else f"${gen.cost:.4f}"
    for p in gen.paths:
        print(p)
    print(f"cost {cost}, {gen.seconds:.0f}s, logged total ${log.total():.4f}")
    return 0


def cmd_generate(args):
    if args.theme:
        p = prompts.theme(args.theme, palette=args.palette)
    elif args.post:
        p = prompts.from_post(args.post, palette=args.palette, setting=args.setting)
    else:
        p = prompts.Prompt(args.subject, palette=args.palette)
    return _generate(args, p.text())


def cmd_twin(args):
    instr = prompts.day_edit() if args.to == "day" else prompts.night_edit()
    return _generate(args, instr, references=[args.src])


def _check(img, mode, work, stem):
    sheet, stats = preview.sheet(img, modes=(mode,))
    out = Path(work) / "previews" / f"{stem}_{mode}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=85)
    print(preview.stats_table(stats))
    print(preview.worst(stats))
    print(f"preview: {out}")
    return all(s["ok"] for s in stats.values())


def cmd_check(args):
    img = Image.open(args.img).convert("RGB")
    return 0 if _check(img, args.mode, args.work_dir, Path(args.img).stem) else 1


def cmd_export(args):
    img_dir = Path(args.static_dir) / "img"
    target = img_dir / f"{args.name}.webp"
    if target.exists():
        print(f"hero: {target} exists; pick another --name", file=sys.stderr)
        return 1
    banner = export.prepare(Image.open(args.src), aspect=args.aspect, width=args.width)
    if not _check(banner, args.mode, args.work_dir, args.name) and not args.force:
        print("hero: contrast fails for this mode; not exported (--force to override)",
              file=sys.stderr)
        return 1
    path, line = export.save(banner, args.name, "webp", directory=img_dir,
                             quality=args.quality)
    if args.mode == "light":
        line = line.replace("hero_image =", "hero_image_light =", 1)
    print(f"wrote {path} ({path.stat().st_size / 1024:.0f} KB, {banner.width}x{banner.height})")
    print(line)
    return 0


def cmd_spend(args):
    log = openrouter.CostLog(Path(args.work_dir) / "cost_log.jsonl")
    print(f"logged total ${log.total():.4f} over {len(log.records())} requests")
    return 0


def parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--work-dir", default=str(site.WORK), help=argparse.SUPPRESS)
    ap.add_argument("--static-dir", default=str(site.STATIC), help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("models", help="list image models (free)").set_defaults(fn=cmd_models)

    def paid(p):
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument("--aspect", default="8:1", help="aspect ratio sent to the model")
        p.add_argument("--resolution", default="2K")
        p.add_argument("--n", type=int, default=1)
        p.add_argument("--max-cost", type=float, default=0.50,
                       help="refuse if the expected cost (USD) is higher (default 0.50)")
        p.add_argument("--tag", default="")

    g = sub.add_parser("generate", help="new image (costs money)")
    src = g.add_mutually_exclusive_group(required=True)
    src.add_argument("--theme", choices=sorted(prompts.THEMES))
    src.add_argument("--post", help="post slug; uses its title and description")
    src.add_argument("--subject", help="free-text subject")
    g.add_argument("--palette", choices=["night", "day"], default="night")
    g.add_argument("--setting", help="theme to place a --post subject in")
    paid(g)
    g.set_defaults(fn=cmd_generate)

    t = sub.add_parser("twin", help="redraw as day/night twin (costs money)")
    t.add_argument("src")
    t.add_argument("--to", choices=["day", "night"], required=True)
    paid(t)
    t.set_defaults(fn=cmd_twin)

    c = sub.add_parser("check", help="hero text contrast per viewport (offline)")
    c.add_argument("img")
    c.add_argument("--mode", choices=["dark", "light"], required=True)
    c.set_defaults(fn=cmd_check)

    e = sub.add_parser("export", help="banner into static/img/ (offline)")
    e.add_argument("src")
    e.add_argument("--name", required=True, help="file name without extension")
    e.add_argument("--mode", choices=["dark", "light"], required=True)
    e.add_argument("--aspect", type=float, default=export.DEFAULT_ASPECT)
    e.add_argument("--width", type=int, default=export.DEFAULT_WIDTH)
    e.add_argument("--quality", type=int, default=75)
    e.add_argument("--force", action="store_true", help="export even if contrast fails")
    e.set_defaults(fn=cmd_export)

    sub.add_parser("spend", help="total logged cost").set_defaults(fn=cmd_spend)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
