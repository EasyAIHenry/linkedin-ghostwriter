#!/usr/bin/env python3
"""Lint a LinkedIn post before it goes to Buffer. Standard library only.

Usage: python3 check_post.py post.txt [--post-date YYYY-MM-DD] [--event-date YYYY-MM-DD]

FAIL (exit code 1): links in the body, more than 3 hashtags, em or en dashes used as punctuation, an empty post.
WARN: length outside 900-1,300 characters, a first line over 140 characters (cut off on mobile), long paragraphs,
exclamation marks, hype words, the "it's not X, it's Y" pattern, and time words that don't match the dates you pass.
"""
import argparse
import datetime as dt
import re
import sys

HYPE = ["game-changer", "game changer", "revolutionary", "unlock", "leverage", "delve", "supercharge", "skyrocket",
        "mind-blowing", "mind blowing", "insane", "next level", "next-level", "excited to announce", "thrilled to",
        "journey", "10x", "secret sauce", "crushing it", "disrupt"]
NOT_X_ITS_Y = re.compile(r"\b(it'?s|this is|that'?s)\s+not\s+(just\s+)?[^.?!\n]{1,60}[,.;]\s*(it'?s|this is|that'?s)\b", re.I)
URL = re.compile(r"(https?://|www\.)\S+", re.I)
DASH = re.compile(r"\s[—–]\s|\w—\w")


def check(text, post_date=None, event_date=None):
    fails, warns = [], []
    body = text.strip()
    if not body:
        return ["empty post"], []
    n = len(body)
    if n < 900 or n > 1300:
        warns.append(f"length {n} characters (aim for 900 to 1,300)")
    first = body.splitlines()[0]
    if len(first) > 140:
        warns.append(f"first line is {len(first)} characters; mobile cuts it at about 140")
    if URL.search(body):
        fails.append("link in the body; put it in the first comment instead")
    tags = re.findall(r"(?<!\w)#\w+", body)
    if len(tags) > 3:
        fails.append(f"{len(tags)} hashtags (3 at most)")
    if DASH.search(body):
        fails.append("em or en dash used as punctuation; use a full stop or a comma")
    if "!" in body:
        warns.append(f"{body.count('!')} exclamation mark(s)")
    low = body.lower()
    hits = [w for w in HYPE if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", low)]
    if hits:
        warns.append("hype words: " + ", ".join(hits))
    if NOT_X_ITS_Y.search(body):
        warns.append('"it\'s not X, it\'s Y" pattern')
    for p in [p for p in re.split(r"\n\s*\n", body) if p.strip()]:
        if len(p) > 320:
            warns.append(f"long paragraph ({len(p)} characters): \"{p[:50]}...\"")
    if post_date and event_date:
        gap = (event_date - post_date).days
        said = {w for w in ("tonight", "today", "tomorrow", "this weekend", "next week") if re.search(r"\b" + w + r"\b", low)}
        if "tonight" in said or "today" in said:
            if gap != 0:
                warns.append(f"says today/tonight but the event is {gap} day(s) after the post date")
        if "tomorrow" in said and gap != 1:
            warns.append(f"says tomorrow but the event is {gap} day(s) after the post date")
    return fails, warns


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--post-date")
    ap.add_argument("--event-date")
    a = ap.parse_args(argv)
    d = lambda s: dt.date.fromisoformat(s) if s else None
    text = open(a.file, encoding="utf-8").read()
    fails, warns = check(text, d(a.post_date), d(a.event_date))
    for f in fails:
        print("FAIL", f)
    for w in warns:
        print("WARN", w)
    print(f"{len(text.strip())} characters, {len(fails)} fail, {len(warns)} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
