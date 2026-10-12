import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "linkedin-humanise", "tools"))
import humanise_check  # noqa: E402
from humanise_check import check  # noqa: E402

HUMAN = ("I ran the numbers last night.\n"
         "Three of our five clients came from one referral.\n"
         "That surprised me, because I had spent most of the year on cold outreach, posting every weekday "
         "and sending around forty messages a week.\n"
         "So I stopped.\n"
         "Now I ask every happy client one question when the project ends: who else should I talk to?\n"
         "It is slower. It works.")


def tells(result, name):
    return [h for h in result["hits"] if h["tell"] == name]


class HumaniseCheck(unittest.TestCase):
    def test_human_text_scores_high(self):
        r = check(HUMAN)
        self.assertGreaterEqual(r["score"], 85)
        self.assertEqual(r["hits"], [])

    def test_stock_list_has_forty_plus(self):
        self.assertGreaterEqual(len(humanise_check.STOCK), 40)

    def test_stock_phrase_with_line(self):
        r = check("First line is fine.\nIn today's fast-paced world we must delve deeper.")
        hits = tells(r, "stock phrase")
        self.assertEqual(len(hits), 2)
        self.assertTrue(all(h["line"] == 2 for h in hits))

    def test_curly_apostrophe_matches(self):
        r = check("It’s worth noting that this works.")
        self.assertEqual(len(tells(r, "stock phrase")), 1)

    def test_overlap_counts_once(self):
        r = check("Sleep plays a pivotal role in focus.")
        self.assertEqual(len(tells(r, "stock phrase")), 1)

    def test_corporate_word_inside_stock_phrase_not_double_counted(self):
        r = check("Trust plays a crucial role here.")
        self.assertEqual(len(tells(r, "stock phrase")), 1)
        self.assertEqual(tells(r, "corporate word"), [])

    def test_stock_cap(self):
        r = check("\n".join(["We delve into it."] * 20))
        self.assertEqual(r["penalties"]["stock phrase"], 36)

    def test_em_dash_flagged_hyphen_not(self):
        self.assertEqual(len(tells(check("We shipped it — finally."), "dash")), 1)
        self.assertEqual(len(tells(check("We shipped it -- finally."), "dash")), 1)
        self.assertEqual(tells(check("A third-party app from 2020–2024."), "dash"), [])

    def test_not_x_its_y(self):
        self.assertEqual(len(tells(check("It's not a tool, it's a team."), "contrast pattern")), 1)
        self.assertEqual(len(tells(check("This isn't about money. It's about time."), "contrast pattern")), 1)

    def test_not_only_but(self):
        r = check("Not only does it save time but it saves money.")
        self.assertEqual(len(tells(r, "contrast pattern")), 1)

    def test_rule_of_three_adjectives(self):
        self.assertEqual(len(tells(check("Our app is fast, simple and scalable."), "rule of three")), 1)
        self.assertEqual(tells(check("We bought apples, pears and plums."), "rule of three"), [])

    def test_corporate_words(self):
        r = check("A seamless, robust way to elevate your team.")
        self.assertEqual(len(tells(r, "corporate word")), 3)

    def test_same_length_sentences(self):
        flat = "\n".join(["We met the team at noon today."] * 6)
        r = check(flat)
        self.assertEqual(r["penalties"].get("same-length sentences"), 10)
        self.assertNotIn("same-length sentences", check(HUMAN)["penalties"])

    def test_too_many_questions(self):
        r = check("Why wait? Why not now? What else? Who knew?")
        self.assertEqual(r["penalties"]["questions"], 6)
        self.assertNotIn("questions", check("Why wait? Who knew? It works.")["penalties"])

    def test_emoji_bullets(self):
        r = check("Three things:\n\U0001F680 Ship faster\n✅ Sleep better\n- \U0001F4A1 Think less")
        self.assertEqual(len(tells(r, "emoji bullet")), 3)

    def test_score_never_below_zero(self):
        bad = ("In today's fast-paced world, it's worth noting that AI is a game-changer — truly.\n" * 8 +
               "It's not a tool, it's a team. Not only fast but cheap. Fast, simple and scalable.\n" * 4 +
               "\U0001F680 Seamless, robust, elevate, leverage, holistic.\n" * 5 + "Why? How? What? Who? When?\n")
        self.assertEqual(check(bad)["score"], 0)

    def test_empty_text(self):
        r = check("")
        self.assertEqual(r["score"], 100)
        self.assertEqual(r["hits"], [])

    def test_main_fail_under(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("In today's fast-paced world we delve into synergy — always.")
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = humanise_check.main([f.name, "--fail-under", "90"])
            self.assertEqual(code, 1)
            self.assertIn("Score", out.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(humanise_check.main([f.name]), 0)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
