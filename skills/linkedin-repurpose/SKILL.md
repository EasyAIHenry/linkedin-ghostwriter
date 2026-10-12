---
name: linkedin-repurpose
description: Turns long content the user already made (a video transcript, a podcast, a blog post, a newsletter, a talk) into 3 to 5 LinkedIn posts, one idea each, each standing alone, each quoting or paraphrasing only what is in the source with the timestamp or paragraph it came from. Adds one carousel outline when the source has a list or steps. Lints every post with check_post.py and writes everything to linkedin-posts/repurpose-<slug>/. Use when the user says "repurpose this", "turn this video into LinkedIn posts", "posts from my podcast", "cut my blog into posts", "LinkedIn posts from this transcript", or "/linkedin-repurpose".
---

# linkedin-repurpose

Cuts something long you already made into a few LinkedIn posts that each stand on their own.

## What the user gives
- The source: a transcript file (.txt, .srt, .vtt), a blog post or newsletter (.md, .txt, .html), talk notes or slides, or the text pasted in chat.
- Optional: the goal (clients, hiring, a launch), how many posts (3 to 5), and parts to skip.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, point the user to the linkedin-ghostwriter setup (paste their 5 best posts) and stop.
2. **Folder.** Make `linkedin-posts/repurpose-<slug>/`, with the slug from the source title (lowercase, hyphens). Copy the source in unchanged as `source.<ext>` (pasted text becomes `source.md`).
3. **Locate.** Every claim needs a place in the source:
   - Video, podcast, talk: the timestamp, from the .srt or .vtt cue or the `[hh:mm:ss]` marks in the transcript.
   - Blog, newsletter, notes: number the paragraphs P1, P2 and so on, and save the numbered copy as `source-numbered.md`.
   - Slides: the slide number.
   - No timestamps in a spoken transcript: number its paragraphs the same way and tell the user.
4. **Pick ideas.** Choose 3 to 5 ideas that each make one point on their own. Spread them across the source, not all from the opening. Write `ideas.md`: for each idea, one line on the point, the location, and the exact source words it rests on.
5. **Draft** `post-1.txt` to `post-5.txt` in the user's voice:
   - Line 1 under about 140 characters and specific. 900 to 1,300 characters. Short paragraphs with a blank line between.
   - Stands alone: a reader who never saw the source understands it. No "as I said in part 2".
   - A quote in quotation marks is word for word. You may drop filler words (um, uh, you know) and nothing else.
   - A paraphrase keeps the meaning and the numbers exactly. Nothing from outside the source, no stats from memory.
   - Close with one question only this post could ask, or one open door. No links in the body; a link to the source goes in the first comment.
6. **Sources.** Write `sources.md`: a table per post with every claim, quote and number in it, its location, and the exact source words. A line with no location comes out of the post or goes to the user as a question.
7. **Lint.** `python3 <linkedin-ghostwriter skill>/tools/check_post.py post-N.txt` for each post. Fix every FAIL. Read the WARN lines and decide; keep the user's voice.
8. **Carousel.** Only if the source has a list or steps with 3 or more items, write `carousel.md`:
   - 6 to 10 slides. Slide 1: a title under 8 words. One slide per item: a headline under 8 words, a body under 25 words, the source location. Last slide: a one-line recap and one question.
   - A caption in `carousel-caption.txt`, linted like a post. Under 600 characters is fine; ignore that length WARN.
9. **Show.** Paste each post with its lint line and its source locations. Suggest an order and a gap of at least a day between posts. Point to `linkedin-ghostwriter` to draft each one in Buffer, or `linkedin-plan` to place them in a calendar. Stop there.

## Rules
- One idea per post. If two posts make the same point, cut one.
- The same quote never appears in two posts.
- Other people's words (a guest, an audience question) go in only after the user confirms that person is happy to be quoted. Until then, leave them out.
- If the source got something wrong or out of date, say so to the user. Do not fix it quietly in the post.
- Writing rules: no em dashes, no exclamation marks, no hype words, no "it's not X, it's Y", one idea per sentence, up to 3 hashtags.
- Fewer posts beat thin ones. If the source holds only 2 good ideas, write 2 and say why.

## Never
- Add a fact, number, quote, client or result that is not in the source.
- Post, schedule, send, like, comment, connect, scrape or open linkedin.com for the user. LinkedIn's User Agreement bans bots. This skill writes files only.
- Change or delete the user's source file.
