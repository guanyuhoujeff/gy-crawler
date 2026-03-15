import json
import types
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gy_crawler.sources.facebook.reels import cli, collector, parser, paths


class NormalizeAccountDirTests(unittest.TestCase):
    def test_build_account_directory_name_normalizes_visible_account_name(self):
        self.assertEqual(
            paths.build_account_directory_name("Subudhi Isha-1"),
            "facebook_subudhi_isha_1",
        )


class ReelIdTests(unittest.TestCase):
    def test_extract_reel_id_returns_numeric_segment(self):
        url = "https://www.facebook.com/reel/795067433657541/?s=fb_shorts_profile&stack_idx=0"
        self.assertEqual(paths.extract_reel_id(url), "795067433657541")

    def test_canonicalize_reel_url_strips_query_string(self):
        url = "https://www.facebook.com/reel/795067433657541/?s=fb_shorts_profile&stack_idx=0"
        self.assertEqual(
            paths.canonicalize_reel_url(url),
            "https://www.facebook.com/reel/795067433657541/",
        )

    def test_extract_profile_id_reads_numeric_id_from_profile_url(self):
        profile_url = "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab"
        self.assertEqual(paths.extract_profile_id(profile_url), "100070097403579")


class PublishTimeExtractionTests(unittest.TestCase):
    def test_extract_publish_time_prefers_time_datetime_value(self):
        html = '<time datetime="2025-05-05T22:30:00+0000">May 5, 2025 at 10:30 PM</time>'

        result = parser.extract_publish_time_from_html(html)

        self.assertEqual(result["published_time"], "May 5, 2025 at 10:30 PM")
        self.assertEqual(result["published_time_iso"], "2025-05-05T22:30:00+00:00")

    def test_extract_publish_time_falls_back_to_json_ld(self):
        html = """
        <html>
          <head>
            <script type="application/ld+json">
              {"@context":"https://schema.org","uploadDate":"2024-12-31T08:00:00Z"}
            </script>
          </head>
        </html>
        """

        result = parser.extract_publish_time_from_html(html)

        self.assertEqual(result["published_time"], "2024-12-31T08:00:00Z")
        self.assertEqual(result["published_time_iso"], "2024-12-31T08:00:00+00:00")

    def test_extract_publish_time_falls_back_to_embedded_unix_timestamp_for_matching_reel(self):
        html = """
        <script>
        {"publish_time":1773418978,"story_name":"EntVideoCreationStory","story_fbid":["795067433657541"]}
        </script>
        """

        result = parser.extract_publish_time_from_html(html, reel_id="795067433657541")

        self.assertEqual(result["published_time"], "2026-03-13 16:22:58 UTC")
        self.assertEqual(result["published_time_iso"], "2026-03-13T16:22:58+00:00")


class ReelPayloadTests(unittest.TestCase):
    def test_build_reel_payload_uses_social_video_record_shape(self):
        payload = cli.build_reel_payload(
            account_name="SubudhiIsha1",
            source_profile_url="https://example.com/profile",
            reel_url="https://www.facebook.com/reel/795067433657541/",
            view_count_visible="19K",
            detail={"published_time": None, "published_time_iso": None, "caption": None},
            collected_at="2026-03-14T06:00:00Z",
        )

        self.assertEqual(payload["platform"], "facebook")
        self.assertEqual(payload["content_type"], "reel")
        self.assertEqual(payload["content_id"], "795067433657541")
        self.assertEqual(payload["source_url"], "https://www.facebook.com/reel/795067433657541/")
        self.assertEqual(
            payload["canonical_url"],
            "https://www.facebook.com/reel/795067433657541/",
        )
        self.assertEqual(payload["author_name"], "SubudhiIsha1")
        self.assertEqual(payload["author_handle"], "subudhiisha1")
        self.assertIsNone(payload["title"])
        self.assertIsNone(payload["description"])
        self.assertEqual(payload["view_count_visible"], "19K")
        self.assertIn(
            "missing published time",
            payload["platform_metadata"]["warnings"][0].lower(),
        )
        self.assertEqual(payload["platform_metadata"]["account_slug"], "subudhiisha1")


class FakePageMouse:
    def __init__(self, page):
        self.page = page

    def wheel(self, delta_x, delta_y):
        self.page.scroll_round += 1


class FakePage:
    def __init__(self, payload_rounds):
        self.payload_rounds = payload_rounds
        self.scroll_round = 0
        self.wait_calls = 0
        self.mouse = FakePageMouse(self)

    def evaluate(self, script, limit=None):
        if script == collector.VISIBLE_REELS_SCRIPT:
            round_index = min(self.scroll_round, len(self.payload_rounds) - 1)
            return self.payload_rounds[round_index][:limit]
        return None

    def wait_for_timeout(self, timeout_ms):
        self.wait_calls += 1


class VisibleReelCollectionTests(unittest.TestCase):
    def test_collect_visible_reels_deduplicates_urls_and_keeps_visible_counts(self):
        page = FakePage(
            [[
                {"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"},
                {"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"},
                {"href": "https://www.facebook.com/reel/814700504289989/", "text": "15K"},
            ]]
        )

        result = cli.collect_visible_reels(page, limit=10, scroll=False)

        self.assertEqual(
            result,
            [
                {
                    "reel_url": "https://www.facebook.com/reel/795067433657541/",
                    "view_count_visible": "19K",
                },
                {
                    "reel_url": "https://www.facebook.com/reel/814700504289989/",
                    "view_count_visible": "15K",
                },
            ],
        )

    def test_collect_visible_reels_scrolls_until_limit_is_reached(self):
        page = FakePage(
            [
                [{"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"}],
                [
                    {"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"},
                    {"href": "https://www.facebook.com/reel/814700504289989/", "text": "15K"},
                ],
                [
                    {"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"},
                    {"href": "https://www.facebook.com/reel/814700504289989/", "text": "15K"},
                    {"href": "https://www.facebook.com/reel/1242954067485245/", "text": "12K"},
                ],
            ]
        )

        result = cli.collect_visible_reels(
            page,
            limit=3,
            scroll=True,
            max_scrolls=5,
            max_idle_scrolls=2,
        )

        self.assertEqual(
            result,
            [
                {
                    "reel_url": "https://www.facebook.com/reel/795067433657541/",
                    "view_count_visible": "19K",
                },
                {
                    "reel_url": "https://www.facebook.com/reel/814700504289989/",
                    "view_count_visible": "15K",
                },
                {
                    "reel_url": "https://www.facebook.com/reel/1242954067485245/",
                    "view_count_visible": "12K",
                },
            ],
        )
        self.assertEqual(page.scroll_round, 2)

    def test_collect_visible_reels_stops_after_idle_scrolls(self):
        page = FakePage(
            [
                [{"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"}],
                [{"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"}],
                [{"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"}],
                [{"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"}],
            ]
        )

        result = cli.collect_visible_reels(
            page,
            limit=3,
            scroll=True,
            max_scrolls=10,
            max_idle_scrolls=2,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(page.scroll_round, 2)


class FakeCollector:
    def collect_profile(
        self,
        profile_url,
        limit,
        scroll=True,
        max_scrolls=10,
        max_idle_scrolls=2,
    ):
        return {
            "account_name": "SubudhiIsha1",
            "source_profile_url": profile_url,
            "reels": [
                {
                    "reel_url": "https://www.facebook.com/reel/795067433657541/",
                    "view_count_visible": "19K",
                },
                {
                    "reel_url": "https://www.facebook.com/reel/814700504289989/",
                    "view_count_visible": "15K",
                },
            ],
        }

    def collect_reel_detail(self, reel_url):
        return {
            "published_time": "May 5, 2025 at 10:30 PM",
            "published_time_iso": "2025-05-05T22:30:00+00:00",
            "caption": f"caption for {reel_url}",
        }


class FakeBrowserContext:
    def __init__(self):
        self.closed = False
        self.page = object()

    def new_page(self):
        return self.page

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.closed = False
        self.new_context_calls = []
        self.context = FakeBrowserContext()

    def new_context(self, **kwargs):
        self.new_context_calls.append(kwargs)
        return self.context

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, browser):
        self.browser = browser
        self.launch_calls = []

    def launch(self, **kwargs):
        self.launch_calls.append(kwargs)
        return self.browser


class FakePlaywrightRuntime:
    def __init__(self, chromium):
        self.chromium = chromium
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeSyncPlaywrightFactory:
    def __init__(self, runtime):
        self.runtime = runtime

    def start(self):
        return self.runtime


class AuthenticatedCollectorTests(unittest.TestCase):
    def test_enter_passes_storage_state_to_new_context(self):
        browser = FakeBrowser()
        chromium = FakeChromium(browser)
        runtime = FakePlaywrightRuntime(chromium)
        fake_sync_api = types.SimpleNamespace(
            sync_playwright=lambda: FakeSyncPlaywrightFactory(runtime)
        )

        with mock.patch.dict("sys.modules", {"playwright.sync_api": fake_sync_api}):
            managed = collector.PlaywrightFacebookCollector(
                storage_state_path=".secrets/facebook-state.json"
            )
            try:
                managed.__enter__()
            finally:
                managed.__exit__(None, None, None)

        self.assertEqual(
            browser.new_context_calls,
            [{"storage_state": ".secrets/facebook-state.json"}],
        )


class MainTests(unittest.TestCase):
    def test_main_writes_one_json_per_visible_reel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = FakeCollector()

            exit_code = cli.main(
                [
                    "--profile-url",
                    "https://example.com/reels",
                    "--limit",
                    "2",
                    "--output-root",
                    tmpdir,
                ],
                collector=collector,
                collected_at="2026-03-14T06:00:00Z",
            )

            self.assertEqual(exit_code, 0)
            output_dir = Path(tmpdir) / "facebook_subudhiisha1"
            files = sorted(output_dir.glob("*.json"))
            self.assertEqual(
                [path.name for path in files],
                ["795067433657541.json", "814700504289989.json"],
            )

            payload = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(
                payload["source_url"], "https://www.facebook.com/reel/795067433657541/"
            )
            self.assertEqual(payload["published_time_iso"], "2025-05-05T22:30:00+00:00")

    def test_parse_args_accepts_scroll_controls(self):
        args = cli.parse_args(
            [
                "--profile-url",
                "https://example.com/reels",
                "--limit",
                "20",
                "--no-scroll",
                "--max-scrolls",
                "7",
                "--max-idle-scrolls",
                "3",
            ]
        )

        self.assertEqual(args.limit, 20)
        self.assertFalse(args.scroll)
        self.assertEqual(args.max_scrolls, 7)
        self.assertEqual(args.max_idle_scrolls, 3)


if __name__ == "__main__":
    unittest.main()
