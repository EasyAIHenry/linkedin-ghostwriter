#!/usr/bin/env python3
"""Audit your own LinkedIn post results and print a markdown report. Standard library only.

Usage: python3 audit_posts.py FILE [--day-first] [--rank-by er|impressions]

FILE is a CSV (LinkedIn's post analytics export saved as CSV, a Buffer metrics export, or your own sheet)
or a markdown file with a table, such as linkedin-posts/log.md. Column names are matched loosely:
date, text (or first line), impressions, reactions, comments, reposts, plus an optional time, post type
and length. Numbers like "1,234", "1.2k" and "3.4%" are read. Title rows above the header are skipped.

Engagement rate per post = (reactions + comments + reposts) / impressions. A missing column counts as 0.
Slash dates are read month first (10/05/2026 = 5 October) unless the first number is over 12 or you pass
--day-first. Times are read as written in the file; no time-zone change.
Exit code 0 on success, 2 when the file has no usable impressions column or no posts.
"""
import argparse
import csv
import datetime as dt
import io
import re
import statistics
import sys

SMALL_SAMPLE = 20
MIN_GROUP = 3
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
ENGAGEMENT = ("reactions", "comments", "reposts")

# Exact matches on the header with case, spaces and punctuation removed.
ALIASES = {
    "date": ["date", "postdate", "createddate", "created", "createdat", "published", "publishedat", "publishdate",
             "publisheddate", "posted", "postedat", "postedon", "sentat", "sent", "datetime", "timestamp"],
    "time": ["time", "posttime", "publishtime", "publishedtime", "timeposted", "hour"],
    "text": ["text", "posttext", "post", "content", "postcontent", "message", "commentary", "updatetext",
             "update", "caption", "body", "firstline", "posttitle", "title", "slug"],
    "impressions": ["impressions", "impression", "views", "postimpressions", "totalimpressions",
                    "impressionstotal", "impressioncount", "impressionsorganic"],
    "reactions": ["reactions", "likes", "reactionstotal", "totalreactions", "reactioncount", "likecount"],
    "comments": ["comments", "commentstotal", "totalcomments", "commentcount"],
    "reposts": ["reposts", "shares", "reshares", "repostcount", "sharecount", "totalreposts", "totalshares"],
    "engagements": ["engagements", "engagement", "totalengagements", "engagementstotal"],
    "type": ["type", "posttype", "format", "mediatype", "contenttype", "media"],
    "length": ["length", "characters", "charcount", "chars", "postlength", "charactercount"],
}
# Fallback: the header contains one of these. Headers with these words are never used this way.
CONTAINS = {
    "impressions": ["impression", "views"],
    "reactions": ["reaction", "likes"],
    "comments": ["comment"],
    "reposts": ["repost", "share"],
    "date": ["date", "published", "posted"],
    "text": ["text", "content", "commentary", "caption", "title"],
}
NEVER = ("unique", "rate", "percent", "url", "link")


def norm(header):
    return re.sub(r"[^a-z0-9]", "", str(header).lower())


def parse_number(value):
    """'1,234' -> 1234.0, '1.2k' -> 1200.0, '3.4%' -> 3.4, blank or '-' -> None."""
    if value is None:
        return None
    s = str(value).strip().lower()
    for ch in (",", " ", " ", "_", "'"):
        s = s.replace(ch, "")
    if s in ("", "-", "--", "n/a", "na", "none", "null"):
        return None
    s = s.rstrip("%")
    mult = 1.0
    if s.endswith("k"):
        mult, s = 1000.0, s[:-1]
    elif s.endswith("m"):
        mult, s = 1000000.0, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def _month(word):
    return MONTHS.get(word[:3].lower())


def _find_date(s, day_first):
    m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        return dt.date(int(m[1]), int(m[2]), int(m[3])), m
    m = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", s)
    if m:
        a, b, y = int(m[1]), int(m[2]), int(m[3])
        y = y + 2000 if y < 100 else y
        month, day = (b, a) if (day_first and b <= 12) or a > 12 else (a, b)
        return dt.date(y, month, day), m
    for m in re.finditer(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})", s):
        if _month(m[2]):
            return dt.date(int(m[3]), _month(m[2]), int(m[1])), m
    for m in re.finditer(r"([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", s):
        if _month(m[1]):
            return dt.date(int(m[3]), _month(m[1]), int(m[2])), m
    return None, None


def _find_time(s):
    m = re.search(r"(\d{1,2}):(\d{2})(?::\d{2}(?:\.\d+)?)?(?:\s*([ap])\.?m\b\.?)?", s, re.I)
    if m:
        h, mi, half = int(m[1]), int(m[2]), (m[3] or "").lower()
    else:
        m = re.search(r"\b(\d{1,2})\s*([ap])\.?m\b", s, re.I)
        if m:
            h, mi, half = int(m[1]), 0, m[2].lower()
        elif re.fullmatch(r"\d{1,2}", s.strip()):
            h, mi, half = int(s.strip()), 0, ""
        else:
            return None
    if half == "p" and h < 12:
        h += 12
    if half == "a" and h == 12:
        h = 0
    if h > 23 or mi > 59:
        return None
    return h, mi


def parse_when(date_s, time_s="", day_first=False):
    """Return (date or None, (hour, minute) or None) from a date cell and an optional time cell."""
    s = (date_s or "").strip()
    try:
        d, m = _find_date(s, day_first)
    except ValueError:
        d, m = None, None
    rest = s[:m.start()] + " " + s[m.end():] if m else s
    t = _find_time(rest) if rest.strip() else None
    if t is None and (time_s or "").strip():
        t = _find_time(time_s)
    return d, t


def ends_with_question(text):
    """True when the last line that is not only hashtags ends with a question mark."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    while lines and all(w.startswith("#") for w in lines[-1].split()):
        lines.pop()
    return bool(lines) and lines[-1].rstrip(" \"')”’").endswith("?")


def find_columns(header):
    keys = [norm(h) for h in header]
    cols, used = {}, set()
    for field, names in ALIASES.items():
        for i, k in enumerate(keys):
            if i not in used and k in names:
                cols[field] = i
                used.add(i)
                break
    for field, parts in CONTAINS.items():
        if field in cols:
            continue
        for i, k in enumerate(keys):
            if i in used or any(bad in k for bad in NEVER):
                continue
            if any(p in k for p in parts):
                cols[field] = i
                used.add(i)
                break
    return cols


def _usable(cols):
    return "impressions" in cols and any(f in cols for f in ENGAGEMENT + ("engagements",))


def locate_header(rows):
    for i, row in enumerate(rows[:15]):
        cols = find_columns(row)
        if _usable(cols):
            return i, cols
    first = rows[0] if rows else []
    raise ValueError("no header with an impressions column and a reactions, comments or reposts column. "
                     "First row: " + ", ".join(c for c in first if c))


def read_table(text, markdown=False):
    if markdown:
        rows = []
        for line in text.splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells if c) and any(cells):
                continue
            rows.append(cells)
        return rows
    sample = text[:4096]
    for d in sorted([",", ";", "\t"], key=lambda c: -sample.count(c)):
        rows = list(csv.reader(io.StringIO(text), delimiter=d))
        try:
            locate_header(rows)
            return rows
        except ValueError:
            continue
    return list(csv.reader(io.StringIO(text)))


def to_posts(rows, cols, day_first=False):
    posts, skipped = [], {}

    def cell(row, field):
        i = cols.get(field)
        return row[i].strip() if i is not None and i < len(row) else ""

    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1

    for n, row in enumerate(rows, 1):
        if not any(c.strip() for c in row):
            continue
        text, date_s = cell(row, "text"), cell(row, "date")
        if text.lower() in ("total", "totals") or date_s.lower() in ("total", "totals"):
            skip("total row")
            continue
        imp = parse_number(cell(row, "impressions"))
        if imp is None:
            skip("no impressions number")
            continue
        if imp <= 0:
            skip("zero impressions")
            continue
        parts = {f: parse_number(cell(row, f)) or 0.0 for f in ENGAGEMENT}
        if any(f in cols for f in ENGAGEMENT):
            eng = sum(parts.values())
        else:
            eng = parse_number(cell(row, "engagements")) or 0.0
        d, t = parse_when(date_s, cell(row, "time"), day_first)
        length = parse_number(cell(row, "length"))
        posts.append({
            "row": n, "date": d, "time": t, "text": text, "impressions": imp, "engagements": eng,
            "er": eng / imp, "type": cell(row, "type").lower() or None,
            "chars": int(length) if length else (len(text) if text else None), **parts,
        })
    return posts, skipped


def fmt_n(x):
    if x is None:
        return "n/a"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}"
    return f"{x:,.1f}"


def fmt_pct(x):
    return "n/a" if x is None else f"{x * 100:.2f}%"


def first_line(text, width=80):
    line = next((ln.strip() for ln in (text or "").splitlines() if ln.strip()), "")
    line = line.replace("|", "/")
    return line if len(line) <= width else line[:width - 3].rstrip() + "..."


def groups(posts, keyfn):
    out = {}
    for p in posts:
        k = keyfn(p)
        if k is not None:
            out.setdefault(k, []).append(p)
    return out


def group_section(title, label, grouped, order, name=str):
    lines = [f"## {title}", "", f"| {label} | Posts | Median impressions | Median engagement rate |",
             "| --- | --- | --- | --- |"]
    best = None
    for k in order:
        if k not in grouped:
            continue
        g = grouped[k]
        med_er = statistics.median(p["er"] for p in g)
        med_imp = statistics.median(p["impressions"] for p in g)
        note = " (few posts)" if len(g) < MIN_GROUP else ""
        lines.append(f"| {name(k)}{note} | {len(g)} | {fmt_n(med_imp)} | {fmt_pct(med_er)} |")
        if len(g) >= MIN_GROUP and (best is None or med_er > best[1]):
            best = (k, med_er, len(g))
    lines.append("")
    if best:
        lines.append(f"Best by median engagement rate: {name(best[0])} ({fmt_pct(best[1])}, n = {best[2]}).")
    else:
        lines.append(f"No group has {MIN_GROUP} or more posts, so there is no best here yet.")
    lines.append("")
    return lines, best


def post_table(posts):
    lines = ["| Row | Date | Day | Time | Impressions | Engagement rate | First line |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for p in posts:
        d = p["date"].isoformat() if p["date"] else "n/a"
        day = DAYS[p["date"].weekday()] if p["date"] else "n/a"
        t = f"{p['time'][0]:02d}:{p['time'][1]:02d}" if p["time"] else "n/a"
        lines.append(f"| {p['row']} | {d} | {day} | {t} | {fmt_n(p['impressions'])} | {fmt_pct(p['er'])} | "
                     f"{first_line(p['text'])} |")
    return lines + [""]


LENGTH_BANDS = [("under 500", 0, 500), ("500 to 899", 500, 900), ("900 to 1,300", 900, 1301),
                ("over 1,300", 1301, 10 ** 9)]


def length_band(chars):
    if chars is None:
        return None
    for name, lo, hi in LENGTH_BANDS:
        if lo <= chars < hi:
            return name
    return None


def week_band(posts):
    per_week = {}
    for p in posts:
        if p["date"]:
            wk = p["date"].isocalendar()[:2]
            per_week[wk] = per_week.get(wk, 0) + 1
    def band(p):
        if not p["date"]:
            return None
        c = per_week[p["date"].isocalendar()[:2]]
        return "4+" if c >= 4 else str(c)
    return band, per_week


def audit(text, markdown=False, day_first=False, rank_by="er", source="input"):
    rows = read_table(text, markdown)
    if not rows:
        raise ValueError("the file has no rows")
    h, cols = locate_header(rows)
    header = rows[h]
    data = rows[h + 1:]
    if markdown:
        data = [r for r in data if len(r) == len(header)]
    posts, skipped = to_posts(data, cols, day_first)
    if not posts:
        raise ValueError("no posts with an impressions number above 0")
    n = len(posts)
    used = ", ".join(f'{f} = "{header[i]}"' for f, i in sorted(cols.items(), key=lambda kv: kv[1]))
    if any(f in cols for f in ENGAGEMENT):
        missing = [f for f in ENGAGEMENT if f not in cols]
        formula = "(reactions + comments + reposts) / impressions"
        if missing:
            formula += ". Not in the file, counted as 0: " + ", ".join(missing)
    else:
        formula = "engagements / impressions (no reactions, comments or reposts columns; check what your " \
                  "export counts as an engagement)"
    out = ["# Post audit", "",
           f"Source: `{source}`. Data rows: {sum(1 for r in data if any(c.strip() for c in r))}. "
           f"Posts used: {n}." + (" Skipped: " + ", ".join(f"{v} {k}" for k, v in skipped.items()) + "."
                                   if skipped else ""),
           f"Columns used: {used}.",
           f"Engagement rate = {formula}.",
           "Dates and times are read as written in the file, with no time-zone change.", ""]
    if n < SMALL_SAMPLE:
        out += [f"> Small sample: {n} posts (under {SMALL_SAMPLE}). Read every number below as a hint, not a rule.",
                ""]
    dated = [p for p in posts if p["date"]]
    total_imp = sum(p["impressions"] for p in posts)
    total_eng = sum(p["engagements"] for p in posts)
    out += ["## Summary", "",
            f"- Posts: {n}" + (f" ({len(dated)} with a date)" if len(dated) != n else ""),
            (f"- Dates: {min(p['date'] for p in dated).isoformat()} to {max(p['date'] for p in dated).isoformat()}"
             if dated else "- Dates: none read"),
            f"- Median impressions: {fmt_n(statistics.median(p['impressions'] for p in posts))}",
            f"- Median engagement rate: {fmt_pct(statistics.median(p['er'] for p in posts))}",
            f"- All posts together: {fmt_n(total_eng)} engagements on {fmt_n(total_imp)} impressions "
            f"({fmt_pct(total_eng / total_imp)})", ""]

    key = (lambda p: (p["er"], p["impressions"])) if rank_by == "er" else (lambda p: (p["impressions"], p["er"]))
    ranked = sorted(posts, key=key, reverse=True)
    k = max(1, round(n * 0.2))
    what = "engagement rate" if rank_by == "er" else "impressions"
    out += [f"## Top 20% by {what} ({k} of {n})", ""] + post_table(ranked[:k])
    if n > 1:
        out += [f"## Bottom 20% by {what} ({k} of {n})", ""] + post_table(list(reversed(ranked))[:k])

    out += [f"Groups with fewer than {MIN_GROUP} posts are marked (few posts) and are never called best.", ""]
    if dated:
        lines, _ = group_section("By weekday", "Day", groups(dated, lambda p: p["date"].weekday()), range(7),
                                 lambda d: DAYS[d])
        out += lines
    else:
        out += ["## By weekday", "", "Not available: no dates could be read.", ""]
    timed = [p for p in posts if p["time"]]
    if timed:
        lines, _ = group_section("By hour posted", "Hour", groups(timed, lambda p: p["time"][0]), range(24),
                                 lambda hr: f"{hr:02d}:00 to {hr:02d}:59")
        out += lines
    else:
        out += ["## By hour posted", "", "Not available: the file has no times.", ""]
    if dated:
        band, per_week = week_band(dated)
        lines, _ = group_section("By posts in the same week", "Posts that week", groups(dated, band),
                                 ["1", "2", "3", "4+"], lambda k: f"{k} posts in a week")
        out += lines[:2] + [f"Weeks with at least one post: {len(per_week)}.", ""] + lines[2:]

    with_text = [p for p in posts if p["text"]]
    lengths = [len(p["text"]) for p in with_text]
    full_text = bool(lengths) and statistics.median(lengths) >= 200
    has_len_col = "length" in cols
    if full_text or has_len_col:
        names = [b[0] for b in LENGTH_BANDS]
        lines, _ = group_section("By length (characters)", "Length", groups(posts, lambda p: length_band(p["chars"])),
                                 names)
        out += lines
    else:
        out += ["## By length (characters)", "",
                "Not available: the text column looks like first lines only (median under 200 characters).", ""]
    if full_text:
        q = groups(with_text, lambda p: "Ends with a question" if ends_with_question(p["text"]) else "No question")
        lines, _ = group_section("Question at the end", "Ending", q, ["Ends with a question", "No question"])
        out += lines
        if all(len(q.get(g, [])) >= MIN_GROUP for g in ("Ends with a question", "No question")):
            diff = statistics.median(p["er"] for p in q["Ends with a question"]) - \
                statistics.median(p["er"] for p in q["No question"])
            out += [f"Difference in median engagement rate (question minus no question): {diff * 100:+.2f} points.",
                    ""]
        else:
            out += [f"Not enough posts on one side to compare (need {MIN_GROUP} each).", ""]
    else:
        out += ["## Question at the end", "",
                "Not available: needs the full post text, and the text column looks like first lines only.", ""]
    typed = [p for p in posts if p["type"]]
    if typed:
        g = groups(typed, lambda p: p["type"])
        lines, _ = group_section("By post type", "Type", g, sorted(g))
        out += lines
    return "\n".join(out).rstrip() + "\n"


def read_file(path):
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="CSV export or a markdown file with a table (log.md)")
    ap.add_argument("--day-first", action="store_true", help="read 05/10/2026 as 5 October")
    ap.add_argument("--rank-by", choices=["er", "impressions"], default="er")
    a = ap.parse_args(argv)
    text = read_file(a.file)
    markdown = a.file.lower().endswith((".md", ".markdown"))
    try:
        report = audit(text, markdown=markdown, day_first=a.day_first, rank_by=a.rank_by, source=a.file)
    except ValueError as e:
        print(f"Cannot audit {a.file}: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
