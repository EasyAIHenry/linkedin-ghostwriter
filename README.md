# linkedin-ghostwriter

An automated LinkedIn ghostwriter for Claude that stops before the Post button, plus 11 more LinkedIn skills for everything around the post.
You drop in a poster, a photo or a video and a line about what it is. Claude checks the facts against your own files, writes the post in your voice, lints it, saves it as a Buffer draft and shows you the preview. Nothing goes out until you say yes.

On our test (4 October 2026) it took about 10 minutes from dropping three files to a live post.

## What you need
- A paid Claude plan (Pro or above) and the Claude desktop app, using its Code tab.
- A Buffer account with your LinkedIn page connected. We tested on Buffer Essentials.
- Python 3.9 or newer, for the five small tools (standard library only, no network).

## Install

```
git clone https://github.com/EasyAIHenry/linkedin-ghostwriter.git
skillspector scan --no-llm linkedin-ghostwriter     # optional: scan any skill pack before you trust it
cp -r linkedin-ghostwriter/skills/* ~/.claude/skills/
```

Then connect Buffer once: on claude.ai go to Customize, Connectors, Add custom connector. Name `Buffer`, URL `https://mcp.buffer.com/mcp`. Connect, sign in, approve. In the Code tab, test it with `list my Buffer channels`.

Last, give it your voice: copy `skills/linkedin-ghostwriter/voice-profile.example.md` to `~/.claude/linkedin/voice.md` and fill it from your 5 best posts. If you skip this, the skill asks you for those posts before it writes anything.

## Use it

Start a Code tab session in a folder with your notes (past posts, event details, project files), drag in the files, and paste:

```
Help me post this on my LinkedIn [tomorrow at 9 am]. It is about [what it is], and the goal is
[sign-ups / an update / proof of work]. Check my project files for the facts and for things I have
done before that fit. Write it in my voice and lint it. Save it as a draft in Buffer with these files
and show me the preview. Schedule it only after I say yes.
```

Or just say "ghostwrite this for LinkedIn".

## The 12 skills

| Skill | What it does | Say |
| --- | --- | --- |
| `linkedin-ghostwriter` | Files and a line of direction become a fact-checked post in your voice, saved as a Buffer draft. Schedules only on your yes | "ghostwrite this for LinkedIn" |
| `linkedin-post` | One raw idea becomes a finished text post, with 3 opening lines to pick from | "write a LinkedIn post about..." |
| `linkedin-carousel` | A post or idea becomes a 6 to 10 slide PDF carousel (HTML you print to PDF) | "make this a carousel" |
| `linkedin-repurpose` | A video, podcast, blog or talk becomes 3 to 5 posts, each tied to where it came from | "turn this transcript into posts" |
| `linkedin-plan` | A weekly or monthly plan built on your goal, your dates and your own best posting times | "plan my LinkedIn for next month" |
| `linkedin-humanise` | Scores a draft 0 to 100 for machine-written tells and rewrites only the flagged lines | "make this sound less AI" |
| `linkedin-comment` | 2 or 3 comment options for other people's posts, each adding something real | "help me comment on these" |
| `linkedin-reply` | Triages the comments on your posts and drafts the replies | "reply to my comments" |
| `linkedin-dm` | Connection notes, first messages, one follow-up, a polite no to pitches | "write a connection note to..." |
| `linkedin-inbox` | Sorts a batch of messages into today, this week, archive and spam, then drafts today's replies | "sort my LinkedIn inbox" |
| `linkedin-profile` | Headline, About and Featured rewritten from your facts | "rewrite my LinkedIn profile" |
| `linkedin-audit` | Reads your post analytics export and says what works, with the numbers behind it | "audit my LinkedIn posts" |

Every skill writes text and files only. You post, send and reply yourself, or schedule through Buffer with your yes. They all share one voice file, so they all sound like you.

## The ghostwriter, step by step

| Step | What happens | Writes |
| --- | --- | --- |
| Drop | Copies your files and your direction into a folder for this post | `linkedin-posts/<date>_<slug>/drop/`, `brief.md` |
| Proof check | Finds every date, name, number and quote in your own files and lists the source. No source, no fact | `brief.md` |
| Write | Your voice from `voice.md`, a first line that survives the mobile cut, 900 to 1,300 characters | `post.txt` |
| Lint | `tools/check_post.py`: links in the body, hashtags, dashes, hype words, "tonight" on the wrong day | the lint report |
| Draft | Saves a Buffer draft on your LinkedIn channel and shows the preview | the Buffer draft |
| Your yes | Schedules only that post, at the time you pick | the scheduled post |
| Log | Logs the post, then reads its numbers 48 hours later so the next draft learns | `linkedin-posts/log.md` |

Buffer's connector takes media only as public links, so you drag the files into the draft in Buffer yourself (Drafts tab, Edit). It takes a few seconds.

## Stay safe
- **Scan every skill first.** NVIDIA's free SkillSpector: `skillspector scan --no-llm <repo link>`.
- **Only approved apps.** Post through a named LinkedIn partner such as Buffer, which uses LinkedIn's approved API. Read what you approve when you connect it.
- **No bots on LinkedIn.** LinkedIn's User Agreement bans bots that post, comment or like. This skill never touches linkedin.com. Check every draft too: ours once said "tonight" for a class the next day, which is why the linter now checks it.

## Who this is for
- You post on LinkedIn about real work (events, projects, launches) and the writing is what slows you down.
- You're comfortable with the Claude Code tab. If you're just starting on LinkedIn, write and schedule in Buffer by hand until you know what works.

## Fine print
- It writes from your files. If a fact isn't in them, it asks you instead of guessing.
- Prices, plans and connector details were checked on 5 October 2026. Buffer, Anthropic and LinkedIn change them at their own discretion; confirm on their pages before you pay.
- Not affiliated with Buffer, Anthropic or LinkedIn. MIT licence.

## Tests

```
python3 -m unittest discover -s tests
```
