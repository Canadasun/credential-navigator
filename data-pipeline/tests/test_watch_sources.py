import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crawlers.watch_sources import Fetched, check, fingerprint, matrix_sources  # noqa: E402

PAGE = "<html><nav>Menu {}</nav><main><h1>Fees</h1><p>Application fee: ${}</p></main><footer>{}</footer></html>"
URL = "https://example.ca/fees"


def site(pages, robots=None):
    calls = []

    def fetch(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return Fetched(200, robots) if robots else Fetched(404)
        return pages.get(url, Fetched(404))
    fetch.calls = calls
    return fetch


class FingerprintTests(unittest.TestCase):
    def test_ignores_menus_footers_and_whitespace(self):
        a = PAGE.format("A", "500", "2025")
        b = PAGE.format("B", "500", "2026").replace("<p>", "<p>\n   ")
        self.assertEqual(fingerprint(a), fingerprint(b))

    def test_ignores_approximate_currency_conversions(self):
        a = PAGE.format("", "750 CAD (approx. $525 USD)", "")
        b = PAGE.format("", "750 CAD (approx. $531 USD)", "")
        self.assertEqual(fingerprint(a), fingerprint(b))
        c = PAGE.format("", "$750 CAD ($525 USD)*", "")
        d = PAGE.format("", "$750 CAD ($531 USD)*", "")
        e = PAGE.format("", "$800 CAD ($531 USD)*", "")
        self.assertEqual(fingerprint(c), fingerprint(d))
        self.assertNotEqual(fingerprint(c), fingerprint(e))  # the fee itself changed

    def test_pdfs_are_compared_by_text(self):
        pdf = (Path(__file__).resolve().parents[2] / "backend/tests/fixtures/mechanical_transcript.pdf").read_bytes()
        resaved = pdf.replace(b"%%EOF", b"%%EOF\n% re-saved\n")
        self.assertEqual(Fetched(200, "", pdf).fingerprint(), Fetched(200, "", resaved).fingerprint())

    def test_compressed_responses_are_decoded(self):
        import gzip
        import zlib
        from crawlers.watch_sources import decompress
        html = PAGE.format("", "750", "").encode()
        self.assertEqual(decompress(gzip.compress(html), "gzip"), html)
        self.assertEqual(decompress(gzip.compress(html), ""), html)  # gzip sent without the header
        self.assertEqual(decompress(zlib.compress(html), "deflate"), html)
        import brotli
        self.assertEqual(decompress(brotli.compress(html), "br"), html)
        self.assertEqual(decompress(html, ""), html)

    def test_detects_a_changed_fee(self):
        self.assertNotEqual(fingerprint(PAGE.format("", "500", "")), fingerprint(PAGE.format("", "550", "")))


class CheckTests(unittest.TestCase):
    def run_check(self, fetch, snapshots):
        return check({URL: "Test: Fees"}, snapshots, fetch=fetch, delay=0, today=date(2026, 10, 25))

    def test_first_run_records_baseline(self):
        findings, snaps = self.run_check(site({URL: Fetched(200, PAGE.format("", "500", ""))}), {})
        self.assertEqual(findings[0]["status"], "new")
        self.assertEqual(snaps[URL]["checked_on"], "2026-10-25")

    def test_unchanged_and_changed(self):
        _, snaps = self.run_check(site({URL: Fetched(200, PAGE.format("", "500", ""))}), {})
        same, _ = self.run_check(site({URL: Fetched(200, PAGE.format("x", "500", "y"))}), snaps)
        self.assertEqual(same[0]["status"], "unchanged")
        changed, _ = self.run_check(site({URL: Fetched(200, PAGE.format("", "550", ""))}), snaps)
        self.assertEqual(changed[0]["status"], "changed")

    def test_missing_page_keeps_old_baseline(self):
        old = {URL: {"hash": "abc", "checked_on": "2026-01-01"}}
        findings, snaps = self.run_check(site({}), old)
        self.assertEqual(findings[0]["status"], "missing")
        self.assertEqual(snaps[URL]["hash"], "abc")

    def test_pages_no_longer_cited_leave_the_baseline(self):
        old = {"https://example.ca/retired": {"hash": "abc", "checked_on": "2026-01-01"}}
        _, snaps = self.run_check(site({URL: Fetched(200, PAGE.format("", "500", ""))}), old)
        self.assertEqual(set(snaps), {URL})

    def test_server_error_is_reported(self):
        findings, _ = self.run_check(site({URL: Fetched(503)}), {})
        self.assertEqual(findings[0]["status"], "error")

    def test_robots_disallow_is_respected(self):
        fetch = site({URL: Fetched(200, "x")}, robots="User-agent: *\nDisallow: /fees\n")
        findings, _ = self.run_check(fetch, {})
        self.assertEqual(findings[0]["status"], "blocked")
        self.assertNotIn(URL, fetch.calls)


class MatrixSourcesTests(unittest.TestCase):
    def test_every_matrix_source_is_watched(self):
        sources = matrix_sources()
        self.assertTrue(any("apega.ca" in u for u in sources))
        self.assertTrue(any("nurses.ab.ca" in u for u in sources))
        self.assertTrue(any("/exams/technical/software-engineering" in u for u in sources))


if __name__ == "__main__":
    unittest.main()
