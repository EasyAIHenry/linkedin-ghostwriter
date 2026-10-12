---
name: linkedin-carousel
description: Turns a post or an idea into a LinkedIn document carousel. It plans 6 to 10 slides (a cover that promises something specific, one idea per slide, one call to action at the end), writes the slide text in your voice, builds one self-contained HTML file with a 1080x1350 page per slide, and tells you how to print it to PDF for upload. Use when the user says "make a carousel", "turn this post into a carousel", "LinkedIn carousel", "document post", "PDF slides for LinkedIn", or "/linkedin-carousel".
---

# linkedin-carousel

A post or an idea in, a 1080x1350 PDF carousel out, ready to upload by hand.

## What the user gives
- A finished post (pasted, or a `post.txt` path), or a raw idea in a sentence or two.
- Optional: brand colours as hex codes, brand fonts, and a footer line (their name and what they do).

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, say so, point to the linkedin-ghostwriter setup (fill the voice file from your 5 best posts) and stop.
2. **Facts.** List every number, name and result the slides will use, with its source (the post, `voice.md`, a file the user named). If the idea has no specific true thing (what happened, to whom, what it cost or returned), ask one batched message with up to 3 numbered questions and wait.
3. **Folder.** Create `linkedin-posts/<post-date>_<slug>-carousel/`. Write `plan.md`: the facts with sources, then one line per slide.
4. **Plan 6 to 10 slides.**
   - Slide 1, the cover: a heading that promises something specific (a count, a result, a named problem), up to 10 words, and an optional line under it.
   - Middle slides: one idea each. A heading up to 8 words, a body up to 40 words.
   - Last slide: one call to action only (a question, "send me a message", or "save this for later"). Never two.
   - The slides read in order without the post. Each one earns the swipe to the next.
5. **Write** `slides.json`:
   `{"title": "...", "footer": "...", "brand": {"background": "#hex", "text": "#hex", "accent": "#hex", "heading_font": "...", "body_font": "..."}, "slides": [{"heading": "...", "body": "..."}]}`.
   Leave out `brand` keys the user did not give; the tool uses a plain light default. A blank line in `body` starts a new paragraph.
6. **Lint the words.** Write every heading and body into `slides.txt`, one slide per paragraph, and run `python3 ~/.claude/skills/linkedin-ghostwriter/tools/check_post.py slides.txt`. Fix every FAIL and every dash, hype word, exclamation and "it's not X, it's Y" WARN. Ignore the length and first-line WARNs; slides are short.
7. **Build.** Run `python3 <this skill>/tools/build_carousel.py slides.json -o carousel.html`. Fix every ERROR. Shorten any slide with a length WARN, because text past the page edge is cut off.
8. **Print to PDF.** Tell the user either way, and offer to run the first one:
   - Headless Chrome on a Mac: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --no-pdf-header-footer --print-to-pdf=carousel.pdf "file://$PWD/carousel.html"` (on Linux the binary is `google-chrome` or `chromium`).
   - Any browser: open `carousel.html`, Print, Save as PDF, margins None, background graphics on. The preview must show one page per slide.
9. **Check.** Confirm `carousel.pdf` has one page per slide and that no text runs off a page. If it does, shorten that slide and build again.
10. **Hand over.** Show the slide text as a numbered list and the file paths. The user uploads the PDF by hand (start a post, add a document, give it a title). For the text above the document, suggest linkedin-post.

## Rules
- Slide text is in the user's voice, with plain words and one idea per sentence.
- No em dashes, no exclamation marks, no hype words (game-changer, unlock, leverage, journey, excited to announce), no "it's not X, it's Y".
- Every fact on a slide has a source in `plan.md`.
- Brand fonts only render if they are installed on the machine that prints. Otherwise the tool falls back to system fonts; say so.
- Colours must be hex codes. Ask for them rather than guessing from a logo.

## Never
- Invent a number, a client, a quote or a result to fill a slide.
- Put a link on a slide or more than one call to action.
- Post, upload, schedule, send, like, comment, connect, scrape or open linkedin.com for the user. LinkedIn's User Agreement bans bots. The user uploads the PDF by hand, or schedules through Buffer (an official LinkedIn partner) only with their explicit yes.
