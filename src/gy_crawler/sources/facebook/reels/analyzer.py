import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


DEFAULT_URL = "http://localhost:52501/analyze/upload"


def format_markdown(payload):
    formatted = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"```json\n{formatted}\n```\n"


def analyze_file(mp4_path, url=DEFAULT_URL, session=None):
    http = session or requests
    with mp4_path.open("rb") as file_obj:
        response = http.post(url, files={"file": file_obj})
    response.raise_for_status()
    return response.json()


def iter_mp4_files(input_dir):
    return sorted(path for path in Path(input_dir).rglob("*.mp4") if path.is_file())


def process_one(mp4_path, output_dir, upload):
    result_path = output_dir / f"{mp4_path.stem}.md"
    if result_path.exists():
        return "skipped", mp4_path.name, None

    try:
        payload = upload(mp4_path)
    except Exception as exc:  # noqa: BLE001
        return "failed", mp4_path.name, str(exc)

    result_path.write_text(format_markdown(payload), encoding="utf-8")
    return "success", mp4_path.name, None


def process_batch(input_dir, output_dir, uploader=None, workers=1):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    upload = uploader or analyze_file

    mp4_files = iter_mp4_files(input_path)
    summary = {"total": len(mp4_files), "success": 0, "failed": 0, "skipped": 0}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [
            executor.submit(process_one, mp4_path, output_path, upload)
            for mp4_path in mp4_files
        ]
        for future in as_completed(futures):
            status, file_name, error = future.result()
            summary[status] += 1
            if status == "failed":
                print(f"FAILED {file_name}: {error}", file=sys.stderr)

    return summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Analyze downloaded Facebook Reel videos via upload API",
    )
    parser.add_argument(
        "--input-dir",
        default="raw_file_output/fb_reels",
        help="Directory containing .mp4 files (scans recursively)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/facebook/reel_analysis/markdown",
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--url", default=DEFAULT_URL, help="Analysis API endpoint")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    upload = lambda mp4_path: analyze_file(mp4_path, url=args.url)
    summary = process_batch(args.input_dir, args.output_dir, uploader=upload, workers=args.workers)
    print(
        "total={total} success={success} skipped={skipped} failed={failed}".format(
            **summary
        )
    )
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
