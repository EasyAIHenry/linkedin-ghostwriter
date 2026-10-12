---
name: linkedin-plan
description: Builds a weekly or monthly LinkedIn content plan from the user's goal, what they have coming up and their own past results. Writes linkedin-posts/plan-<start-date>.md, a calendar table with the date, day, time, post idea, the one true fact each idea rests on, the format and the skill to use next. Three posts a week by default, times taken from the user's own best slots, never generic best-time claims. It plans only and never schedules. Use when the user says "plan my LinkedIn", "content calendar", "what should I post this week", "LinkedIn plan for <month>", "post plan for my launch", or "/linkedin-plan".
---

# linkedin-plan

Turns your goal, your diary and your own numbers into a short calendar of posts worth writing.

## What the user gives
- The goal for the period, in one line: clients, hiring, a launch, sign-ups for an event.
- The period: a week or a month, and the start date.
- What is coming up: events, launches, projects, talks, with dates. Files or notes are fine.
- Their past results: `linkedin-posts/log.md`, or a pasted or saved analytics export (CSV).
- Optional: how many posts they can really write, and days or times they cannot post.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, point the user to the linkedin-ghostwriter setup (paste their 5 best posts) and stop.
2. **Numbers.** Run the linkedin-audit tool on their results: `python3 <linkedin-audit skill>/tools/audit_posts.py <log.md or export.csv>`. If the export was pasted, save it first as `linkedin-posts/plan-<start-date>-data.csv`, exactly as pasted. Note the best weekday, the best hour and the "posts in a week" table, each with its n. If there are no results yet, say so.
3. **Cadence.** Default to 3 posts a week. Change it only when the "posts in a week" table shows a different count doing better with n of 3 or more in each group, or when the user says they can write fewer. Never plan more than they say they can write.
4. **Slots.** Take days and hours from their best groups with n of 3 or more. Leave at least one day between posts. If they have fewer than 3 posts in every group, use the times the user says suit them and mark each "your choice, no data yet".
5. **Facts.** List every specific true thing the plan can rest on: an event and its date, a result with its number, a project milestone, a lesson from a real job. Give each a source (file path, `log.md` line, or "you said in chat"). Search their project folders the same way linkedin-ghostwriter does.
6. **Ideas.** One idea per slot, each built on one fact from step 5 and pointed at the goal. Pick the format from what exists: photo only if they have the photo, video only if they have the clip, carousel when the fact is a list or steps, text otherwise. Mix formats; no format three times in a row.
7. **Write** `linkedin-posts/plan-<start-date>.md`:
   - Header: goal, period, cadence and why (with the numbers from step 2), and the time zone.
   - The calendar table, columns in this order: Date | Day | Time | Post idea | The true thing it rests on (source) | Format | Next skill.
   - Post idea: one plain line in the user's voice, under 15 words.
   - Next skill: `linkedin-ghostwriter` for each post, `linkedin-carousel` for carousel slots (then linkedin-ghostwriter to draft it in Buffer), or `linkedin-repurpose` when the post comes from long content they already made.
   - "Questions for you": every fact you need and could not find.
   - "Left out": ideas you dropped because they had no source, in one line each.
   - Last line: "Run linkedin-audit at the end of the period to check the plan against your numbers."
8. **Show.** Paste the table in the chat with the path to the file. Stop there.

## Rules
- Fewer, better posts. A slot with no true fact stays empty and goes under "Questions for you".
- Every post time comes from the user's own data or the user's own choice. Never "the best time to post on LinkedIn is".
- Event posts go before the event, with the right time words: a post the day before says "tomorrow".
- One idea per post. Two ideas on one fact make two slots, or one gets dropped.
- Ideas follow the writing rules: no em dashes, no exclamation marks, no hype words, no "it's not X, it's Y", plain words.
- A month plan is 4 or 5 weekly blocks in one table, with a blank row between weeks.

## Never
- Schedule, draft in Buffer or publish anything. The plan is a file. Each post goes through linkedin-ghostwriter, which asks for a yes per post.
- Invent a fact, a number, a client or a result to fill a slot.
- Post, send, like, comment, connect, scrape or open linkedin.com for the user. LinkedIn's User Agreement bans bots.
- Quote a generic posting-time or posting-frequency study as advice.
