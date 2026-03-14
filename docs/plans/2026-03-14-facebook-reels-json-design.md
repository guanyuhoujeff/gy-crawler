# Facebook Reels JSON Export Design

## Goal

Build a reusable script that opens a Facebook profile's reels tab with Playwright, collects a limited set of visible reel links, visits each reel page, extracts at least the reel URL and publish time, and writes one JSON file per reel into an account-specific output directory.

## Scope

- Input: a Facebook profile reels URL and a reel limit
- Collection: visible reels from the currently loaded reels tab
- Detail extraction: per-reel publish time plus any other stable metadata available on the page
- Output: one JSON file per reel under an account-derived directory
- First validation target: `https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab`

## Recommended Approach

Use Playwright end-to-end for both collection and per-reel extraction.

Why this approach:
- It matches the path already proven to work in this session.
- It tolerates Facebook's client-side rendering better than plain HTTP scraping.
- It is easier to verify and debug because selectors, page text, and fallback parsing can all be observed from a real browser context.

Rejected alternatives:
- Direct HTML or embedded JSON scraping from raw HTTP responses is more brittle against Facebook markup changes.
- A mixed Playwright + raw HTTP design adds complexity without clear reliability gains for the first version.

## Data Model

Each reel is written as `<reel_id>.json`.

Minimum fields:

```json
{
  "account_name": "SubudhiIsha1",
  "account_slug": "subudhiisha1",
  "source_profile_url": "https://www.facebook.com/people/SubudhiIsha1/100070097403579/?sk=reels_tab",
  "reel_url": "https://www.facebook.com/reel/795067433657541/?s=fb_shorts_profile&stack_idx=0",
  "reel_id": "795067433657541",
  "published_time": "May 5, 2025 at 10:30 PM",
  "published_time_iso": "2025-05-05T22:30:00+00:00",
  "caption": "optional",
  "view_count_visible": "19K",
  "collected_at": "2026-03-14T05:31:54Z",
  "collector": {
    "name": "facebook_reels_export",
    "version": 1
  },
  "warnings": []
}
```

If a field cannot be extracted reliably, it should still be present with `null` where appropriate, plus a warning describing the missing value.

## Output Layout

The script creates an account-specific output directory using:

- Prefix: `facebook_`
- Body: normalized account name
- Normalization: lowercase, remove or collapse non-alphanumeric characters to underscores, trim redundant underscores

Example:
- Account name: `SubudhiIsha1`
- Output directory: `facebook_subudhiisha1`

## Extraction Strategy

### Profile Page

1. Navigate to the profile reels URL.
2. Wait for the page to stabilize.
3. Collect currently visible anchor tags whose `href` contains `/reel/`.
4. Deduplicate by absolute reel URL.
5. Capture any visible counter text associated with each reel card.
6. Read the visible account name from the profile page to derive the output directory.

### Reel Detail Page

For each reel URL:

1. Open the reel page in the same browser context.
2. Attempt publish-time extraction in this order:
   - Visible `time` element `datetime`
   - Visible time text
   - Structured data such as JSON-LD
   - Embedded script content containing timestamp-like metadata
3. Attempt to extract caption text when visible and not obviously UI chrome.
4. Derive `reel_id` from the reel URL.
5. Emit warnings for any missing fields.

## Error Handling

- If the profile page yields no visible reel URLs, exit non-zero.
- If a single reel fails to load or parse, continue processing the rest and record the error in that reel's output only if a partial record is still possible; otherwise count it as failed and move on.
- The script prints a final summary with totals for discovered, written, and failed reels.
- Selector failures must identify whether they happened during profile collection or reel detail extraction.

## Testing Strategy

Unit tests should cover:
- account directory name normalization
- reel ID extraction from URLs
- parsing publish time from small HTML snippets or metadata blobs
- JSON payload assembly and warning behavior

Integration verification should cover:
- running the script against the provided Facebook reels page with `--limit 10`
- confirming output files land in the derived directory
- confirming each JSON contains `reel_url`
- confirming publish time is populated when available and `null` plus warnings otherwise

## Constraints And Assumptions

- Facebook may display a login dialog; the script should avoid depending on logged-in state and work with publicly visible content only.
- The first version targets currently visible reels and does not auto-scroll for pagination.
- The first version is a CLI script, not a library package.

## Implementation Note

This workspace is currently an untracked subdirectory inside the parent git repository, so this design document is written locally but not committed to avoid accidentally committing unrelated parent-level content.
