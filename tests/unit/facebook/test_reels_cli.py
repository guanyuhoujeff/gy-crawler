import json
import tempfile
import unittest
from pathlib import Path

from gy_crawler.sources.facebook.reels import cli, parser, paths


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
    def test_build_reel_payload_preserves_required_fields_and_warnings(self):
        payload = cli.build_reel_payload(
            account_name="SubudhiIsha1",
            source_profile_url="https://example.com/profile",
            reel_url="https://www.facebook.com/reel/795067433657541/",
            view_count_visible="19K",
            detail={"published_time": None, "published_time_iso": None, "caption": None},
            collected_at="2026-03-14T06:00:00Z",
        )

        self.assertEqual(payload["reel_id"], "795067433657541")
        self.assertEqual(payload["account_slug"], "subudhiisha1")
        self.assertEqual(payload["view_count_visible"], "19K")
        self.assertIn("missing published time", payload["warnings"][0].lower())


class FakePage:
    def __init__(self, payload):
        self.payload = payload

    def evaluate(self, script, limit):
        return self.payload[:limit]


class VisibleReelCollectionTests(unittest.TestCase):
    def test_collect_visible_reels_deduplicates_urls_and_keeps_visible_counts(self):
        page = FakePage(
            [
                {"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"},
                {"href": "https://www.facebook.com/reel/795067433657541/", "text": "19K"},
                {"href": "https://www.facebook.com/reel/814700504289989/", "text": "15K"},
            ]
        )

        result = cli.collect_visible_reels(page, limit=10)

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


class FakeCollector:
    def collect_profile(self, profile_url, limit):
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
                payload["reel_url"], "https://www.facebook.com/reel/795067433657541/"
            )
            self.assertEqual(payload["published_time_iso"], "2025-05-05T22:30:00+00:00")


if __name__ == "__main__":
    unittest.main()
