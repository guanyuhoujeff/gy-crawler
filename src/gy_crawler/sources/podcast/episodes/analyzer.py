import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
from pathlib import Path

import requests


DEFAULT_URL = "http://localhost:52501/analyze/upload"


def format_markdown(payload):
    formatted = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"```json\n{formatted}\n```\n"


def analyze_file(mp3_path, url=DEFAULT_URL, session=None):
    http = session or requests
    with mp3_path.open("rb") as file_obj:
        response = http.post(url, files={"file": file_obj})
    response.raise_for_status()
    return response.json()


def iter_mp3_files(input_dir):
    return sorted(path for path in Path(input_dir).glob("*.mp3") if path.is_file())


def process_one(mp3_path, output_path, upload):
    result_path = output_path / f"{mp3_path.name}.md"
    if result_path.exists():
        return "skipped", mp3_path.name, None

    try:
        payload = upload(mp3_path)
    except Exception as exc:  # noqa: BLE001
        return "failed", mp3_path.name, str(exc)

    result_path.write_text(format_markdown(payload), encoding="utf-8")
    return "success", mp3_path.name, None


def process_batch(input_dir, output_dir, uploader=None, workers=1):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    upload = uploader or analyze_file

    summary = {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    mp3_files = iter_mp3_files(input_path)
    summary["total"] = len(mp3_files)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [
            executor.submit(process_one, mp3_path, output_path, upload)
            for mp3_path in mp3_files
        ]
        for future in as_completed(futures):
            status, file_name, error = future.result()
            summary[status] += 1
            if status == "failed":
                print(f"FAILED {file_name}: {error}", file=sys.stderr)

    return summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="raw_file_output/podcast")
    parser.add_argument(
        "--output-dir",
        default="data/processed/podcast/episode_analysis/markdown",
    )
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    summary = process_batch(args.input_dir, args.output_dir, workers=args.workers)
    print(
        "total={total} success={success} skipped={skipped} failed={failed}".format(
            **summary
        )
    )
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
