import gzip
import unittest

from webcrew.browser import decode_html
from webcrew.core import Error


class EncodingTests(unittest.TestCase):
    def test_gzip_html_decodes_without_relaxing_size_limit(self):
        html = b"<p>Step-free access is available.</p>"
        self.assertEqual(decode_html(gzip.compress(html), {"content-encoding": "gzip"}), html)

    def test_gzip_bomb_is_bounded(self):
        with self.assertRaises(Error):
            decode_html(gzip.compress(b"x" * 1_000_001), {"content-encoding": "gzip"})

    def test_truncated_or_extra_gzip_member_rejected(self):
        raw = gzip.compress(b"<p>Public page</p>")
        for body in [raw[:-4], raw + raw, b"invalid"]:
            with self.subTest(size=len(body)), self.assertRaises(Error):
                decode_html(body, {"content-encoding": "gzip"})

    def test_unknown_encoding_and_bad_utf8_rejected(self):
        for body, headers in [(b"html", {"content-encoding": "br"}), (b"\xff", {})]:
            with self.assertRaises(Error):
                decode_html(body, headers)

    def test_uncompressed_html_unchanged(self):
        raw = b"<p>Public page</p>"
        self.assertEqual(decode_html(raw, {}), raw)
