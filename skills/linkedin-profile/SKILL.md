---
name: linkedin-profile
description: Rewrites the user's LinkedIn headline, About section and Featured section from their own facts. They paste their current profile text; it returns two headline options under 220 characters, an About under 2,600 characters whose first 3 lines carry the message, and 3 Featured picks from what they already have. It never edits the profile itself. Use when the user says "rewrite my LinkedIn profile", "fix my headline", "write my About section", "what should I feature", "profile makeover", or "/linkedin-profile".
---

# linkedin-profile

Turn the user's pasted profile and facts into a headline, an About and a Featured plan they paste in by hand.

## What the user gives
- Their current headline, About and Featured items, pasted as text. Not a link.
- Who they help, what result they get them, and the proof: numbers, clients, projects, awards, with where each one is written down.
- What they want people to do next: book a call, send a message, buy, hire.
- What they already have that could be featured: posts, articles, a site, a lead magnet, a case study, a talk.

## Steps
1. **Voice.** Read `~/.claude/linkedin/voice.md`. If it is missing, stop and point the user to the linkedin-ghostwriter setup: copy `voice-profile.example.md` to that path and fill it from their 5 best posts.
2. **Folder.** Make `linkedin-posts/profile/<YYYY-MM-DD>/`. Save the pasted text as `current.md`.
3. **Proof list.** In `facts.md`, list every fact the new profile may use, each with its source (the user's message, the voice file's "My facts", a project file). A fact with no source becomes a question in the reply, not a line in the profile.
4. **Headline, two options.** Each under 220 characters, counted and shown. Shape: who they help, the result, one proof point. Example shape, not content: "I help <who> <get what result>. <One proof point with its number>." Option A leads with the person helped. Option B leads with the proof point. No job-title soup, no list of five skills separated by bars.
5. **About.** Under 2,600 characters, counted and shown.
   - Lines 1 to 3: the whole message, because that is what shows before "see more". Who they help, the problem, the result. Keep these 3 lines short, about 300 characters together.
   - Then proof: 2 to 4 specific results, each a sentence with a real number or name from `facts.md`.
   - Then how they work: what working with them looks like, in plain steps.
   - Then how to start: one clear next step, such as "Send me a message with <what to include>."
   - Short paragraphs, a blank line between each, first person, no hashtags.
   - Save it as `about.txt` in the folder.
6. **Featured, 3 picks.** Only from what the user already has. For each: the item, why it earns a slot (proof, a free useful thing, or the way to buy), and a title of up to about 60 characters. Order them: the strongest proof first, the next step last. If they have fewer than 3 good items, say which gap to fill and stop there.
7. **Check.** Run `python3 ~/.claude/skills/linkedin-ghostwriter/tools/check_post.py about.txt` on the About; fix every FAIL and ignore the 900 to 1,300 length warning, which is for posts. If `~/.claude/skills/linkedin-humanise/tools/humanise_check.py` is installed, run it on the About and fix any tell it lists.
8. **Write `profile.md`** with: headline A and B with character counts, the About with its count, the Featured table, and the open questions. Show it to the user, then the questions.
9. **Log.** Append one line to `linkedin-posts/log.md`: date, `profile`, headline chosen if they pick one.

## Rules
- Only the user's facts. Never invent a client, a number, a title, a testimonial or a result.
- Be specific: a named audience and a counted result beat "helping businesses grow".
- Write as the user, in first person, in the voice from `voice.md`.
- Writing rules: no em dashes, no exclamation marks, no hype words (game-changer, unlock, leverage, journey, passionate about), no "it's not X, it's Y", one idea per sentence, plain words.
- Keep anything from the current profile that already works, and say why you kept it.

## Never
- Log in to LinkedIn, open linkedin.com, scrape the profile or edit it for the user. LinkedIn's User Agreement bans bots. The user pastes the text in and pastes the result back by hand.
- Post, send, like, comment or connect for the user.
- Go over 220 characters for a headline or 2,600 for the About.
