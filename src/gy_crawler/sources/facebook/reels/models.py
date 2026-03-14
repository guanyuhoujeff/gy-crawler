from datetime import datetime, timezone

from .paths import (
    canonicalize_reel_url,
    extract_profile_id,
    extract_reel_id,
    normalize_name_fragment,
)


def current_timestamp():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_reel_payload(
    account_name,
    source_profile_url,
    reel_url,
    view_count_visible,
    detail,
    collected_at=None,
):
    warnings = list(detail.get("warnings", []))
    if not detail.get("published_time") and not detail.get("published_time_iso"):
        warnings.append("Missing published time")

    account_slug = normalize_name_fragment(account_name)
    return {
        "platform": "facebook",
        "content_type": "reel",
        "content_id": extract_reel_id(reel_url),
        "source_url": reel_url,
        "canonical_url": canonicalize_reel_url(reel_url),
        "author_name": account_name,
        "author_id": extract_profile_id(source_profile_url),
        "author_handle": account_slug,
        "title": detail.get("title"),
        "description": detail.get("caption"),
        "published_time": detail.get("published_time"),
        "published_time_iso": detail.get("published_time_iso"),
        "view_count_visible": view_count_visible,
        "collected_at": collected_at or current_timestamp(),
        "collector": {"name": "facebook_reels_export", "version": 1},
        "platform_metadata": {
            "source_profile_url": source_profile_url,
            "account_slug": account_slug,
            "warnings": warnings,
        },
    }
