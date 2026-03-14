# Facebook Reels SocialVideoRecord Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Normalize Facebook Reels output into a shared `SocialVideoRecord` structure and add bounded auto-scroll collection to support higher reel limits.

**Architecture:** The current Facebook Reels source package will keep its source-specific collector and parser logic, but the payload assembly will be refactored into a normalized shared record shape with Facebook-only fields nested under `platform_metadata`. Collection will shift from single-pass visible-only extraction to a bounded loop that scrolls until the requested reel count is reached or collection stalls.

**Tech Stack:** Python 3.11, unittest, Playwright, pathlib, JSON

---

### Task 1: Add failing tests for normalized SocialVideoRecord output

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/models.py`

**Step 1: Write the failing test**

Add a test that asserts the reel payload contains:

- `platform`
- `content_type`
- `content_id`
- `source_url`
- `canonical_url`
- `author_name`
- `author_id`
- `author_handle`
- `description`
- `platform_metadata`

and no longer uses the old top-level Facebook-only shape.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.ReelPayloadTests -v`
Expected: FAIL because the current payload shape is still Facebook-specific.

**Step 3: Write minimal implementation**

Refactor payload creation in `src/gy_crawler/sources/facebook/reels/models.py` to build the normalized structure.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.ReelPayloadTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/models.py
git commit -m "feat: normalize facebook reels into social video records"
```

### Task 2: Add canonical URL and author metadata tests

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/paths.py`
- Modify: `src/gy_crawler/sources/facebook/reels/models.py`

**Step 1: Write the failing test**

Add tests for:

- converting discovered reel URLs into canonical reel URLs
- extracting a stable author handle
- passing through author id when profile metadata provides one

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.ReelIdTests tests.unit.facebook.test_reels_cli.ReelPayloadTests -v`
Expected: FAIL because the canonical URL and author mapping do not exist yet.

**Step 3: Write minimal implementation**

Add canonical URL helpers and update payload mapping.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.ReelIdTests tests.unit.facebook.test_reels_cli.ReelPayloadTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/paths.py src/gy_crawler/sources/facebook/reels/models.py
git commit -m "feat: add canonical facebook reel url mapping"
```

### Task 3: Add failing tests for scroll-based profile collection

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/collector.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`

**Step 1: Write the failing test**

Add tests using fake pages that simulate multiple collection rounds:

- collecting enough reels without scrolling
- collecting more reels after one or more scrolls
- stopping after `max_idle_scrolls` with no new URLs

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.VisibleReelCollectionTests -v`
Expected: FAIL because collection is currently single-pass only.

**Step 3: Write minimal implementation**

Refactor collection so the page can:

- scroll
- wait
- re-read loaded DOM anchors
- stop by `limit`, `max_scrolls`, and idle count

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.VisibleReelCollectionTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/collector.py src/gy_crawler/sources/facebook/reels/cli.py
git commit -m "feat: add bounded auto-scroll for facebook reels collection"
```

### Task 4: Add CLI argument coverage for scroll controls

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`

**Step 1: Write the failing test**

Add a CLI parsing test covering:

- `--limit`
- `--no-scroll`
- `--max-scrolls`
- `--max-idle-scrolls`

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.MainTests -v`
Expected: FAIL because the CLI does not expose those arguments yet.

**Step 3: Write minimal implementation**

Add the parser arguments and thread them into export flow.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.MainTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/cli.py
git commit -m "feat: add facebook reels scroll controls to cli"
```

### Task 5: Run focused and live verification

**Files:**
- Modify: any affected Facebook reels files

**Step 1: Run Facebook unit tests**

Run: `python -m unittest tests.unit.facebook.test_reels_cli -v`
Expected: PASS

**Step 2: Run script bootstrap regression**

Run: `python -m unittest tests.unit.test_script_bootstrap -v`
Expected: PASS

**Step 3: Run live crawl with current target**

Run: `python -m gy_crawler.sources.facebook.reels.cli --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --limit 10 --output-root output`
Expected: PASS with normalized JSON output

**Step 4: Run live crawl with a higher target**

Run: `python -m gy_crawler.sources.facebook.reels.cli --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --limit 20 --output-root output`
Expected: additional scroll attempts occur; collection stops at limit or idle bounds without hanging

**Step 5: Inspect one output file**

Run: `sed -n '1,220p' output/facebook_subudhiisha1/<reel-id>.json`
Expected: normalized `SocialVideoRecord` shape

**Step 6: Commit**

```bash
git add src/gy_crawler/sources/facebook/reels tests/unit/facebook/test_reels_cli.py docs/plans/2026-03-14-facebook-reels-social-video-record-design.md docs/plans/2026-03-14-facebook-reels-social-video-record-plan.md
git commit -m "feat: normalize facebook reels and add auto-scroll"
```

## Notes

- Keep stop conditions conservative so scroll logic cannot run indefinitely.
- Preserve the current extraction fallbacks for publish time while changing the outer payload structure.
- Do not move Facebook-only fields into top-level shared fields unless they are likely to exist in YouTube as well.
