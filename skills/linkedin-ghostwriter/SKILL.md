---
name: linkedin-ghostwriter
description: An automated LinkedIn ghostwriter that stops before the Post button. You drop files (a poster, photos, a video) and a few lines of direction; Claude checks every fact against your project files, writes the post in your voice, lints it, saves it as a Buffer draft and shows you the preview. It schedules only after you say yes. Use when the user says "post this on my LinkedIn", "write my LinkedIn post", "LinkedIn post for <event/project>", "put this in Buffer", "ghostwrite this", or "/linkedin-ghostwriter".
---

# linkedin-ghostwriter

You give it the files and the direction. It does everything up to the schedule button, then stops for your yes.

## Before the first post (once)
1. **Buffer connected.** On claude.ai: Customize, Connectors, Add custom connector. Name `Buffer`, URL `https://mcp.buffer.com/mcp`. Connect, sign in, approve. Check it works: ask "list my Buffer channels" and note the LinkedIn channel id. Buffer is an official LinkedIn marketing partner, so posts go through LinkedIn's approved API. Never use a tool that clicks around LinkedIn for you.
2. **Your voice.** Copy `voice-profile.example.md` to `~/.claude/linkedin/voice.md` and fill it from your 5 best posts by engagement rate. If the file is missing, ask the user for those 5 posts and write it with them before drafting anything. A post in the wrong voice is worse than no post.

## What the user gives (the drop)
- Files: poster, photos, a video.
- Direction, 1 to 3 lines: what it is, the goal (sign-ups, an update, proof of work), the call to action, and the day it should go out.

## Steps
1. **Folder.** `linkedin-posts/<post-date>_<slug>/` in the working folder, with `drop/` (copies of every file) and `brief.md` (the direction in the user's own words).
2. **Proof check.** Search the user's project folders for every fact the post will use: dates, names, places, numbers, quotes. List each fact with its source file in `brief.md`. A fact with no source stays out of the post or comes back to the user as a question. Never invent a number, a quote, a client or a sign-up count.
3. **Write** `post.txt` in the voice from `voice.md`:
   - Line 1 survives truncation (under about 140 characters on mobile) and says something specific.
   - Short paragraphs, 1 to 3 lines, a blank line between each.
   - Real names, places, hours and months from the proof list.
   - One idea. If there are two, say so and offer two posts.
   - Close with one open door ("send me a message") or one question only this post could ask.
   - Time words match the post time: an event the same evening is "tonight", not "tomorrow".
   - 900 to 1,300 characters, up to 3 hashtags, no links in the body (the link goes in the first comment).
4. **Lint.** `python3 <this skill>/tools/check_post.py post.txt --post-date <YYYY-MM-DD>`. Fix every FAIL. Read the WARN lines and decide; don't rewrite the user's voice to please the linter.
5. **Buffer draft.** Buffer connector `create_post` on the LinkedIn channel with `saveToDraft: true` and the text. Buffer's connector takes media only as public URLs, so tell the user to drag the files from `drop/` into the draft in Buffer (Drafts tab, Edit). If a browser tool is available, it can do the upload instead, with the user watching.
6. **Ask.** Show the final text, the LinkedIn preview from the Buffer draft, and a proposed time. Schedule only when the user says yes for this post: `edit_post` with the scheduled time, keeping the media. A yes for one post is not a yes for the next.
7. **Log.** Append date, slug, Buffer post id and time to `linkedin-posts/log.md`. After 48 hours, read the post's metrics from Buffer and add impressions, reactions, comments and engagement rate, so the next draft learns from what worked.

## Never
- Post, schedule or publish without the user's yes for that post.
- Put a fact in the post that has no source.
- Upload the user's files anywhere except their own Buffer.
- Use an unofficial auto-poster, a browser bot on linkedin.com, or anything that likes, comments or connects on the user's behalf. LinkedIn's User Agreement bans it.
