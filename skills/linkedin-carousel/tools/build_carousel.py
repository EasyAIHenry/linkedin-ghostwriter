#!/usr/bin/env python3
"""Build a LinkedIn document carousel as one self-contained HTML file. Standard library only.

Usage: python3 build_carousel.py slides.json [-o carousel.html]

slides.json:
{
  "title": "5 checks before you send an invoice",
  "footer": "Your name, what you do",                      (optional)
  "brand": {"background": "#FAFAF7", "text": "#141414", "accent": "#2F5BEA",
            "heading_font": "Inter", "body_font": "Inter"},  (all optional)
  "slides": [{"heading": "...", "body": "..."}, ...]          (6 to 10 slides)
}

Every slide is one 1080x1350 page (CSS @page size), so printing to PDF gives one page per slide.
ERROR (exit code 1): not 6 to 10 slides, a slide with no heading, a colour that is not #RGB or #RRGGBB,
a font name with characters other than letters, digits, spaces, dots, underscores and hyphens.
WARN: headings over 60 characters, bodies over 280 characters (text may not fit), em dashes, exclamation marks.
"""
import argparse
import html
import json
import re
import sys

MIN_SLIDES, MAX_SLIDES = 6, 10
WIDTH, HEIGHT = 1080, 1350
DEFAULT_BRAND = {"background": "#FAFAF7", "text": "#141414", "accent": "#2F5BEA"}
SYSTEM_FONTS = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
COLOUR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
FONT = re.compile(r"^[A-Za-z0-9 ._-]{1,60}$")
DASH = re.compile(r"[\u2014\u2013]")


def validate(data):
    """Return (errors, warnings) for a parsed slides.json."""
    errors, warns = [], []
    if not isinstance(data, dict):
        return ["the file must hold one JSON object"], []
    slides = data.get("slides")
    if not isinstance(slides, list):
        return ['"slides" must be a list of {"heading", "body"}'], []
    if not MIN_SLIDES <= len(slides) <= MAX_SLIDES:
        errors.append(f"{len(slides)} slides (use {MIN_SLIDES} to {MAX_SLIDES})")
    for i, s in enumerate(slides, 1):
        if not isinstance(s, dict):
            errors.append(f"slide {i} must be an object")
            continue
        heading, body = s.get("heading", ""), s.get("body", "")
        if not isinstance(heading, str) or not heading.strip():
            errors.append(f"slide {i} has no heading")
            heading = ""
        if not isinstance(body, str):
            errors.append(f"slide {i} body must be text")
            body = ""
        if len(heading) > 60:
            warns.append(f"slide {i} heading is {len(heading)} characters (60 at most fits well)")
        if len(body) > 280:
            warns.append(f"slide {i} body is {len(body)} characters (280 at most fits well)")
        if DASH.search(heading + body):
            warns.append(f"slide {i} has an em or en dash")
        if "!" in heading + body:
            warns.append(f"slide {i} has an exclamation mark")
    title = data.get("title", "")
    if title and not isinstance(title, str):
        errors.append('"title" must be text')
    footer = data.get("footer", "")
    if footer and not isinstance(footer, str):
        errors.append('"footer" must be text')
    brand = data.get("brand", {})
    if not isinstance(brand, dict):
        errors.append('"brand" must be an object')
        brand = {}
    for key in ("background", "text", "accent"):
        if key in brand and not (isinstance(brand[key], str) and COLOUR.match(brand[key])):
            errors.append(f"brand {key} {brand[key]!r} is not a #RGB or #RRGGBB colour")
    for key in ("heading_font", "body_font"):
        if key in brand and not (isinstance(brand[key], str) and FONT.match(brand[key])):
            errors.append(f"brand {key} {brand[key]!r} is not a plain font name")
    return errors, warns


def _font_stack(name):
    return f'"{name}", {SYSTEM_FONTS}' if name else SYSTEM_FONTS


def _paragraphs(body):
    parts = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return "".join("<p>" + html.escape(p).replace("\n", "<br>") + "</p>" for p in parts)


def render(data):
    """Return the carousel HTML. Call validate() first."""
    slides = data["slides"]
    brand = dict(DEFAULT_BRAND, **data.get("brand", {}))
    title = data.get("title") or slides[0]["heading"]
    footer = html.escape(data.get("footer", ""))
    css = f"""
@page {{ size: {WIDTH}px {HEIGHT}px; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: {brand['background']}; }}
body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.slide {{ width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; position: relative; display: flex;
  flex-direction: column; padding: 120px 96px 140px; background: {brand['background']}; color: {brand['text']};
  font-family: {_font_stack(brand.get('body_font'))}; }}
.slide + .slide {{ break-before: page; page-break-before: always; }}
.bar {{ position: absolute; top: 0; left: 0; right: 0; height: 18px; background: {brand['accent']}; }}
.num {{ font-size: 32px; font-weight: 700; color: {brand['accent']}; margin-bottom: 40px; }}
h1, h2 {{ font-family: {_font_stack(brand.get('heading_font'))}; margin: 0 0 48px; line-height: 1.08;
  letter-spacing: -0.01em; }}
h1 {{ font-size: 104px; }}
h2 {{ font-size: 76px; }}
.body p {{ font-size: 42px; line-height: 1.38; margin: 0 0 28px; }}
.cover {{ justify-content: center; }}
.cover .body p {{ font-size: 46px; }}
.last {{ justify-content: center; }}
.last h2 {{ color: {brand['accent']}; font-size: 88px; }}
.foot {{ position: absolute; left: 96px; right: 96px; bottom: 64px; display: flex; justify-content: space-between;
  font-size: 28px; opacity: 0.7; }}
""".strip()
    pages, n = [], len(slides)
    for i, s in enumerate(slides, 1):
        kind = "cover" if i == 1 else "last" if i == n else "inner"
        tag = "h1" if i == 1 else "h2"
        num = f'<div class="num">{i - 1:02d}</div>' if kind == "inner" else ""
        pages.append(
            f'<section class="slide {kind}"><div class="bar"></div>{num}'
            f'<{tag}>{html.escape(s["heading"].strip())}</{tag}>'
            f'<div class="body">{_paragraphs(s.get("body", ""))}</div>'
            f'<div class="foot"><span>{footer}</span><span>{i} / {n}</span></div></section>')
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            f"<title>{html.escape(title)}</title>\n<style>\n{css}\n</style>\n</head>\n<body>\n"
            + "\n".join(pages) + "\n</body>\n</html>\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="slides.json")
    ap.add_argument("-o", "--out", default="carousel.html")
    a = ap.parse_args(argv)
    try:
        with open(a.file, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print("ERROR", f"cannot read {a.file}: {e}")
        return 1
    errors, warns = validate(data)
    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errors:
        return 1
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(render(data))
    print(f"wrote {a.out}: {len(data['slides'])} slides, {len(warns)} warn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
