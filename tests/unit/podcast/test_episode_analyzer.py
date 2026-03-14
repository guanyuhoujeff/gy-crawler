import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gy_crawler.sources.podcast.episodes import analyzer
from gy_crawler.sources.podcast.feeds import downloader


class PodcastDownloaderHelperTests(unittest.TestCase):
    def test_safe_filename_replaces_invalid_characters(self):
        self.assertEqual(
            downloader.safe_filename('a/b:c*podcast?"<>|'),
            "a_b_c_podcast_____",
        )

    def test_guess_extension_defaults_to_mp3_for_unknown_urls(self):
        self.assertEqual(downloader.guess_extension("https://example.com/audio"), ".mp3")


class FormatMarkdownTests(unittest.TestCase):
    def test_format_markdown_wraps_raw_json_in_fenced_block(self):
        payload = {"title": "測試", "score": 0.75, "tags": ["a", "b"]}

        result = analyzer.format_markdown(payload)

        expected_json = json.dumps(payload, ensure_ascii=False, indent=2)
        self.assertEqual(result, f"```json\n{expected_json}\n```\n")


class ProcessBatchTests(unittest.TestCase):
    def test_process_batch_skips_existing_results_and_continues_after_failures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_dir = tmp_path / "mp3"
            output_dir = tmp_path / "result"
            input_dir.mkdir()
            output_dir.mkdir()

            first = input_dir / "001_test.mp3"
            second = input_dir / "002_test.mp3"
            third = input_dir / "003_test.mp3"
            for path in (first, second, third):
                path.write_bytes(b"fake mp3 content")

            existing_output = output_dir / "001_test.mp3.md"
            existing_output.write_text("existing", encoding="utf-8")

            calls = []

            def fake_uploader(path):
                calls.append(path.name)
                if path.name == "002_test.mp3":
                    raise RuntimeError("boom")
                return {"file": path.name}

            summary = analyzer.process_batch(
                input_dir=input_dir,
                output_dir=output_dir,
                uploader=fake_uploader,
            )

            self.assertEqual(summary["total"], 3)
            self.assertEqual(summary["skipped"], 1)
            self.assertEqual(summary["success"], 1)
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(calls, ["002_test.mp3", "003_test.mp3"])
            self.assertEqual(existing_output.read_text(encoding="utf-8"), "existing")
            self.assertFalse((output_dir / "002_test.mp3.md").exists())
            self.assertEqual(
                (output_dir / "003_test.mp3.md").read_text(encoding="utf-8"),
                "```json\n{\n  \"file\": \"003_test.mp3\"\n}\n```\n",
            )

    def test_process_batch_supports_multiple_workers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_dir = tmp_path / "mp3"
            output_dir = tmp_path / "result"
            input_dir.mkdir()
            output_dir.mkdir()

            for index in range(4):
                (input_dir / f"{index:03d}_test.mp3").write_bytes(b"fake mp3 content")

            calls = []

            def fake_uploader(path):
                calls.append(path.name)
                return {"file": path.name}

            summary = analyzer.process_batch(
                input_dir=input_dir,
                output_dir=output_dir,
                uploader=fake_uploader,
                workers=2,
            )

            self.assertEqual(summary["total"], 4)
            self.assertEqual(summary["success"], 4)
            self.assertEqual(summary["failed"], 0)
            self.assertEqual(summary["skipped"], 0)
            self.assertEqual(sorted(calls), [f"{index:03d}_test.mp3" for index in range(4)])
            self.assertEqual(len(list(output_dir.glob("*.md"))), 4)


class MainTests(unittest.TestCase):
    def test_main_accepts_explicit_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            input_dir = tmp_path / "mp3"
            output_dir = tmp_path / "result"
            input_dir.mkdir()
            (input_dir / "001_test.mp3").write_bytes(b"fake mp3 content")

            with mock.patch.object(analyzer, "analyze_file", return_value={"ok": True}):
                exit_code = analyzer.main(
                    ["--input-dir", str(input_dir), "--output-dir", str(output_dir)]
                )
                self.assertEqual(exit_code, 0)
                self.assertEqual(
                    (output_dir / "001_test.mp3.md").read_text(encoding="utf-8"),
                    "```json\n{\n  \"ok\": true\n}\n```\n",
                )


if __name__ == "__main__":
    unittest.main()
