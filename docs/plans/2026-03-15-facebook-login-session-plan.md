# Facebook Reels Login Session Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a one-time manual Facebook login bootstrap that saves Playwright session state to disk and lets the Facebook Reels crawler reuse that session in later runs.

**Architecture:** A dedicated login bootstrap script will own manual authentication and session persistence. The existing Facebook Reels collector will remain responsible for crawling only, but will accept an optional storage-state path when creating the Playwright browser context. The crawler CLI will expose this as an optional flag while preserving the current public-mode path when the flag is omitted.

**Tech Stack:** Python 3.11, unittest, Playwright, pathlib, argparse

---

### Task 1: Add failing tests for authenticated collector construction

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/collector.py`

**Step 1: Write the failing test**

Add a focused unit test that instantiates `PlaywrightFacebookCollector(storage_state_path=".secrets/facebook-state.json")` with mocked Playwright objects and asserts that `browser.new_context(...)` receives the same storage-state path.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.AuthenticatedCollectorTests -v`
Expected: FAIL because the collector constructor does not yet accept or forward `storage_state_path`.

**Step 3: Write minimal implementation**

Update `src/gy_crawler/sources/facebook/reels/collector.py` so:

- `PlaywrightFacebookCollector.__init__` accepts `storage_state_path=None`
- `__enter__` passes `storage_state=self.storage_state_path` into `browser.new_context(...)` only when a path is provided

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.AuthenticatedCollectorTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/collector.py
git commit -m "feat: allow facebook reels collector to reuse storage state"
```

### Task 2: Add failing tests for crawler CLI storage-state handling

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`

**Step 1: Write the failing test**

Add CLI parsing and main-path tests for:

- accepting `--storage-state .secrets/facebook-state.json`
- forwarding the parsed value into collector construction
- failing fast with a clear error when the path does not exist

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.StorageStateCliTests -v`
Expected: FAIL because the CLI does not expose `--storage-state` and does not validate the file path.

**Step 3: Write minimal implementation**

Update `src/gy_crawler/sources/facebook/reels/cli.py` to:

- add `--storage-state`
- validate the file path only when the flag is provided
- pass the path into `PlaywrightFacebookCollector(...)`
- preserve current behavior when the flag is omitted

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.StorageStateCliTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/cli.py
git commit -m "feat: add storage state option to facebook reels cli"
```

### Task 3: Add failing tests for manual login bootstrap script

**Files:**
- Create: `tests/unit/facebook/test_login_session.py`
- Create: `scripts/facebook_login_session.py`

**Step 1: Write the failing test**

Create unit tests covering:

- CLI argument parsing requires `--storage-state`
- the script launches Chromium in headed mode
- after confirmation, `context.storage_state(path=...)` is called
- parent directories for the state file are created automatically

Use mocked Playwright objects and mocked user confirmation input.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_login_session -v`
Expected: FAIL because the login bootstrap script does not exist yet.

**Step 3: Write minimal implementation**

Create `scripts/facebook_login_session.py` with:

- repo bootstrap wiring matching other scripts under `scripts/`
- an argparse interface
- headed Chromium launch
- manual confirmation prompt
- storage-state file write
- clean shutdown with exit code `0` on success

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_login_session -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_login_session.py scripts/facebook_login_session.py
git commit -m "feat: add facebook login session bootstrap script"
```

### Task 4: Add failure-path coverage for expired or missing sessions

**Files:**
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`

**Step 1: Write the failing test**

Add tests for:

- missing storage-state path returns exit code `1`
- error text tells the user to rerun the login bootstrap script
- authenticated mode does not silently fall back to public mode

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.StorageStateErrorTests -v`
Expected: FAIL because the CLI does not yet provide these error paths.

**Step 3: Write minimal implementation**

Tighten `src/gy_crawler/sources/facebook/reels/cli.py` error handling so:

- missing files are reported before browser startup
- authenticated-mode failures surface actionable remediation text
- public mode remains unchanged

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.unit.facebook.test_reels_cli.StorageStateErrorTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/facebook/test_reels_cli.py src/gy_crawler/sources/facebook/reels/cli.py
git commit -m "feat: improve facebook storage state failure handling"
```

### Task 5: Add repository hygiene for session files

**Files:**
- Modify: `.gitignore`

**Step 1: Write the failing check**

Inspect `.gitignore` and confirm that `.secrets/` is not yet ignored.

**Step 2: Run check to verify change is needed**

Run: `rg -n "^\\.secrets/?$" .gitignore`
Expected: no matches

**Step 3: Write minimal implementation**

Add:

```gitignore
.secrets/
```

to `.gitignore`.

**Step 4: Run check to verify it passes**

Run: `rg -n "^\\.secrets/?$" .gitignore`
Expected: one match

**Step 5: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore saved facebook session files"
```

### Task 6: Run focused verification and manual workflow check

**Files:**
- Modify: any affected files from earlier tasks

**Step 1: Run focused unit tests**

Run: `python -m unittest tests.unit.facebook.test_reels_cli tests.unit.facebook.test_login_session -v`
Expected: PASS

**Step 2: Verify crawler help shows the new flag**

Run: `python scripts/facebook_reels_export.py --help`
Expected: output includes `--storage-state`

**Step 3: Verify login bootstrap help**

Run: `python scripts/facebook_login_session.py --help`
Expected: shows required `--storage-state` argument and headed login usage

**Step 4: Perform manual session bootstrap**

Run: `python scripts/facebook_login_session.py --storage-state .secrets/facebook-state.json --headed`
Expected: a visible browser opens, manual login succeeds, and `.secrets/facebook-state.json` is created

**Step 5: Perform authenticated crawl smoke test**

Run: `python scripts/facebook_reels_export.py --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --storage-state .secrets/facebook-state.json --limit 20 --output-root output`
Expected: crawl completes using the saved session and writes reel JSON files

**Step 6: Commit**

```bash
git add .gitignore scripts/facebook_login_session.py src/gy_crawler/sources/facebook/reels/cli.py src/gy_crawler/sources/facebook/reels/collector.py tests/unit/facebook/test_login_session.py tests/unit/facebook/test_reels_cli.py docs/plans/2026-03-15-facebook-login-session-design.md docs/plans/2026-03-15-facebook-login-session-plan.md
git commit -m "feat: add reusable facebook login session bootstrap"
```

## Notes

- Keep the authenticated path optional; do not require session state for public accounts.
- Prefer explicit user confirmation over fragile DOM-based login detection.
- Do not attempt to store or accept raw credentials in CLI arguments.
- Fail fast when a configured session file is missing or clearly invalid.
