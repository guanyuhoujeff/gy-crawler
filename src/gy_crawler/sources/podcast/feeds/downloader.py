import csv
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


DEFAULT_TIMEOUT = 60
DEFAULT_SLEEP_BETWEEN_DOWNLOADS = 1.0


def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180]


def get_audio_url(entry) -> str | None:
    enclosures = entry.get("enclosures", [])
    for enc in enclosures:
        href = enc.get("href")
        if href:
            return href

    links = entry.get("links", [])
    for link in links:
        href = link.get("href")
        link_type = link.get("type", "")
        if href and "audio" in link_type:
            return href

    return None


def guess_extension(audio_url: str) -> str:
    path = urlparse(audio_url).path.lower()
    if path.endswith(".mp3"):
        return ".mp3"
    if path.endswith(".m4a"):
        return ".m4a"
    if path.endswith(".aac"):
        return ".aac"
    return ".mp3"


def short_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


def download_file(url: str, output_path: Path, timeout=DEFAULT_TIMEOUT) -> None:
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with output_path.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024 * 64):
                if chunk:
                    file_obj.write(chunk)


def init_log(output_dir: Path, log_file: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    if not log_file.exists():
        with log_file.open("w", newline="", encoding="utf-8-sig") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow(
                ["index", "title", "published", "audio_url", "filename", "status", "error"]
            )


def append_log(log_file, index, title, published, audio_url, filename, status, error=""):
    with log_file.open("a", newline="", encoding="utf-8-sig") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow([index, title, published, audio_url, filename, status, error])


def parse_feed(rss_url):
    import feedparser

    return feedparser.parse(rss_url)


def download_feed(
    rss_url,
    output_dir,
    log_file=None,
    timeout=DEFAULT_TIMEOUT,
    sleep_between_downloads=DEFAULT_SLEEP_BETWEEN_DOWNLOADS,
    limit=0,
):
    output_path = Path(output_dir)
    log_path = Path(log_file) if log_file else output_path / "download_log.csv"
    init_log(output_path, log_path)

    feed = parse_feed(rss_url)
    entries = feed.entries
    if limit > 0:
        entries = entries[:limit]
    if not entries:
        return {"success": 0, "skipped": 0, "failed": 0, "total": 0}

    summary = {"success": 0, "skipped": 0, "failed": 0, "total": len(entries)}
    for index, entry in enumerate(entries, start=1):
        title = entry.get("title", f"episode_{index}")
        published = entry.get("published", "") or entry.get("updated", "")
        audio_url = get_audio_url(entry)

        if not audio_url:
            append_log(index=index, title=title, published=published, audio_url="", filename="", status="no_audio_url", error="No audio URL found", log_file=log_path)
            summary["skipped"] += 1
            continue

        filename = safe_filename(
            f"{index:03d}_{title}_{short_hash(audio_url)}{guess_extension(audio_url)}"
        )
        target_path = output_path / filename

        if target_path.exists():
            append_log(log_file=log_path, index=index, title=title, published=published, audio_url=audio_url, filename=filename, status="skipped_exists")
            summary["skipped"] += 1
            continue

        try:
            download_file(audio_url, target_path, timeout=timeout)
            append_log(log_file=log_path, index=index, title=title, published=published, audio_url=audio_url, filename=filename, status="downloaded")
            summary["success"] += 1
        except Exception as exc:  # noqa: BLE001
            append_log(log_file=log_path, index=index, title=title, published=published, audio_url=audio_url, filename=filename, status="failed", error=str(exc))
            summary["failed"] += 1

        time.sleep(sleep_between_downloads)

    return summary
