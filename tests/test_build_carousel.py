import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "linkedin-carousel", "tools"))
from build_carousel import main, render, validate  # noqa: E402


def deck(n=7, **extra):
    slides = [{"heading": "Five checks before you send an invoice", "body": "Each one cost us a late payment."}]
    slides += [{"heading": f"Check {i}", "body": "Put the due date in the first line."} for i in range(1, n - 1)]
    slides += [{"heading": "Which check would you add?", "body": "Send me a message."}]
    data = {"title": "Invoice checks", "slides": slides}
    data.update(extra)
    return data


class Validate(unittest.TestCase):
    def test_good_deck_has_no_errors(self):
        errors, warns = validate(deck())
        self.assertEqual(errors, [])
        self.assertEqual(warns, [])

    def test_too_few_slides(self):
        errors, _ = validate(deck(5))
        self.assertTrue(any("5 slides" in e for e in errors))

    def test_too_many_slides(self):
        errors, _ = validate(deck(11))
        self.assertTrue(any("11 slides" in e for e in errors))

    def test_six_and_ten_are_allowed(self):
        self.assertEqual(validate(deck(6))[0], [])
        self.assertEqual(validate(deck(10))[0], [])

    def test_missing_heading(self):
        data = deck()
        data["slides"][2]["heading"] = "  "
        errors, _ = validate(data)
        self.assertTrue(any("slide 3 has no heading" in e for e in errors))

    def test_slides_must_be_a_list(self):
        errors, _ = validate({"slides": "one"})
        self.assertTrue(errors)

    def test_bad_colour(self):
        errors, _ = validate(deck(brand={"accent": "red; background:url(x)"}))
        self.assertTrue(any("accent" in e for e in errors))

    def test_short_hex_colour_is_fine(self):
        self.assertEqual(validate(deck(brand={"accent": "#0af"}))[0], [])

    def test_font_injection_rejected(self):
        errors, _ = validate(deck(brand={"heading_font": 'Inter"; } body { display:none'}))
        self.assertTrue(any("heading_font" in e for e in errors))

    def test_long_text_warns(self):
        data = deck()
        data["slides"][1]["heading"] = "x" * 61
        data["slides"][1]["body"] = "y" * 281
        _, warns = validate(data)
        self.assertTrue(any("heading" in w for w in warns))
        self.assertTrue(any("body" in w for w in warns))

    def test_dash_and_exclamation_warn(self):
        data = deck()
        data["slides"][1]["body"] = "We shipped it \u2014 finally!"
        _, warns = validate(data)
        self.assertTrue(any("dash" in w for w in warns))
        self.assertTrue(any("exclamation" in w for w in warns))


class Render(unittest.TestCase):
    def test_one_section_per_slide(self):
        out = render(deck(8))
        self.assertEqual(out.count('<section class="slide'), 8)
        self.assertIn("1 / 8", out)
        self.assertIn("8 / 8", out)

    def test_page_size_is_1080_by_1350(self):
        out = render(deck())
        self.assertIn("@page { size: 1080px 1350px; margin: 0; }", out)
        self.assertIn("width: 1080px; height: 1350px", out)

    def test_cover_and_last_slide_classes(self):
        out = render(deck())
        self.assertIn('class="slide cover"', out)
        self.assertIn('class="slide last"', out)
        self.assertEqual(out.count("<h1>"), 1)

    def test_text_is_escaped(self):
        data = deck()
        data["slides"][1]["body"] = "<script>alert(1)</script> & more"
        out = render(data)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("&amp; more", out)

    def test_blank_lines_make_paragraphs(self):
        data = deck()
        data["slides"][1]["body"] = "First.\n\nSecond.\nSame paragraph."
        out = render(data)
        self.assertIn("<p>First.</p><p>Second.<br>Same paragraph.</p>", out)

    def test_brand_colours_and_fonts_used(self):
        out = render(deck(brand={"accent": "#123456", "heading_font": "Brand Sans"}))
        self.assertIn("#123456", out)
        self.assertIn('"Brand Sans", -apple-system', out)
        self.assertIn("#FAFAF7", out)

    def test_self_contained(self):
        out = render(deck())
        self.assertNotIn("<link", out)
        self.assertNotIn("<script", out)
        self.assertNotIn("http", out)

    def test_title_defaults_to_cover_heading(self):
        data = deck()
        del data["title"]
        self.assertIn("<title>Five checks before you send an invoice</title>", render(data))


class Cli(unittest.TestCase):
    def run_main(self, data):
        with tempfile.TemporaryDirectory() as d:
            src, out = os.path.join(d, "slides.json"), os.path.join(d, "carousel.html")
            with open(src, "w", encoding="utf-8") as f:
                f.write(data if isinstance(data, str) else json.dumps(data))
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([src, "-o", out])
            written = open(out, encoding="utf-8").read() if os.path.exists(out) else None
        return code, written

    def test_writes_html(self):
        code, written = self.run_main(deck())
        self.assertEqual(code, 0)
        self.assertTrue(written.startswith("<!doctype html>"))

    def test_errors_write_nothing(self):
        code, written = self.run_main(deck(3))
        self.assertEqual(code, 1)
        self.assertIsNone(written)

    def test_bad_json(self):
        code, written = self.run_main("{not json")
        self.assertEqual(code, 1)
        self.assertIsNone(written)


if __name__ == "__main__":
    unittest.main()
