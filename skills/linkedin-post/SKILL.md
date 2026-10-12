---
name: linkedin-post
description: Turns one raw idea (a sentence or two) into a finished LinkedIn text post in your voice. It asks one batched question if the idea has no specific true thing in it, offers 3 opening lines with different angles and picks one, drafts the post, lints it and prints it ready to copy with a short receipt. Text only; scheduling is the linkedin-ghostwriter's job. Use when the user says "turn this idea into a LinkedIn post", "write a LinkedIn post about", "draft a post from this", "I have an idea for a post", "make this a LinkedIn post", or "/linkedin-post".
---

# linkedin-post

One raw idea in, one finished text post out, ready to copy.

## What the user gives
- The idea, in a sentence or two. Example: "the client who paid twice because our invoice was confusing".
- Optional: the day it should go out, and any project files that hold the facts.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, say so, point to the linkedin-ghostwriter setup (fill the voice file from your 5 best posts) and stop.
2. **Find the true thing.** A post needs one specific true thing: what happened, to whom, and what it cost or returned. Look for it in the idea, in the "My facts" section of `voice.md`, and in any files the user named. If any of the three is missing, ask one batched message with numbered questions (3 at most) and wait. Never fill a gap with a guess.
3. **Folder.** Create `linkedin-posts/<post-date>_<slug>/` (today's date if no post date). Write `idea.md`: the idea in the user's own words, their answers, and each fact with its source (file name, `voice.md`, or "user, in chat").
4. **Three openings.** Write 3 first lines, each under 140 characters, each a different angle, not a rewording. Pick from: the scene (what happened), the cost or result (a number the user gave), the mistake, the plain lesson, a question only this story can ask. Label each with its angle. Then name the one to ship and why, in one sentence.
5. **Draft.** Write `post.txt` on the chosen opening, in the voice from `voice.md`:
   - Short paragraphs, 1 to 3 lines, a blank line between each.
   - One idea. If the idea holds two, say so and offer a second post.
   - Close with one open door ("send me a message") or one question tied to this story.
   - 900 to 1,300 characters, up to 3 hashtags, no links in the body.
6. **Lint.** Run `python3 ~/.claude/skills/linkedin-ghostwriter/tools/check_post.py post.txt` (add `--post-date` and `--event-date` when the post names a day). Fix every FAIL. Read each WARN and decide; keep the user's voice over the linter.
7. **Print.** Show the 3 openings with labels, then the post in one fenced code block, exactly as it should be pasted. Under it, a receipt of three lines:
   - Opening: the angle used, and the one-sentence reason.
   - Length: characters, and hashtag count.
   - Lint: fails and warns, with each kept WARN and why.
8. **Next step.** Tell the user: copy it and post by hand, or say "put this in Buffer" to hand `post.txt` to linkedin-ghostwriter for a draft and a schedule on their yes. If they want another opening, redraft on it and lint again.
9. **Log, only when told.** When the user says they posted it, append one line to `linkedin-posts/log.md`: date, slug, "posted by hand" (or the Buffer post id), time, opening angle. Do not log a draft.

## Rules
- Write in the user's voice. Their words beat the linter and beat this file.
- Every number, name, client and quote has a source in `idea.md`. No source, no fact.
- One idea per sentence. Plain words.
- No em dashes, no exclamation marks, no hype words (game-changer, unlock, leverage, journey, excited to announce), no "it's not X, it's Y".
- The first line says something specific. It is never a teaser with nothing in it.
- Time words match the post date: "tonight" only when the event is the same day.

## Never
- Invent a number, a client, a quote or a result.
- Ask more than one round of questions before the first draft.
- Post, schedule, send, like, comment, connect, scrape or open linkedin.com for the user. LinkedIn's User Agreement bans bots. The user copies and posts by hand, or schedules through Buffer (an official LinkedIn partner) with their explicit yes, through linkedin-ghostwriter.
- Write to `log.md` before the user says the post is live.
