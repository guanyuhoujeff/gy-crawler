import re


def normalize_name_fragment(value):
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return slug.strip("_") or "unknown"


def build_account_directory_name(account_name):
    return f"facebook_{normalize_name_fragment(account_name)}"


def extract_reel_id(reel_url):
    match = re.search(r"/reel/(\d+)", reel_url)
    if not match:
        raise ValueError(f"Could not extract reel id from URL: {reel_url}")
    return match.group(1)
