"""Download Facebook Reel videos via yt-dlp."""

import json
import tempfile
from http.cookiejar import MozillaCookieJar
from pathlib import Path

import yt_dlp


def _playwright_state_to_cookiefile(storage_state_path):
    """Convert Playwright storage-state JSON to a Netscape cookie file.

    Returns the path to a temporary cookie file.
    """
    data = json.loads(Path(storage_state_path).read_text(encoding="utf-8"))
    cookies = data.get("cookies", [])
    if not cookies:
        raise ValueError(f"No cookies found in {storage_state_path}")

    jar = MozillaCookieJar()
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix="yt_dlp_cookies_", delete=False,
    )
    # Write Netscape cookie header + each cookie line
    tmp.write("# Netscape HTTP Cookie File\n")
    for c in cookies:
        domain = c.get("domain", "")
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        raw_expires = c.get("expires", 0)
        expires = str(max(int(raw_expires), 0))
        name = c.get("name", "")
        value = c.get("value", "")
        tmp.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
    tmp.flush()
    tmp.close()
    return tmp.name


def download_reel(reel_url, output_dir, reel_id, cookies_from_browser=None, storage_state=None):
    """Download a single reel video.

    Args:
        reel_url: Facebook reel URL.
        output_dir: Directory to save the video.
        reel_id: Reel ID used for the filename.
        cookies_from_browser: Browser name for yt-dlp cookie extraction (e.g. "chrome").
        storage_state: Path to Playwright storage-state JSON for cookie auth.

    Returns the downloaded file path on success, or None on failure.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(output_dir / f"{reel_id}.%(ext)s")

    ydl_opts = {
        "format": "best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "sleep_interval": 1,
    }

    cookie_file = None
    if storage_state:
        cookie_file = _playwright_state_to_cookiefile(storage_state)
        ydl_opts["cookiefile"] = cookie_file
    elif cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(reel_url, download=True)
            if info is None:
                return None
            ext = info.get("ext", "mp4")
            downloaded = output_dir / f"{reel_id}.{ext}"
            if downloaded.exists():
                return downloaded
    finally:
        if cookie_file:
            Path(cookie_file).unlink(missing_ok=True)

    return None
