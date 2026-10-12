import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "linkedin-ghostwriter", "tools"))
from check_post import check  # noqa: E402

GOOD = ("Sam shot a sitcom alone on his sofa.\n\n" + "AI replaced the set, the props and the cast. " * 22 +
        "\n\nWhat would you film first? Send me a message.\n\n#AI #Film")


class CheckPost(unittest.TestCase):
    def test_good_post_passes(self):
        fails, warns = check(GOOD)
        self.assertEqual(fails, [])

    def test_link_in_body_fails(self):
        fails, _ = check(GOOD + "\n\nhttps://example.com")
        self.assertTrue(any("link" in f for f in fails))

    def test_too_many_hashtags_fails(self):
        fails, _ = check(GOOD + " #a #b #c")
        self.assertTrue(any("hashtags" in f for f in fails))

    def test_em_dash_fails(self):
        fails, _ = check("We shipped it — finally.\n\n" + GOOD)
        self.assertTrue(any("dash" in f for f in fails))

    def test_hyphenated_word_is_fine(self):
        fails, _ = check("A third-party app.\n\n" + GOOD)
        self.assertEqual(fails, [])

    def test_empty_fails(self):
        fails, _ = check("   ")
        self.assertEqual(fails, ["empty post"])

    def test_length_warns(self):
        _, warns = check("Short post.")
        self.assertTrue(any("length" in w for w in warns))

    def test_long_first_line_warns(self):
        _, warns = check("x" * 150 + "\n\n" + GOOD)
        self.assertTrue(any("first line" in w for w in warns))

    def test_hype_words_warn(self):
        _, warns = check("This is a game-changer.\n\n" + GOOD)
        self.assertTrue(any("game-changer" in w for w in warns))

    def test_not_x_its_y_warns(self):
        _, warns = check("It's not a tool, it's a team.\n\n" + GOOD)
        self.assertTrue(any("pattern" in w for w in warns))

    def test_exclamation_warns(self):
        _, warns = check("We did it!\n\n" + GOOD)
        self.assertTrue(any("exclamation" in w for w in warns))

    def test_tonight_on_wrong_day_warns(self):
        _, warns = check("See you tonight.\n\n" + GOOD, dt.date(2026, 10, 4), dt.date(2026, 10, 5))
        self.assertTrue(any("tonight" in w for w in warns))

    def test_tomorrow_on_right_day_is_quiet(self):
        _, warns = check("See you tomorrow.\n\n" + GOOD, dt.date(2026, 10, 4), dt.date(2026, 10, 5))
        self.assertFalse(any("tomorrow" in w for w in warns))


if __name__ == "__main__":
    unittest.main()
