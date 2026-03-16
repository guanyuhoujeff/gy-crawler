"""Download reel videos from already-exported JSON metadata files.

Usage:
    python scripts/download_reels.py output/facebook_imoneytalk --storage-state .secrets/facebook-state.json
    python scripts/download_reels.py output/facebook_imoneytalk --cookies-from-browser firefox
    python scripts/download_reels.py output  # scans all subdirectories
"""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _bootstrap import ensure_repo_src_on_path

ensure_repo_src_on_path()

import argparse
import json

from gy_crawler.sources.facebook.reels.downloader import download_reel


def find_reel_jsons(directory):
    """Yield (json_path, content_id, reel_url) from all reel JSON files."""
    directory = Path(directory)
    for json_path in sorted(directory.rglob("*.json")):
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("content_type") != "reel":
            continue
        reel_url = data.get("canonical_url") or data.get("source_url")
        content_id = data.get("content_id")
        if reel_url and content_id:
            yield json_path, content_id, reel_url


def already_downloaded(json_path, content_id):
    """Check if a video file already exists next to the JSON."""
    parent = json_path.parent
    return any(parent.glob(f"{content_id}.*")) and not all(
        p.suffix == ".json" for p in parent.glob(f"{content_id}.*")
    )


def main():
    parser = argparse.ArgumentParser(
        description="Download reel videos from existing JSON metadata",
    )
    parser.add_argument(
        "directory",
        help="Path to output directory (e.g. output/facebook_imoneytalk or output/)",
    )
    parser.add_argument(
        "--storage-state",
        help="Path to Playwright storage-state JSON for cookie auth (e.g. .secrets/facebook-state.json)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to extract cookies from for yt-dlp (e.g. chrome, firefox)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip reels that already have a video file (default: true)",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Re-download even if video file already exists",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Directory not found: {directory}", file=sys.stderr)
        return 1

    reels = list(find_reel_jsons(directory))
    if not reels:
        print(f"No reel JSON files found in {directory}", file=sys.stderr)
        return 1

    downloaded = 0
    skipped = 0
    failed = 0

    for json_path, content_id, reel_url in reels:
        output_dir = json_path.parent

        if args.skip_existing and already_downloaded(json_path, content_id):
            skipped += 1
            continue

        print(f"[{downloaded + failed + 1}/{len(reels)}] {content_id} ...", end=" ", flush=True)
        try:
            result = download_reel(
                reel_url=reel_url,
                output_dir=output_dir,
                reel_id=content_id,
                cookies_from_browser=args.cookies_from_browser,
                storage_state=args.storage_state,
            )
            if result:
                downloaded += 1
                print(f"OK ({result.name})")
            else:
                failed += 1
                print("FAILED (no file)")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAILED ({exc})")

    print(f"\ntotal={len(reels)} downloaded={downloaded} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
