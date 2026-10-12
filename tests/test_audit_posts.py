import contextlib
import datetime as dt
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "skills", "linkedin-audit", "tools"))
from audit_posts import (audit, ends_with_question, find_columns, main, parse_number,  # noqa: E402
                         parse_when)

FIXTURE = os.path.join(HERE, "audit_posts_fixture.csv")


def fixture_report(**kw):
    with open(FIXTURE, encoding="utf-8") as f:
        return audit(f.read(), source="fixture", **kw)


def small_csv(n, delim=","):
    rows = [delim.join(["Date", "Text", "Impressions", "Likes", "Comments", "Shares"])]
    for i in range(n):
        rows.append(delim.join([f"2026-09-{i % 28 + 1:02d}", f"Post {i}", "1000", str(10 + i), "2", "0"]))
    return "\n".join(rows) + "\n"


class Numbers(unittest.TestCase):
    def test_thousands_separator(self):
        self.assertEqual(parse_number("1,234"), 1234.0)

    def test_k_suffix_and_percent(self):
        self.assertEqual(parse_number("1.2k"), 1200.0)
        self.assertEqual(parse_number("3.4%"), 3.4)

    def test_blank_and_dash_are_none(self):
        self.assertIsNone(parse_number(""))
        self.assertIsNone(parse_number(" - "))
        self.assertIsNone(parse_number("n/a"))


class Dates(unittest.TestCase):
    def test_iso_with_time(self):
        self.assertEqual(parse_when("2026-10-05T08:30:00Z"), (dt.date(2026, 10, 5), (8, 30)))

    def test_slash_is_month_first_by_default(self):
        self.assertEqual(parse_when("10/05/2026")[0], dt.date(2026, 10, 5))

    def test_slash_day_first(self):
        self.assertEqual(parse_when("10/05/2026", day_first=True)[0], dt.date(2026, 5, 10))

    def test_slash_first_number_over_12_is_the_day(self):
        self.assertEqual(parse_when("25/09/2026")[0], dt.date(2026, 9, 25))

    def test_month_names_and_pm(self):
        self.assertEqual(parse_when("Mon, 5 Oct 2026 8:30 PM"), (dt.date(2026, 10, 5), (20, 30)))
        self.assertEqual(parse_when("Oct 5, 2026")[0], dt.date(2026, 10, 5))

    def test_separate_time_column(self):
        self.assertEqual(parse_when("2026-10-05", "9 am"), (dt.date(2026, 10, 5), (9, 0)))

    def test_no_date(self):
        self.assertEqual(parse_when("soon"), (None, None))


class Columns(unittest.TestCase):
    def test_linkedin_style_headers(self):
        cols = find_columns(["Created date", "Post title", "Impressions", "Reactions", "Comments", "Reposts"])
        self.assertEqual([cols[k] for k in ("date", "text", "impressions", "reactions", "comments", "reposts")],
                         [0, 1, 2, 3, 4, 5])

    def test_buffer_style_headers(self):
        cols = find_columns(["Date", "Text", "Views", "Likes", "Comments", "Shares"])
        self.assertEqual(cols["impressions"], 2)
        self.assertEqual(cols["reactions"], 3)
        self.assertEqual(cols["reposts"], 5)

    def test_unique_impressions_and_rates_are_not_used(self):
        cols = find_columns(["Date", "Unique impressions", "Impressions (organic)", "Engagement rate", "Likes"])
        self.assertEqual(cols["impressions"], 2)
        self.assertNotIn("engagements", cols)

    def test_link_column_is_not_the_text(self):
        cols = find_columns(["Post link", "Post content", "Impressions", "Likes"])
        self.assertEqual(cols["text"], 1)


class Question(unittest.TestCase):
    def test_question_before_hashtags(self):
        self.assertTrue(ends_with_question("Line one.\n\nWhat would you cut first?\n\n#Onboarding #Teams"))

    def test_question_mid_post_only(self):
        self.assertFalse(ends_with_question("Why now?\n\nBecause it was ready."))


class FixtureReport(unittest.TestCase):
    def setUp(self):
        self.r = fixture_report()

    def test_counts_and_zero_impressions_skipped(self):
        self.assertIn("Posts used: 10.", self.r)
        self.assertIn("1 zero impressions", self.r)

    def test_small_sample_flag(self):
        self.assertIn("Small sample: 10 posts (under 20)", self.r)

    def test_medians(self):
        self.assertIn("Median impressions: 1,650", self.r)
        self.assertIn("Median engagement rate: 2.62%", self.r)
        self.assertIn("559 engagements on 16,500 impressions (3.39%)", self.r)

    def test_top_and_bottom(self):
        top = self.r.split("## Top 20%")[1].split("## Bottom")[0]
        bottom = self.r.split("## Bottom 20%")[1].split("## By weekday")[0]
        self.assertIn("(2 of 10)", top)
        self.assertIn("| 6 | 2026-09-15 | Tue | 08:45 | 3,000 | 4.60% |", top)
        self.assertIn("| 3 | 2026-09-08 | Tue | 08:00 | 2,400 | 4.50% |", top)
        self.assertIn("| 8 | 2026-09-19 | Sat | 17:30 | 600 | 1.00% |", bottom)
        self.assertIn("| 5 | 2026-09-12 | Sat | 18:00 | 800 | 1.25% |", bottom)

    def test_best_weekday_and_hour(self):
        self.assertIn("Best by median engagement rate: Tue (4.25%, n = 4).", self.r)
        self.assertIn("| Sat (few posts) | 2 |", self.r)
        self.assertIn("Best by median engagement rate: 08:00 to 08:59 (4.50%, n = 3).", self.r)

    def test_length_bands(self):
        self.assertIn("Best by median engagement rate: 900 to 1,300 (4.00%, n = 5).", self.r)

    def test_question_effect(self):
        self.assertIn("| Ends with a question | 4 | 2,200 | 4.25% |", self.r)
        self.assertIn("| No question | 6 | 1,100 | 1.90% |", self.r)
        self.assertIn("+2.35 points", self.r)

    def test_posts_per_week_and_type(self):
        self.assertIn("Best by median engagement rate: 2 posts in a week (3.20%, n = 4).", self.r)
        self.assertIn("Best by median engagement rate: carousel (4.50%, n = 3).", self.r)

    def test_rank_by_impressions(self):
        r = fixture_report(rank_by="impressions")
        top = r.split("## Top 20%")[1].split("## Bottom")[0]
        self.assertIn("by impressions", r)
        self.assertIn("| 6 | 2026-09-15 |", top)
        self.assertIn("| 3 | 2026-09-08 |", top)


class OtherInputs(unittest.TestCase):
    def test_title_rows_above_header(self):
        r = audit("Post analytics\nExported 2026-10-01\n\n" + small_csv(5))
        self.assertIn("Posts used: 5.", r)

    def test_semicolon_delimiter(self):
        r = audit(small_csv(5, delim=";"))
        self.assertIn("Posts used: 5.", r)

    def test_twenty_posts_has_no_small_sample_flag(self):
        self.assertNotIn("Small sample", audit(small_csv(20)))

    def test_short_text_skips_length_and_question(self):
        r = audit(small_csv(5))
        self.assertIn("looks like first lines only", r)
        self.assertNotIn("Ends with a question |", r)

    def test_no_times_means_no_hour_table(self):
        self.assertIn("the file has no times", audit(small_csv(5)))

    def test_missing_reposts_counts_as_zero_and_is_said(self):
        csv_text = "Date,Impressions,Reactions,Comments\n2026-09-01,200,8,2\n"
        r = audit(csv_text)
        self.assertIn("counted as 0: reposts", r)
        self.assertIn("Median engagement rate: 5.00%", r)

    def test_markdown_log_table(self):
        log = ("# Log\n\n| Date | Slug | Buffer id | Impressions | Reactions | Comments |\n"
               "| --- | --- | --- | --- | --- | --- |\n"
               "| 2026-10-01 09:00 | launch-week | abc | 1,000 | 30 | 10 |\n"
               "| 2026-10-03 09:00 | studio-photo | def | 500 | 5 | 0 |\n"
               "| 2026-10-05 09:00 | not-measured-yet | ghi |  |  |  |\n")
        r = audit(log, markdown=True)
        self.assertIn("Posts used: 2.", r)
        self.assertIn("1 no impressions number", r)
        self.assertIn("| 1 | 2026-10-01 | Thu | 09:00 | 1,000 | 4.00% | launch-week |", r)

    def test_no_impressions_column_is_an_error(self):
        with self.assertRaises(ValueError):
            audit("Date,Text,Likes\n2026-09-01,Hello,5\n")


class Cli(unittest.TestCase):
    def test_main_prints_report(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([FIXTURE])
        self.assertEqual(code, 0)
        self.assertTrue(buf.getvalue().startswith("# Post audit"))

    def test_main_exit_2_on_bad_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("a,b\n1,2\n")
            path = f.name
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main([path]), 2)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
