#!/usr/bin/env python3
"""Score how human a draft reads, from tells you can count. Standard library only.

Usage: python3 humanise_check.py draft.txt [--json] [--fail-under N]
       python3 humanise_check.py - < draft.txt

The score runs from 0 to 100. Higher reads more human.
It starts at 100 and takes points off for each tell it finds. Each tell has a cap,
so one habit cannot sink the whole score on its own.

    tell                                         points per hit    cap
    stock AI phrase (STOCK below, 50+ of them)   6                 36
    em dash, spaced en dash or " -- "            4                 16
    "it's not X, it's Y" or "not only X but Y"   8                 24
    rule-of-three adjective list                 5                 15
    corporate word (CORPORATE below)             3                 15
    questions over the allowance                 3 each            12
    emoji bullet at the start of a line          3                 12
    same-length sentences (5 or more sentences)  10 or 5           10

    score = max(0, 100 - sum of the capped penalties)

Same-length sentences: the spread is the coefficient of variation of words per
sentence (population standard deviation divided by the mean). A spread under 0.25
costs 10 points and 0.25 to 0.35 costs 5. People mix short and long sentences.
Machine drafts tend to sit in a narrow band.
Questions: the allowance is 2, or one in five sentences if that is more.
A rule-of-three list is "A, B and C" where all three words look like adjectives
(from ADJECTIVES or an adjective ending such as -ive, -ful, -able, -ous).
Overlaps count once: "plays a pivotal role" is one stock phrase, and a corporate
word inside a stock phrase is not counted again.

Bands: 85 and up reads human. 70 to 84 has a few tells. Under 70, rewrite the flagged lines.
Exit code 1 only when --fail-under is given and the score is below it.
"""
import argparse
import bisect
import json
import re
import statistics
import sys

STOCK = [
    r"in today's fast[- ]paced (?:world|environment|landscape)",
    r"in today's digital (?:age|world|landscape)",
    r"in today's (?:rapidly )?(?:changing|evolving) (?:world|landscape)",
    r"ever[- ](?:evolving|changing) landscape",
    r"navigat(?:e|es|ing) the complexities",
    r"navigat(?:e|es|ing) the (?:landscape|world) of",
    r"delv(?:e|es|ed|ing)",
    r"deep dive",
    r"let's dive in",
    r"it's worth noting",
    r"it is worth noting",
    r"it's important to note",
    r"it is important to note",
    r"game[- ]changer",
    r"unlock(?:s|ed|ing)? the (?:power|potential|secrets?)",
    r"unleash(?:es|ed|ing)?",
    r"harness(?:es|ed|ing)? the power",
    r"at the end of the day",
    r"a testament to",
    r"plays? a (?:crucial|pivotal|vital|key) role",
    r"pivotal",
    r"paradigm shift",
    r"buckle up",
    r"here's the thing",
    r"secret sauce",
    r"tapestry",
    r"in conclusion",
    r"moreover",
    r"furthermore",
    r"needless to say",
    r"it goes without saying",
    r"rest assured",
    r"look no further",
    r"take (?:it|your \w+) to the next level",
    r"cutting[- ]edge",
    r"state[- ]of[- ]the[- ]art",
    r"revolutioni[sz](?:e|es|ed|ing)",
    r"embark(?:s|ed|ing)? on (?:a|this|my|our|your) journey",
    r"stand out from the crowd",
    r"thought leader(?:ship)?",
    r"move the needle",
    r"low[- ]hanging fruit",
    r"(?:i'm|we're|i am|we are) (?:so )?(?:thrilled|excited|humbled|delighted) to (?:announce|share)",
    r"without further ado",
    r"in (?:the|this) (?:realm|world) of",
    r"food for thought",
    r"key takeaways?",
    r"that being said",
    r"in a world where",
    r"the ultimate guide",
    r"let (?:that|this) sink in",
    r"here's why (?:it|this) matters",
    r"i hope this (?:email|message) finds you well",
    r"(?:a|the) double[- ]edged sword",
    r"the future of \w+ is here",
]

CORPORATE = [
    r"seamless(?:ly)?", r"robust", r"elevat(?:e|es|ed|ing)", r"leverag(?:e|es|ed|ing)",
    r"streamlin(?:e|es|ed|ing)", r"empower(?:s|ed|ing|ment)?", r"holistic", r"transformative",
    r"innovative", r"comprehensive", r"meticulous(?:ly)?", r"crucial", r"foster(?:s|ed|ing)?",
    r"bolster(?:s|ed|ing)?", r"utili[sz](?:e|es|ed|ing|ation)", r"facilitat(?:e|es|ed|ing)",
    r"optimi[sz](?:e|es|ed|ing)", r"myriad", r"plethora", r"synerg(?:y|ies|istic)", r"dynamic",
    r"vibrant", r"actionable insights?", r"best[- ]in[- ]class", r"world[- ]class",
]

ADJECTIVES = set("""
fast faster quick quicker simple simpler easy easier clear clean lean smart smarter bold strong stronger
safe secure cheap cheaper better bigger new fresh modern agile nimble flexible scalable reliable robust
seamless efficient effective intuitive innovative dynamic engaging impactful authentic powerful meaningful
actionable practical concise transparent consistent personal human honest thoughtful bright sharp rich deep
warm real unique creative strategic calm kind open focused proven trusted elegant sleek polished
""".split())
ADJ_ENDINGS = ("ive", "ful", "able", "ible", "ous", "less", "ic", "al", "ish")

CAPS = {"stock phrase": (6, 36), "dash": (4, 16), "contrast pattern": (8, 24), "rule of three": (5, 15),
        "corporate word": (3, 15), "questions": (3, 12), "emoji bullet": (3, 12)}

STOCK_RX = [re.compile(r"(?<![\w'])" + p + r"(?![\w])", re.I) for p in STOCK]
CORP_RX = [re.compile(r"(?<![\w'])" + p + r"(?![\w])", re.I) for p in CORPORATE]
DASH_RX = re.compile(r"—|\s–\s|\s--\s")
NOT_X_Y = re.compile(
    r"\b(?:it's|it is|this is|that's|that is|they're|we're|you're)\s+not\s+[^.?!\n]{1,60}?[,;:.]\s*"
    r"(?:it's|it is|this is|that's|that is|they're|we're|you're)\b", re.I)
ISNT_X_Y = re.compile(
    r"\b(?:it|this|that)\s+(?:isn't|wasn't)\s+[^.?!\n]{1,60}?[,;:.]\s*(?:it's|it is|it was|this is|that's)\b", re.I)
NOT_ONLY = re.compile(r"\bnot\s+only\b[^.?!\n]{1,80}?\bbut\b", re.I)
THREE = re.compile(r"\b([A-Za-z][a-z'-]+),\s+([A-Za-z][a-z'-]+),?\s+(?:and|&)\s+([A-Za-z][a-z'-]+)\b")


def _normalise(text):
    return text.replace("’", "'").replace("‘", "'")


def _adjective(word):
    w = word.lower()
    return w in ADJECTIVES or (len(w) > 4 and w.endswith(ADJ_ENDINGS))


def _is_emoji(ch):
    o = ord(ch)
    return 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF


def sentences(text):
    """Return (line, sentence, word count) for every sentence. A line break also ends a sentence."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for part in re.split(r"(?<=[.?!])\s+", line.strip()):
            words = re.findall(r"[A-Za-z0-9']+", part)
            if words:
                out.append((i, part, len(words)))
    return out


def check(text):
    text = _normalise(text)
    starts = [0] + [m.end() for m in re.finditer(r"\n", text)]
    line_of = lambda pos: bisect.bisect_right(starts, pos)
    hits = []
    taken = []

    def add(tell, start, end, match):
        hits.append({"tell": tell, "line": line_of(start), "match": match.strip()})
        taken.append((start, end))

    found = []
    for rx in STOCK_RX:
        found += [(m.start(), m.end(), m.group(0)) for m in rx.finditer(text)]
    for s, e, g in sorted(found, key=lambda f: (f[0], -(f[1] - f[0]))):
        if not any(s < te and e > ts for ts, te in taken):
            add("stock phrase", s, e, g)
    for rx in CORP_RX:
        for m in rx.finditer(text):
            if not any(m.start() < te and m.end() > ts for ts, te in taken):
                add("corporate word", m.start(), m.end(), m.group(0))
    for m in DASH_RX.finditer(text):
        add("dash", m.start(), m.end(), text[max(0, m.start() - 15):m.end() + 15].replace("\n", " "))
    for rx in (NOT_X_Y, ISNT_X_Y, NOT_ONLY):
        for m in rx.finditer(text):
            add("contrast pattern", m.start(), m.end(), m.group(0))
    for m in THREE.finditer(text):
        if all(_adjective(w) for w in m.groups()):
            add("rule of three", m.start(), m.end(), m.group(0))
    for i, line in enumerate(text.splitlines(), 1):
        s = line.lstrip(" \t-*•")
        if s and _is_emoji(s[0]):
            hits.append({"tell": "emoji bullet", "line": i, "match": line.strip()[:60]})

    sents = sentences(text)
    questions = [(ln, s) for ln, s, _ in sents if s.rstrip("\"')]").endswith("?")]
    allowance = max(2, len(sents) // 5)
    excess = max(0, len(questions) - allowance)
    if excess:
        hits += [{"tell": "questions", "line": ln, "match": s[:60]} for ln, s in questions]

    penalties = {}
    for tell, (each, cap) in CAPS.items():
        n = excess if tell == "questions" else sum(1 for h in hits if h["tell"] == tell)
        if n:
            penalties[tell] = min(cap, each * n)
    spread = None
    if len(sents) >= 5:
        counts = [n for _, _, n in sents]
        spread = round(statistics.pstdev(counts) / statistics.mean(counts), 2)
        if spread < 0.35:
            penalties["same-length sentences"] = 10 if spread < 0.25 else 5
            hits.append({"tell": "same-length sentences", "line": None,
                         "match": f"spread {spread} across {len(sents)} sentences (aim for 0.35 or more)"})
    hits.sort(key=lambda h: (h["line"] or 0, h["tell"]))
    score = max(0, 100 - sum(penalties.values()))
    return {"score": score, "penalties": penalties, "hits": hits,
            "sentences": len(sents), "questions": len(questions), "spread": spread}


def band(score):
    if score >= 85:
        return "reads human"
    if score >= 70:
        return "a few tells"
    return "rewrite the flagged lines"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", help="text file, or - for standard input")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    ap.add_argument("--fail-under", type=int, help="exit 1 if the score is below this")
    a = ap.parse_args(argv)
    if a.file == "-":
        text = sys.stdin.read()
    else:
        with open(a.file, encoding="utf-8") as f:
            text = f.read()
    r = check(text)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"Score {r['score']}/100 ({band(r['score'])})")
        if r["penalties"]:
            print("Penalties: " + ", ".join(f"{k} -{v}" for k, v in r["penalties"].items()))
        for h in r["hits"]:
            where = f"line {h['line']}" if h["line"] else "whole text"
            print(f"{where:<11} {h['tell']:<22} {h['match']}")
        print(f"{r['sentences']} sentences, {r['questions']} questions, spread {r['spread']}")
    return 1 if a.fail_under is not None and r["score"] < a.fail_under else 0


if __name__ == "__main__":
    sys.exit(main())
