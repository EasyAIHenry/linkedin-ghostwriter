---
name: linkedin-inbox
description: Triages a batch of LinkedIn messages the user pastes in or exports. Sorts each into reply today, reply this week, archive, or spam-or-pitch with a one-line reason, then drafts replies for the today pile in the user's voice. A small tool pre-sorts the messages CSV by simple signals so Claude only judges the unclear ones. Output is a markdown table plus the drafts. It never sends or deletes anything. Use when the user says "triage my LinkedIn inbox", "sort my LinkedIn messages", "who should I reply to", "clear my DMs", "go through my messages export", or "/linkedin-inbox".
---

# linkedin-inbox

Sort a batch of LinkedIn messages into four piles and draft the replies that cannot wait.

## What the user gives
- The messages: pasted text, or the `messages.csv` from LinkedIn's own data export (Settings, Data privacy, Get a copy of your data). Any CSV with from, date and text columns works.
- Their name as it appears in messages, so the tool can skip their own sent messages and spot when someone uses it.
- Optional: people or topics that always matter (a client, a project), and what they never reply to.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, stop and point the user to the linkedin-ghostwriter setup: copy `voice-profile.example.md` to that path and fill it from their 5 best posts.
2. **Folder.** Make `linkedin-posts/inbox/<YYYY-MM-DD>/`. Copy the CSV in as `messages.csv`. If the user pasted text, write it into `messages.csv` yourself with the columns `from,date,text`, one row per message.
3. **Pre-sort.** Run `python3 <this skill>/tools/inbox_triage.py messages.csv --name "<full name>" --name "<first name>" --today <YYYY-MM-DD>`. It prints a table with a pile and a reason for every message. Piles: today, week, archive, spam, unsure. The signals:
   - a question mark, and how many days old the message is
   - the user's name in the text
   - money words (rate, budget, invoice, a currency amount)
   - a message that is only a link
   - pitch phrases ("quick call", "we help", "lead generation")
   Rows the user sent are skipped and counted.
4. **Judge.** Read every "unsure" row and decide its pile. Then check the rest quickly; the tool is a first pass, not the decision. Move a row when the text says otherwise, such as a client's message with no question mark. Give each a one-line reason in plain words. Apply the user's "always matters" and "never reply" lists last.
5. **Table.** Write `triage.md` with one markdown table: `| # | From | Date | Pile | Reason |`, using the piles "Reply today", "Reply this week", "Archive" and "Spam or pitch", sorted in that order. Under it, the count per pile.
6. **Drafts for today.** For each "Reply today" row, draft a reply in the user's voice:
   - Answer what they asked, in 2 to 5 short sentences.
   - One ask or one clear next step at most.
   - If the answer needs a fact the user has not given (a price, a date, availability), leave a marked gap such as `[your rate]` and list it as a question.
   - Add the drafts to `triage.md` under the table, each headed with the row number and sender.
7. **Check.** No em dashes, no exclamation marks, no hype words, no "it's not X, it's Y" in any draft. Show the user the table, then the drafts, then the open questions.
8. **Log.** Append one line to `linkedin-posts/log.md`: date, `inbox`, the count per pile.

## Rules
- A one-line reason for every message, so the user can disagree quickly.
- Only the facts in the messages and the voice file. Never invent a price, a date, a promise or a reason for a no.
- Polite no replies to pitches only if the user asks; otherwise the pile is enough. The linkedin-dm skill writes them.
- When unsure between two piles, pick the more urgent one and say so.
- Keep the messages local. They contain other people's words and details; do not quote them anywhere except `triage.md`.

## Never
- Send, reply, archive, delete, mark as read, connect or open linkedin.com for the user. LinkedIn's User Agreement bans bots. The skill writes text and files only; the user copies each reply and sends it by hand.
- Delete or change `messages.csv` or any file the user gave.
- Let the messages leave this folder: they stay on the user's machine.
- Draft replies for the archive or spam piles unless the user asks.
