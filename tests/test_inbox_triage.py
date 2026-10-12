import contextlib
import datetime as dt
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "linkedin-inbox", "tools"))
import inbox_triage  # noqa: E402
from inbox_triage import parse_date, read_rows, run, table, triage  # noqa: E402

TODAY = dt.date(2026, 10, 12)
NAMES = ["Henry Chua", "Henry"]


def msg(text, date="2026-10-11", sender="A Sender"):
    return {"from": sender, "date": date, "text": text}


def pile(text, date="2026-10-11"):
    return triage(msg(text, date), NAMES, TODAY)[0]


def write_csv(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="")
    f.write(content)
    f.close()
    return f.name


class InboxTriage(unittest.TestCase):
    def test_recent_question_is_today(self):
        self.assertEqual(pile("Are you free to speak at our meetup in November?"), "today")

    def test_named_question_ten_days_is_today(self):
        self.assertEqual(pile("Henry, can you share the deck from the workshop?", "2026-10-02"), "today")

    def test_older_question_is_week(self):
        self.assertEqual(pile("Can you share the deck from the workshop?", "2026-09-25"), "week")

    def test_very_old_question_is_unsure(self):
        self.assertEqual(pile("Can you share the deck?", "2026-07-01"), "unsure")

    def test_links_only_is_spam(self):
        self.assertEqual(pile("https://example.com/offer check this"), "spam")

    def test_two_pitch_phrases_is_spam(self):
        self.assertEqual(pile("We help agencies with lead generation. Got 15 minutes?"), "spam")

    def test_pitch_plus_money_is_spam(self):
        self.assertEqual(pile("Our agency can cut your costs by $5,000 a month."), "spam")

    def test_one_pitch_phrase_is_unsure(self):
        self.assertEqual(pile("Would you be open to a coffee after your talk?"), "unsure")

    def test_seo_needs_whole_word(self):
        self.assertNotEqual(pile("Loved your post about Seoul. Where did you stay?"), "spam")

    def test_thank_you_is_archive(self):
        self.assertEqual(pile("Thanks for the connect."), "archive")

    def test_old_without_question_is_archive(self):
        self.assertEqual(pile("Good to meet you at the conference last month.", "2026-08-01"), "archive")

    def test_named_without_question_is_week(self):
        self.assertEqual(pile("Henry, I read your guide and tried it with my team.", "2026-10-08"), "week")

    def test_money_without_question_is_unsure(self):
        self.assertEqual(pile("Invoice 12 is paid, see the attached receipt.", "2026-10-10"), "unsure")

    def test_bad_date_is_unsure(self):
        self.assertEqual(pile("Can we talk?", "sometime"), "unsure")

    def test_empty_is_archive(self):
        self.assertEqual(pile(""), "archive")

    def test_parse_linkedin_export_date(self):
        self.assertEqual(parse_date("2026-10-10 08:12:33 UTC"), dt.date(2026, 10, 10))
        self.assertEqual(parse_date("2026-10-10"), dt.date(2026, 10, 10))
        self.assertIsNone(parse_date(""))

    def test_reads_linkedin_export_headers(self):
        path = write_csv("CONVERSATION ID,FROM,TO,DATE,SUBJECT,CONTENT\n"
                         "1,A Sender,Henry Chua,2026-10-11 09:00:00 UTC,,Can we talk on Friday?\n")
        try:
            rows = read_rows(path)
        finally:
            os.unlink(path)
        self.assertEqual(rows, [{"from": "A Sender", "date": "2026-10-11 09:00:00 UTC",
                                 "text": "Can we talk on Friday?"}])

    def test_missing_columns_raise(self):
        path = write_csv("name,when\nA,2026-10-11\n")
        try:
            with self.assertRaises(ValueError):
                read_rows(path)
        finally:
            os.unlink(path)

    def test_own_messages_skipped(self):
        rows = [msg("Sure, Friday works.", sender="Henry Chua"), msg("Is Friday still on?")]
        results, skipped = run(rows, NAMES, TODAY)
        self.assertEqual(skipped, 1)
        self.assertEqual([r["pile"] for r in results], ["today"])

    def test_table_escapes_pipes_and_sorts(self):
        rows = [msg("Thanks for the connect."), msg("Quick one | are you free on Friday?")]
        out = table(run(rows, NAMES, TODAY)[0])
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("| # | From |"))
        self.assertIn("today", lines[2])
        self.assertIn("\\|", lines[2])
        self.assertIn("archive", lines[3])

    def test_main_prints_counts(self):
        path = write_csv("from,date,text\nA Sender,2026-10-11,Can we talk?\nB Sender,2026-10-11,https://x.io\n")
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = inbox_triage.main([path, "--name", "Henry Chua", "--today", "2026-10-12"])
        finally:
            os.unlink(path)
        self.assertEqual(code, 0)
        self.assertIn("today 1", out.getvalue())
        self.assertIn("spam 1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
