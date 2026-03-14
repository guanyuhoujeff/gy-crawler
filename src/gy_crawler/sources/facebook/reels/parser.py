import json
import re
from datetime import datetime, timezone
from html import unescape


def normalize_iso_datetime(value):
    if not value:
        return None

    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    elif re.search(r"[+-]\d{4}$", candidate):
        candidate = f"{candidate[:-2]}:{candidate[-2:]}"

    try:
        return datetime.fromisoformat(candidate).isoformat()
    except ValueError:
        return None


def _strip_tags(value):
    text = re.sub(r"<[^>]+>", "", value)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _find_first_nested_value(payload, keys):
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in payload.values():
            found = _find_first_nested_value(value, keys)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_first_nested_value(item, keys)
            if found:
                return found
    return None


def _format_unix_timestamp(timestamp_value):
    dt = datetime.fromtimestamp(int(timestamp_value), tz=timezone.utc)
    return {
        "published_time": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "published_time_iso": dt.isoformat(),
    }


def extract_publish_time_from_html(html, reel_id=None):
    time_match = re.search(
        r"<time[^>]*datetime=[\"']([^\"']+)[\"'][^>]*>(.*?)</time>",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if time_match:
        raw_iso = unescape(time_match.group(1)).strip()
        text = _strip_tags(time_match.group(2)) or raw_iso
        return {
            "published_time": text,
            "published_time_iso": normalize_iso_datetime(raw_iso),
        }

    script_matches = re.findall(
        r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    for script_body in script_matches:
        try:
            payload = json.loads(unescape(script_body).strip())
        except json.JSONDecodeError:
            continue
        raw_value = _find_first_nested_value(
            payload,
            ("uploadDate", "datePublished", "dateCreated"),
        )
        if raw_value:
            return {
                "published_time": raw_value,
                "published_time_iso": normalize_iso_datetime(raw_value),
            }

    if reel_id:
        reel_id_pattern = re.escape(str(reel_id))
        story_patterns = [
            rf"story_fbid.{{0,120}}?{reel_id_pattern}",
            rf"post_id.{{0,120}}?{reel_id_pattern}",
            reel_id_pattern,
        ]
        for story_pattern in story_patterns:
            for match in re.finditer(story_pattern, html, flags=re.IGNORECASE | re.DOTALL):
                window_start = max(0, match.start() - 500)
                window_end = min(len(html), match.end() + 500)
                window = html[window_start:window_end]
                timestamp_match = re.search(
                    r"(?:publish_time|creation_time)\\?\":(\d{10,13})",
                    window,
                    re.IGNORECASE,
                )
                if timestamp_match:
                    return _format_unix_timestamp(timestamp_match.group(1))

    return {"published_time": None, "published_time_iso": None}


def extract_caption_from_html(html):
    meta_match = re.search(
        r"<meta[^>]+property=[\"']og:description[\"'][^>]+content=[\"']([^\"']*)[\"']",
        html,
        re.IGNORECASE,
    )
    if meta_match:
        content = unescape(meta_match.group(1)).strip()
        if content:
            return content

    script_matches = re.findall(
        r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    for script_body in script_matches:
        try:
            payload = json.loads(unescape(script_body).strip())
        except json.JSONDecodeError:
            continue
        description = _find_first_nested_value(payload, ("description", "caption"))
        if description:
            return description

    return None
