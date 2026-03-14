from datetime import datetime, timezone

from .paths import extract_reel_id, normalize_name_fragment


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

    return {
        "account_name": account_name,
        "account_slug": normalize_name_fragment(account_name),
        "source_profile_url": source_profile_url,
        "reel_url": reel_url,
        "reel_id": extract_reel_id(reel_url),
        "published_time": detail.get("published_time"),
        "published_time_iso": detail.get("published_time_iso"),
        "caption": detail.get("caption"),
        "view_count_visible": view_count_visible,
        "collected_at": collected_at or current_timestamp(),
        "collector": {"name": "facebook_reels_export", "version": 1},
        "warnings": warnings,
    }
