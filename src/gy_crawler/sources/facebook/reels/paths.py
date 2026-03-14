import re
from urllib.parse import parse_qs, urlparse


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


def canonicalize_reel_url(reel_url):
    parsed = urlparse(reel_url)
    return f"{parsed.scheme}://{parsed.netloc}/reel/{extract_reel_id(reel_url)}/"


def extract_profile_id(profile_url):
    parsed = urlparse(profile_url)
    query_id = parse_qs(parsed.query).get("id")
    if query_id:
        return query_id[0]

    match = re.search(r"/people/[^/]+/(\d+)/?", parsed.path)
    if match:
        return match.group(1)

    return None
