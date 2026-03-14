import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from gy_crawler.cli import main as cli_main


class MainCliTests(unittest.TestCase):
    def test_main_dispatches_facebook_reels_command(self):
        with mock.patch(
            "gy_crawler.sources.facebook.reels.cli.main",
            return_value=0,
        ) as reels_main:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = cli_main.main(
                    [
                        "crawl",
                        "facebook",
                        "reels",
                        "--profile-url",
                        "https://example.com/reels",
                    ]
                )

        self.assertEqual(exit_code, 0)
        reels_main.assert_called_once_with(
            ["--profile-url", "https://example.com/reels"]
        )


if __name__ == "__main__":
    unittest.main()
