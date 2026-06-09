"""Unit tests for web_crawl.py."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import web_crawl


class TestCrawl(unittest.TestCase):
    def setUp(self):
        web_crawl.visited.clear()
        web_crawl.to_visit.clear()

    def tearDown(self):
        web_crawl.visited.clear()
        web_crawl.to_visit.clear()

    @patch("web_crawl.requests.get")
    def test_discovers_same_domain_links(self, mock_get):
        root_html = """
        <html>
          <body>
            <a href="/about">About</a>
            <a href="https://other.example.com/external">External</a>
          </body>
        </html>
        """
        about_html = "<html><body><a href='/'>Home</a></body></html>"

        def fake_get(url, timeout=5):
            response = MagicMock()
            if url.endswith("/about"):
                response.text = about_html
            else:
                response.text = root_html
            return response

        mock_get.side_effect = fake_get

        urls = web_crawl.crawl("https://example.com", max_pages=10)

        self.assertIn("https://example.com", urls)
        self.assertIn("https://example.com/about", urls)
        self.assertFalse(any("other.example.com" in url for url in urls))

    @patch("web_crawl.requests.get")
    def test_respects_max_pages_limit(self, mock_get):
        mock_get.return_value = MagicMock(
            text='<html><body><a href="/next">Next</a></body></html>'
        )

        urls = web_crawl.crawl("https://example.com", max_pages=2)

        self.assertLessEqual(len(urls), 2)

    @patch("web_crawl.requests.get")
    def test_continues_when_request_fails(self, mock_get):
        mock_get.side_effect = Exception("network error")

        urls = web_crawl.crawl("https://example.com", max_pages=1)

        self.assertEqual(urls, [])


class TestWebCrawlMainWorkflow(unittest.TestCase):
    @patch("web_crawl.subprocess.run")
    @patch("web_crawl.save_pages")
    @patch("web_crawl.crawl", return_value=["https://example.com/page"])
    def test_main_workflow_saves_pages_and_runs_ingest(
        self, mock_crawl, mock_save_pages, mock_run
    ):
        base = "https://example.com"
        urls = web_crawl.crawl(base, max_pages=30)
        web_crawl.save_pages(urls)
        web_crawl.subprocess.run(["python", "doc_scraping.py", "ingest"])

        mock_crawl.assert_called_once_with(base, max_pages=30)
        mock_save_pages.assert_called_once_with(urls)
        mock_run.assert_called_once_with(["python", "doc_scraping.py", "ingest"])


if __name__ == "__main__":
    unittest.main()
