import unittest
from unittest.mock import Mock, patch

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from scrape_fanqie_ranks import open_rank_page


class OpenRankPageTests(unittest.TestCase):
    @patch("scrape_fanqie_ranks.time.sleep")
    def test_success_waits_for_book_links_without_retry(self, sleep):
        page = Mock()

        open_rank_page(page, "https://fanqienovel.com/rank/0_1_1139")

        page.goto.assert_called_once_with(
            "https://fanqienovel.com/rank/0_1_1139",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_selector.assert_called_once_with(
            'a[href^="/page/"]', timeout=30000
        )
        sleep.assert_not_called()

    @patch("scrape_fanqie_ranks.time.sleep")
    def test_navigation_timeout_retries_then_succeeds(self, sleep):
        page = Mock()
        page.goto.side_effect = [PlaywrightTimeoutError("navigation timed out"), None]

        open_rank_page(page, "https://fanqienovel.com/rank/0_1_1139")

        self.assertEqual(page.goto.call_count, 2)
        page.wait_for_selector.assert_called_once()
        sleep.assert_called_once_with(5)

    @patch("scrape_fanqie_ranks.time.sleep")
    def test_missing_book_links_retries_then_succeeds(self, sleep):
        page = Mock()
        page.wait_for_selector.side_effect = [
            PlaywrightTimeoutError("book links timed out"), None
        ]

        open_rank_page(page, "https://fanqienovel.com/rank/0_1_1139")

        self.assertEqual(page.goto.call_count, 2)
        self.assertEqual(page.wait_for_selector.call_count, 2)
        sleep.assert_called_once_with(5)

    @patch("scrape_fanqie_ranks.time.sleep")
    def test_persistent_timeout_raises_after_three_attempts(self, sleep):
        page = Mock()
        error = PlaywrightTimeoutError("navigation timed out")
        page.goto.side_effect = error

        with self.assertRaises(PlaywrightTimeoutError) as raised:
            open_rank_page(page, "https://fanqienovel.com/rank/0_1_1139")

        self.assertIs(raised.exception, error)
        self.assertEqual(page.goto.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        page.wait_for_selector.assert_not_called()
