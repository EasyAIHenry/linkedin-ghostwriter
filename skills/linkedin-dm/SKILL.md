---
name: linkedin-dm
description: Drafts LinkedIn messages the user sends by hand. Connection notes under 300 characters with a specific reason, first messages after connecting, one follow-up after a week of silence that adds something new, and polite no replies to inbound pitches. Every message uses a real detail from what the user pasted about the person, makes one ask, and is easy to answer. It never sends. Use when the user says "write a connection note", "message this person on LinkedIn", "follow up on LinkedIn", "how do I say no to this pitch", "draft a DM", or "/linkedin-dm".
---

# linkedin-dm

Write one short, personal LinkedIn message the user can copy and send themselves.

## What the user gives
- Which message: a connection note, a first message, a follow-up, or a reply to a pitch.
- What they know about the person, pasted: their headline, a post they wrote, where they met, a shared contact. For a pitch reply, the pitch itself.
- Why they want to talk, and the one thing they want to ask.
- For a follow-up: the first message and the date it was sent.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, stop and point the user to the linkedin-ghostwriter setup: copy `voice-profile.example.md` to that path and fill it from their 5 best posts.
2. **Find the real detail.** Pick one specific thing from what the user pasted: a line from a post, a project, the event they both attended. Quote where it came from. If there is no real detail, say so and ask for one. Do not write "I came across your profile and was impressed".
3. **Draft by type.**
   - **Connection note:** under 300 characters, counted and shown. The detail, the reason to connect, nothing to sell.
   - **First message after connecting:** 3 to 5 short sentences. Thanks for connecting in a few words, the detail, why the user is writing, one ask.
   - **Follow-up:** only one, and only if 7 days or more have passed since the first message. It adds something new: a useful link for them, a result, an answer to something they posted. It never says "just bumping this" or "following up on my last message". If fewer than 7 days have passed, say how many to wait.
   - **Reply to a pitch:** a polite no in 1 to 3 sentences. Thank them, say no clearly, no reason needed, no door left open unless the user wants one.
4. **One ask, easy to answer.** End with a question that takes yes, no or one line to answer. "Would a 15-minute call next week work?" is fine. "Let me know your thoughts" is not an ask.
5. **Check.** No em dashes, no exclamation marks, no hype words, no "it's not X, it's Y", nothing that reads as a template with a name swapped in. Read it once as the person: would they know it was written for them?
6. **Save.** Write `linkedin-posts/dms/<YYYY-MM-DD>_<person-slug>_<type>.md` with the detail and its source, the message, its character count and, for a first message, the earliest follow-up date. Show the user the message ready to copy.
7. **Log.** Append one line to `linkedin-posts/log.md`: date, `dm`, type, person slug, follow-up due date if any.

## Rules
- One message, one ask. If the user wants two things, pick the one that matters and say why.
- Use only what the user pasted. Never invent a mutual contact, a shared event or praise for work you have not seen.
- Short beats clever. Most messages fit in 4 lines on a phone.
- Write in the user's voice, first person, plain words, one idea per sentence.
- If the user asks for many near-identical messages to send in bulk, say that LinkedIn treats mass outreach as spam and write each one only from its own real detail.

## Never
- Send, connect, follow, like, comment or open linkedin.com for the user. LinkedIn's User Agreement bans bots. The skill writes text and files only; the user copies and sends each message by hand.
- Write a template that pretends to be personal.
- Draft a second follow-up. After one follow-up with no reply, the answer is to stop.
- Scrape or look up the person online. Work only from what the user pasted.
