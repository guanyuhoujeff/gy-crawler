import argparse
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _bootstrap import ensure_repo_src_on_path


ensure_repo_src_on_path()

from gy_crawler.sources.podcast.feeds.downloader import download_feed


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--rss-url", required=True)
    parser.add_argument("--output-dir", default="data/raw/podcast/episodes/audio")
    parser.add_argument("--log-file", default="data/tmp/podcast/feed_download_log.csv")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    summary = download_feed(
        rss_url=args.rss_url,
        output_dir=Path(args.output_dir),
        log_file=Path(args.log_file) if args.log_file else None,
    )
    print(
        "total={total} success={success} skipped={skipped} failed={failed}".format(
            **summary,
        )
    )
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
