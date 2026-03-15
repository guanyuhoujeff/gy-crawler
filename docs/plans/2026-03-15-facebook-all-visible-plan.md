# Facebook Reels All Visible Crawl Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `--all-visible` Facebook Reels crawl mode that keeps scrolling until no new visible reels appear, while preserving the existing `--limit` workflow.

**Architecture:** The change stays inside the existing reels exporter and collector. The CLI will expose a new mutually exclusive `--all-visible` mode, and the collector will support both count-bounded and best-effort full-visible collection using the current canonical URL deduplication logic.

**Tech Stack:** Python 3.10+, unittest, argparse, Playwright, pathlib

---

### Task 1: Add failing tests for CLI mode selection

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`

**Step 1: Write the failing tests**

Add focused CLI parsing tests that assert:

- `--all-visible` parses successfully
- `--limit` still parses successfully
- `--all-visible` and `--limit` together raise argparse usage failure
- default invocation still behaves like limited mode with `limit == 10`

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli.AllVisibleCliModeTests -v`
Expected: FAIL because `--all-visible` is not yet exposed and mutual exclusion is not implemented.

**Step 3: Write minimal implementation**

Update `src/gy_crawler/sources/facebook/reels/cli.py` so:

- `parse_args(...)` adds a mutually exclusive group for `--limit` and `--all-visible`
- `--limit` remains available
- the parser defaults to `limit=10` when no explicit mode is selected
- parsed args expose a boolean `all_visible`

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli.AllVisibleCliModeTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/cli.py
git commit -m "feat: add facebook reels all-visible cli mode"
```

### Task 2: Add failing tests for all-visible collector behavior

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/collector.py`

**Step 1: Write the failing tests**

Add collector tests that assert:

- `collect_visible_reels(..., all_visible=True)` continues across multiple scroll rounds until idle stop
- the returned reel list includes every unique canonical reel URL surfaced across those rounds
- duplicates encountered across rounds are still removed
- limited mode behavior remains unchanged

Use the existing fake page helpers and add payload rounds that reveal new reels after several scrolls.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli.AllVisibleCollectionTests -v`
Expected: FAIL because the collector does not yet accept or honor an `all_visible` mode.

**Step 3: Write minimal implementation**

Update `src/gy_crawler/sources/facebook/reels/collector.py` so:

- `collect_visible_reels(...)` accepts `all_visible=False`
- limited mode keeps stopping at `limit`
- all-visible mode does not stop on reel count
- all-visible mode stops when `idle_scrolls >= max_idle_scrolls`
- canonical URL deduplication remains the single source of truth

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli.AllVisibleCollectionTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/collector.py
git commit -m "feat: collect all visible facebook reels across scroll rounds"
```

### Task 3: Add failing tests for CLI to collector wiring

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`

**Step 1: Write the failing tests**

Add tests that assert:

- `main(...)` forwards `all_visible=True` into the profile collection/export path
- `main(...)` still forwards `limit` in limited mode
- authenticated mode with `--storage-state` remains compatible with `--all-visible`

Patch the collector or export entrypoint so the tests can inspect forwarded arguments directly.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli.AllVisibleWiringTests -v`
Expected: FAIL because the CLI does not yet thread `all_visible` into export or collection.

**Step 3: Write minimal implementation**

Update `src/gy_crawler/sources/facebook/reels/cli.py` so:

- `export_reels(...)` accepts `all_visible=False`
- `main(...)` forwards `args.all_visible`
- `export_reels(...)` passes `all_visible` into `collector.collect_profile(...)`

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli.AllVisibleWiringTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/cli.py
git commit -m "feat: wire facebook all-visible mode through export flow"
```

### Task 4: Run focused verification and authenticated smoke test

**Files:**
- Modify: any affected files from earlier tasks

**Step 1: Run focused unit tests**

Run: `python3 -m unittest tests.unit.facebook.test_reels_cli -v`
Expected: PASS

**Step 2: Verify crawler help shows the new mode**

Run: `python3 scripts/facebook_reels_export.py --help`
Expected: output includes `--all-visible`

**Step 3: Run authenticated all-visible smoke test**

Run: `python3 scripts/facebook_reels_export.py --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --storage-state .secrets/facebook-state.json --all-visible --max-idle-scrolls 5 --delay-seconds 2 --output-root output_all_visible`
Expected: the crawl proceeds past the old default limit and writes multiple reel JSON files before stopping after idle scroll rounds.

**Step 4: Clean transient verification output if needed**

Remove `output_all_visible/` if it is only a temporary verification artifact and not intended to stay in the worktree.

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/cli.py src/gy_crawler/sources/facebook/reels/collector.py docs/plans/2026-03-15-facebook-all-visible-design.md docs/plans/2026-03-15-facebook-all-visible-plan.md
git commit -m "feat: add best-effort facebook all-visible reels crawl"
```

## Notes

- Keep the new mode best-effort; do not overstate completeness guarantees in help text or errors.
- Preserve the existing JSON payload shape and output directory structure.
- Do not add checkpoint or resume support in this plan.
- Reuse the existing authenticated storage-state path exactly as implemented today.
