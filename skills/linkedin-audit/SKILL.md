---
name: linkedin-audit
description: Reviews the user's own past LinkedIn posts and says what works, with the numbers behind every finding. Reads a post analytics CSV (LinkedIn's export saved as CSV, or Buffer metrics) or linkedin-posts/log.md, runs tools/audit_posts.py for engagement rate, median impressions, top and bottom 20%, best weekday and hour, length bands and questions at the end, then writes 3 to 5 plain findings and what to do next week. Flags small samples and never invents a number. Use when the user says "audit my LinkedIn", "what works on my LinkedIn", "review my posts", "which posts did best", "analyse my LinkedIn analytics", or "/linkedin-audit".
---

# linkedin-audit

Reads your own post numbers and tells you, in plain words, what works and what to do next week.

## What the user gives
- A CSV of their own posts: LinkedIn's post analytics export saved as CSV, a Buffer metrics export, or their own sheet. If they have an .xlsx file, ask them to save it as CSV first.
- Or nothing: then use `linkedin-posts/log.md` from the linkedin-ghostwriter skill.
- Optional: the time zone of the export, and anything unusual in the period (a holiday, a paid boost, a viral reshare).

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, run steps 2 and 3 only, show the top 5 posts by engagement rate as the input for the linkedin-ghostwriter setup (5 best posts), and stop.
2. **Folder.** Make `linkedin-posts/audit-<YYYY-MM-DD>/` (today's date). Copy the input file in as `data.csv` or `data.md`. Never edit the copy.
3. **Run the tool.** `python3 <this skill>/tools/audit_posts.py <data file> > linkedin-posts/audit-<date>/report.md`.
   - Check the "Columns used" line. If a column was matched wrongly, rename that header in a second copy, `data-fixed.csv`, and say which header you changed.
   - Slash dates are read month first. If the export is day first (05/10 meaning 5 October), add `--day-first`. If you cannot tell, ask.
   - Exit code 2 means no impressions column or no posts. Show the error and ask for a better export.
   - Add `--rank-by impressions` only if the user's goal is reach, not response.
4. **Read the posts.** Open `report.md`. Read the full text of every post in the top and bottom tables: from the text column (match on the Row number), or from `linkedin-posts/<date>_<slug>/post.txt` when the data came from `log.md`.
5. **Write** `linkedin-posts/audit-<date>/findings.md`:
   - First line: the number of posts, the date range, and "small sample" if n is under 20.
   - 3 to 5 findings. Each one is a single plain sentence, then the numbers behind it copied from `report.md` (medians, n per group), then the posts it rests on (date and first line).
   - Patterns you see in the post text (how the top posts open, topic, format) count only when you name the posts: "3 of the 4 top posts open on a scene: 15 Sep, 8 Sep, 1 Sep."
   - A short "What this does not show" list: groups under 3 posts, missing columns, sections the tool marked "Not available".
6. **Next week.** Under the findings, 3 actions, each tied to one finding: which days and hours to post, which length or format to try, one post to write (an idea, not a draft). Offer `linkedin-plan` to turn them into a calendar and `linkedin-ghostwriter` to write the post.
7. **Show.** Paste the findings and the actions in the chat, with the paths to `report.md` and `findings.md`. Stop there.

## Rules
- Every number in `findings.md` comes from `report.md` or from the data file, exactly as written. Do the sum yourself only for a count you can show, such as "3 of 4 posts".
- Under 20 posts, say "small sample" at the top and use "so far" and "in these posts", not "always".
- A group under 3 posts is never a finding. Say it needs more posts.
- These are links, not causes. Write "posts on Tuesday did better here", not "Tuesday makes posts do better".
- Compare the user only with themselves. No industry averages, no "best time to post" claims from outside their data.
- Findings use plain words, one idea per sentence, no em dashes, no exclamation marks, no hype words.
- If the export has a paid boost or one viral post, say so and show the medians with that post left in. Medians already resist one outlier.

## Never
- Invent a number, fill a gap in the data, or guess a missing time zone.
- Open, log in to or scrape linkedin.com, or fetch numbers from anywhere except the files the user gives. LinkedIn's User Agreement bans bots and scraping.
- Post, send, like, comment or connect on the user's behalf. This skill writes files only.
- Change `log.md` or the user's export.
