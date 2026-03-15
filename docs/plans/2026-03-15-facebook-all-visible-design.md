# Facebook Reels All Visible Crawl Design

## Goal

Add an authenticated `--all-visible` crawl mode for the Facebook Reels exporter so an operator can reuse a saved login session and collect as many visible reels from a profile as the Facebook UI exposes through scrolling.

## Scope

- Add an `--all-visible` CLI mode alongside the existing `--limit` mode
- Reuse the saved Playwright storage state from the existing login-session workflow
- Continue scrolling until the reels page stops surfacing new canonical reel URLs
- Preserve the current one-JSON-per-reel output format

## Chosen Approach

Keep the current two-stage export flow:

1. collect unique reel URLs from the profile reels page
2. visit each collected reel URL to extract detail fields and write JSON output

The new behavior only changes how the list-stage stops collecting URLs. The crawler will keep scrolling until it sees no new canonical reel URLs for a configured number of consecutive rounds. This keeps the change local to the profile collection path and avoids unnecessary redesign of detail extraction or output writing.

## Non-Goals

- No claim of guaranteed 100% completeness against all Facebook UI variants
- No new checkpoint or resume workflow in this first version
- No Graph API or token-based data collection
- No automated session refresh or auto-login behavior

## User Experience

### Existing Limited Crawl

The current limited mode remains available:

```bash
python3 scripts/facebook_reels_export.py \
  --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" \
  --storage-state .secrets/facebook-state.json \
  --limit 200 \
  --output-root output
```

### New All Visible Crawl

The new mode removes the reel-count stop condition and crawls until scrolling stops revealing new reel URLs:

```bash
python3 scripts/facebook_reels_export.py \
  --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" \
  --storage-state .secrets/facebook-state.json \
  --all-visible \
  --max-idle-scrolls 5 \
  --delay-seconds 2 \
  --output-root output
```

## CLI Behavior

- Keep `--limit` for count-bounded collection
- Add `--all-visible` for best-effort full visible collection
- Treat `--limit` and `--all-visible` as mutually exclusive
- Preserve current default behavior by defaulting to `--limit 10` when neither is explicitly provided
- Continue exposing `--max-idle-scrolls`, `--max-scrolls`, and `--delay-seconds`

Behavior rules:

- `--limit` mode stops as soon as the requested number of unique reels is collected
- `--all-visible` mode ignores reel count and stops only after repeated idle scroll rounds or a safety cap
- authenticated and unauthenticated paths should both support `--all-visible`

## Collector Behavior

The current collector already deduplicates reel URLs by canonical URL and scrolls until a stop condition is met. The new mode will extend that behavior without changing the detail-extraction stage.

### Limited Mode

Keep the current semantics:

- collect visible reel anchors
- deduplicate by canonical URL
- stop when the reel count reaches `limit`
- stop early if idle scroll rounds or maximum scrolls are hit first

### All Visible Mode

Add a mode that:

- keeps collecting canonical reel URLs after each scroll round
- resets the idle counter whenever a scroll reveals at least one new reel URL
- increments the idle counter when a round reveals zero new reel URLs
- stops when `idle_scrolls >= max_idle_scrolls`
- may also stop at `max_scrolls` if a safety cap is configured

This makes `max_idle_scrolls` the primary stop signal and keeps `max_scrolls` as a protection against pathological infinite-scroll behavior.

## Output Semantics

- Keep one JSON file per reel
- Keep the current directory naming logic
- Keep the current summary output shape

In `--all-visible` mode:

- `discovered` means the total number of unique reels found during the entire scrolling session
- `written` means the number of detail JSON files written
- `failed` continues to count detail extraction failures only

## Error Handling

- If `--limit` and `--all-visible` are both supplied, fail during argument parsing before browser startup
- If `--all-visible` yields no visible reels, keep the current `Profile collection failed: no visible reels found` error
- If authenticated crawling fails because the saved session is missing or expired, preserve the current remediation text pointing to `facebook_login_session.py`

## Testing Strategy

Unit tests should cover:

- CLI parsing for `--all-visible`
- mutual exclusion between `--limit` and `--all-visible`
- limited mode still stopping at the requested reel count
- all-visible mode continuing through multiple scroll rounds until idle stop
- all-visible mode still deduplicating canonical URLs
- authenticated crawl wiring staying compatible with `--all-visible`

Live verification should cover:

- running `--all-visible` with a valid storage-state file
- confirming the crawl proceeds beyond the old default limit
- confirming the crawl exits once scrolling stops surfacing new reels

## File Impact

Likely files to change:

- Modify: `src/gy_crawler/sources/facebook/reels/collector.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `scripts/facebook_reels_export.py` only if help text compatibility needs adjustment

## Constraints

- Preserve the current `--limit` workflow
- Keep output JSON shape backward compatible
- Reuse the existing login-session path instead of inventing a new auth mechanism
- Keep the implementation small and testable before considering resume support
