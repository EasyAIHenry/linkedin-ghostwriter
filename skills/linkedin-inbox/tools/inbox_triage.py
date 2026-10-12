#!/usr/bin/env python3
"""Pre-sort a LinkedIn messages CSV into piles. Standard library only.

Usage: python3 inbox_triage.py messages.csv --name "First Last" [--name First] [--today YYYY-MM-DD] [--json]

The CSV needs a sender, a date and the message text. Headers are matched without case:
  sender: from, sender        date: date, sent, sent at        text: text, content, message, body
That covers LinkedIn's own messages export (FROM, DATE, CONTENT) and a hand-made from,date,text file.
Rows sent by the user (the sender matches a --name exactly) are skipped and counted.

Piles: today, week, archive, spam (spam or a pitch), unsure. Rules, first match wins:
  1. empty text                                   -> archive
  2. only a link (4 words or fewer once links go) -> spam
  3. 2+ pitch phrases, or 1 pitch phrase + money  -> spam
  4. 1 pitch phrase                               -> unsure
  5. no readable date                             -> unsure
  6. a question, 3 days old or less               -> today
     a question that uses the user's name, 14 days or less -> today
     a question, 30 days or less                  -> week
     a question, older                            -> unsure
  7. a short thank-you, no question               -> archive
     uses the user's name, 14 days or less        -> week
     money words, no question                     -> unsure
     older than 30 days                           -> archive
     anything else                                -> unsure
Claude judges every "unsure" row, and checks the rest. The tool reads the file only. It sends nothing.
"""
import argparse
import csv
import datetime as dt
import json
import re
import sys

SENDER = ("from", "sender", "sender name")
DATE = ("date", "sent", "sent at", "timestamp")
TEXT = ("text", "content", "message", "body")

URL = re.compile(r"(https?://|www\.)\S+", re.I)
MONEY = re.compile(
    r"[$£€]\s?\d|\b\d+(?:\.\d+)?\s?(?:k|usd|sgd|eur|gbp)\b|\b(?:budget|invoice|quote|quotation|rate|rates|"
    r"fee|fees|pricing|price|paid|payment|retainer|cost|costs|revenue|roi)\b", re.I)
PITCH = [
    "quick call", "quick chat", "15 minutes", "15-minute", "15 mins", "book a call", "book a demo", "schedule a call",
    "hop on a call", "our services", "our agency", "our team can", "we help", "we specialise", "we specialize",
    "i help businesses", "i help companies", "generate leads", "more leads", "lead generation", "booked appointments",
    "outsourc*", "white label", "white-label", "guaranteed", "seo", "web development", "app development",
    "virtual assistant", "investment opportunity", "crypto", "forex", "partnership opportunity",
    "increase your revenue", "scale your business", "free audit", "free trial", "limited time",
    "let me know if you're interested", "would you be open to",
]
THANKS = re.compile(r"\b(thanks|thank you|thx|cheers|appreciate it)\b", re.I)
FORMATS = ("%Y-%m-%d %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M",
           "%m/%d/%Y %H:%M", "%d %b %Y", "%b %d, %Y")


def parse_date(value):
    v = (value or "").strip()
    for f in FORMATS:
        try:
            return dt.datetime.strptime(v, f).date()
        except ValueError:
            pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})", v)
    if m:
        try:
            return dt.date.fromisoformat(m.group(1))
        except ValueError:
            return None
    return None


def _column(headers, names):
    for h in headers:
        if h and h.strip().lower() in names:
            return h
    return None


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        cols = [_column(headers, n) for n in (SENDER, DATE, TEXT)]
        if None in cols:
            raise ValueError("the CSV needs from, date and text columns; found: " + ", ".join(headers))
        return [{"from": (r.get(cols[0]) or "").strip(), "date": (r.get(cols[1]) or "").strip(),
                 "text": (r.get(cols[2]) or "").strip()} for r in reader]


def _pitch_hits(low):
    hits = []
    for p in PITCH:
        tail = "" if p.endswith("*") else r"(?!\w)"
        if re.search(r"(?<!\w)" + re.escape(p.rstrip("*")) + tail, low):
            hits.append(p.rstrip("*"))
    return hits


def triage(row, names, today):
    """Return (pile, reason) for one message."""
    text = row["text"]
    low = text.lower()
    if not text:
        return "archive", "empty message"
    rest = URL.sub(" ", text)
    if URL.search(text) and len(re.findall(r"\w+", rest)) <= 4:
        return "spam", "only a link"
    pitch = _pitch_hits(low)
    money = bool(MONEY.search(text))
    if len(pitch) >= 2 or (pitch and money):
        return "spam", "pitch: " + ", ".join(pitch[:3]) + (" + money words" if money else "")
    if pitch:
        return "unsure", f"one pitch phrase ({pitch[0]}); could be real"
    sent = parse_date(row["date"])
    if sent is None:
        return "unsure", "no readable date"
    age = (today - sent).days
    named = any(re.search(r"(?<!\w)" + re.escape(n.lower()) + r"(?!\w)", low) for n in names)
    if "?" in text:
        if age <= 3:
            return "today", f"a question, {age} day(s) old"
        if named and age <= 14:
            return "today", f"a question that uses your name, {age} days old"
        if age <= 30:
            return "week", f"a question, {age} days old"
        return "unsure", f"an old question, {age} days; still worth a reply?"
    if THANKS.search(text) and len(re.findall(r"\w+", text)) <= 8:
        return "archive", "a thank-you, nothing to answer"
    if named and age <= 14:
        return "week", f"uses your name, no question, {age} days old"
    if money:
        return "unsure", "money words but no question"
    if age > 30:
        return "archive", f"no question, {age} days old"
    return "unsure", "no clear signal"


def run(rows, names, today):
    mine = {n.strip().lower() for n in names}
    out, skipped = [], 0
    for i, row in enumerate(rows, 1):
        if row["from"].lower() in mine:
            skipped += 1
            continue
        pile, reason = triage(row, names, today)
        sent = parse_date(row["date"])
        out.append({"row": i, "from": row["from"], "date": sent.isoformat() if sent else row["date"],
                    "pile": pile, "reason": reason, "text": row["text"]})
    return out, skipped


def _cell(s, n=None):
    s = " ".join(s.split()).replace("|", "\\|")
    return s if n is None or len(s) <= n else s[:n - 3] + "..."


def table(results):
    lines = ["| # | From | Date | Pile | Reason | Message |", "| --- | --- | --- | --- | --- | --- |"]
    order = {"today": 0, "week": 1, "unsure": 2, "archive": 3, "spam": 4}
    for r in sorted(results, key=lambda r: (order[r["pile"]], r["row"])):
        lines.append(f"| {r['row']} | {_cell(r['from'])} | {r['date']} | {r['pile']} | {_cell(r['reason'])} | "
                     f"{_cell(r['text'], 80)} |")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--name", action="append", default=[], help="your name as it appears; repeat for variants")
    ap.add_argument("--today", help="YYYY-MM-DD, default is the real date")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    try:
        rows = read_rows(a.file)
    except ValueError as e:
        print("ERROR", e)
        return 2
    results, skipped = run(rows, a.name, today)
    if a.json:
        print(json.dumps({"results": results, "skipped_own": skipped}, indent=2))
        return 0
    print(table(results))
    counts = {p: sum(1 for r in results if r["pile"] == p) for p in ("today", "week", "unsure", "archive", "spam")}
    print("\n" + ", ".join(f"{p} {n}" for p, n in counts.items()) + f"; skipped {skipped} sent by you")
    return 0


if __name__ == "__main__":
    sys.exit(main())
