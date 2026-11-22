"""Hero-banner generation helpers for this site (ported from ~/lab/or-img-gen).

CLI front end: scripts/hero.py. Workflow and findings: notes/hero-images.md.

Modules:
    site       hero geometry, colors, text boxes, post front matter
    contrast   WCAG luminance/contrast, text-region contrast stats, zone toning
    crop       `background-size: cover` maths, center crops, resizing
    preview    render the banner with nav + title overlaid, per mode and width
    prompts    style preamble + subject prompt builder (drafts need jef's approval)
    openrouter OpenRouter image API client with spend guard and cost log
    export     web export (WebP/PNG/JPEG) with size report + front-matter line
"""
