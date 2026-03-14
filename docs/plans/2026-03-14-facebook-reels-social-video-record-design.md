# Facebook Reels SocialVideoRecord And Auto-Scroll Design

## Goal

Upgrade the Facebook Reels crawler so its output is normalized into a reusable `SocialVideoRecord` shape, and add controlled auto-scroll collection so future requests for more reels can load beyond the initially visible grid.

## Scope

- Normalize Facebook reel output into a stable cross-platform model
- Preserve Facebook-specific fields under a platform-specific metadata section
- Add controlled scrolling to collect more reels when `--limit` exceeds the initially visible set
- Keep the current public crawling behavior working

## Chosen Data Model

Use a shared `SocialVideoRecord` plus `platform_metadata`.

This is the balanced option:

- reusable across Facebook and future YouTube support
- avoids overfitting the main schema to Facebook specifics
- still preserves Facebook-only details without losing fidelity

## SocialVideoRecord Shape

The normalized output should follow this structure:

```json
{
  "platform": "facebook",
  "content_type": "reel",
  "content_id": "795067433657541",
  "source_url": "https://www.facebook.com/reel/795067433657541/?s=fb_shorts_profile&stack_idx=0",
  "canonical_url": "https://www.facebook.com/reel/795067433657541/",
  "author_name": "SubudhiIsha1",
  "author_id": "100070097403579",
  "author_handle": "subudhiisha1",
  "title": null,
  "description": "炒股不賺錢，就默念這10句話 #股市",
  "published_time": "2026-03-13 16:22:58 UTC",
  "published_time_iso": "2026-03-13T16:22:58+00:00",
  "view_count_visible": "2.1 萬",
  "collected_at": "2026-03-14T06:12:06Z",
  "collector": {
    "name": "facebook_reels_export",
    "version": 1
  },
  "platform_metadata": {
    "source_profile_url": "https://www.facebook.com/people/SubudhiIsha1/100070097403579/?sk=reels_tab",
    "account_slug": "subudhiisha1",
    "warnings": []
  }
}
```

## Field Rules

### Shared Fields

- `platform`: fixed as `facebook`
- `content_type`: fixed as `reel`
- `content_id`: numeric reel id
- `source_url`: original discovered reel URL
- `canonical_url`: normalized reel URL without transient query parameters when possible
- `author_name`: profile display name
- `author_id`: Facebook numeric profile id when known
- `author_handle`: normalized profile name for now
- `title`: `null` in the current Facebook path unless a stable title field is found
- `description`: caption text
- `published_time`: human-readable value
- `published_time_iso`: normalized ISO timestamp
- `view_count_visible`: currently visible value as scraped
- `collected_at`: collection timestamp
- `collector`: collector metadata

### Platform Metadata

Facebook-specific fields should move under `platform_metadata`, such as:

- `source_profile_url`
- `account_slug`
- `warnings`
- future fields such as reactions or privacy labels

## Auto-Scroll Strategy

Use a target-count-driven scrolling loop with idle detection.

This is preferred over fixed scroll counts because:

- users ask for a target number of reels, not a number of page movements
- Facebook lazy loading is variable
- fixed counts are too brittle across accounts

## Scroll Behavior

Add collection options:

- `limit`: target number of reels to collect
- `scroll`: whether scrolling is enabled
- `max_scrolls`: absolute upper bound on scroll attempts
- `max_idle_scrolls`: consecutive scrolls allowed without discovering new reel URLs

Behavior:

1. collect currently loaded reel URLs
2. if count is already at least `limit`, stop
3. if scrolling is disabled, stop
4. scroll down once
5. wait for content to settle
6. collect again and deduplicate by canonical reel URL
7. if new reels were found, reset idle counter
8. if no new reels were found, increment idle counter
9. stop when:
   - `limit` reached
   - `max_scrolls` reached
   - `max_idle_scrolls` reached

## Collection Semantics

The crawler should collect all reel links loaded into the DOM, not only links inside the current viewport. This makes scrolling additive and more reliable because already-loaded links remain discoverable even after the viewport changes.

Deduplication key:

- canonical reel URL when derivable
- otherwise the extracted reel id

## Error Handling

- If profile collection yields zero reels after the full scroll strategy, return a profile-level failure
- If detail extraction fails for one reel, continue and emit warnings in `platform_metadata`
- If scrolling stops because of idle detection, surface that reason in summary logs

## Testing Strategy

Unit tests should cover:

- `SocialVideoRecord` field mapping
- canonical URL normalization
- author metadata extraction rules
- scrolling loop stop conditions
- deduplication behavior across multiple collection rounds

Integration verification should cover:

- collecting more than the initially visible reel count
- confirming that increasing `--limit` causes scrolling
- confirming that outputs follow the new normalized schema

## File Impact

Likely files to change:

- `src/gy_crawler/sources/facebook/reels/cli.py`
- `src/gy_crawler/sources/facebook/reels/collector.py`
- `src/gy_crawler/sources/facebook/reels/models.py`
- `src/gy_crawler/sources/facebook/reels/paths.py`
- possibly `src/gy_crawler/models/` for a shared record helper
- `tests/unit/facebook/test_reels_cli.py`

## Constraints

- Avoid overbuilding a global multi-platform model layer beyond what Facebook and likely YouTube need immediately
- Preserve backward crawl reliability while changing output shape
- Keep scroll logic bounded to avoid hanging on unstable Facebook pages
