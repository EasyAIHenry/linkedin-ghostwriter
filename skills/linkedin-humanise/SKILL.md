---
name: linkedin-humanise
description: Checks any draft for the tells that make writing read as machine-written, scores it 0 to 100 with a counting tool, and rewrites only the flagged parts in the user's voice. Keeps the user's facts and structure and reports the score before and after. Use when the user says "humanise this", "make this sound like me", "does this sound like AI", "remove the AI tells", "de-AI my post", "check this draft", or "/linkedin-humanise".
---

# linkedin-humanise

Find the lines that sound machine-written and rewrite only those, in the user's own voice.

## What the user gives
- The draft: pasted text or a file path. A post, an About section, a message, a comment.
- Optional: what it is for (a post, a DM) and anything that must not change, such as a quote or a product name.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, stop and point the user to the linkedin-ghostwriter setup: copy `voice-profile.example.md` to that path and fill it from their 5 best posts.
2. **Folder.** Make `linkedin-posts/humanise/<YYYY-MM-DD>_<slug>/` in the working folder. Save the draft as `before.txt`, exactly as given.
3. **Score before.** Run `python3 <this skill>/tools/humanise_check.py before.txt`. It prints the score, the penalty per tell, and every hit with its line number. Tells it counts:
   - stock phrases ("in today's fast-paced world", "delve", "it's worth noting", "game-changer", "unlock the power" and 50 more)
   - em dashes, spaced en dashes and " -- "
   - "it's not X, it's Y" and "not only X but Y"
   - rule-of-three adjective lists ("fast, simple and scalable")
   - corporate words ("seamless", "robust", "elevate", "leverage")
   - sentences that all run the same length
   - more questions than the text can carry
   - emoji at the start of a line used as bullets
4. **Read it yourself too.** The tool counts. It cannot hear. Note any other line that sounds generic next to the voice file: a vague opener, a moral at the end, a list where one example would do. Mark these as "read by ear" so the user knows they came from you, not the tool.
5. **Rewrite only the flagged parts.** For each hit, change the smallest span that removes the tell:
   - Stock phrase or corporate word: say the plain thing, or cut it if the sentence stands without it.
   - Dash: a full stop or a comma.
   - "Not X, it's Y": state Y directly.
   - Rule of three: keep the one adjective that is true and specific, or swap the list for a fact.
   - Same-length sentences: split one long sentence and join two short ones. Do not add new claims to make length.
   - Questions: keep the one that matters, turn the rest into statements.
   - Emoji bullets: plain line breaks or a hyphen.
   Every other line stays word for word. Keep the order, the paragraphs and every fact.
6. **Score after.** Save the result as `after.txt` and run the tool again. If it is post-length (over about 600 characters), also run `python3 ~/.claude/skills/linkedin-ghostwriter/tools/check_post.py after.txt` and fix every FAIL.
7. **Report.** Write `report.md` with: score before and after, a table of each change (line, tell, before, after), the "read by ear" notes, and any hit you left alone with the reason. Show the user the rewritten text first, then the scores, then the table.
8. **Log.** Append one line to `linkedin-posts/log.md`: date, `humanise`, slug, score before and after.

## Rules
- The aim is the user's voice, not a high score. If a flagged word is one the voice file says they use, keep it and say so.
- Change the fewest words that fix the tell. A rewrite the user cannot recognise as theirs has failed.
- Never add a fact, number, name, client or quote while rewriting. If a sentence needs a specific to sound human, ask the user for it.
- Keep anything the user said must not change, even if the tool flags it.
- If the score is already 85 or more, say so and offer only the hits worth fixing. Do not rewrite for the sake of it.
- Writing rules for the rewrite: no em dashes, no exclamation marks, no hype words, no "it's not X, it's Y", one idea per sentence, plain words.

## Never
- Post, send, schedule, comment, like or connect for the user, or open linkedin.com. LinkedIn's User Agreement bans bots. The skill writes text and files only; the user copies and posts by hand, or schedules through Buffer with their explicit yes.
- Rewrite lines the tool did not flag and you did not mark by ear.
- Claim the text will pass an AI detector. The score counts tells. It is not a detector.
- Send the draft to any website or service.
