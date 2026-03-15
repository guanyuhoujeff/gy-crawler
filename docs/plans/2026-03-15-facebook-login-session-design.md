# Facebook Reels Login Session Bootstrap Design

## Goal

Add an optional authenticated collection path for the Facebook Reels crawler by separating login bootstrap from reel export. A user should be able to log in manually once in a visible browser, save Playwright session state to disk, and reuse that state in later crawl runs.

## Scope

- Add a one-time login bootstrap script for manual Facebook login
- Add optional `storage_state` support to the existing Facebook Reels collector
- Keep the current public crawling path working when no session file is provided
- Make session expiry a clear operational error instead of an automatic recovery path

## Chosen Approach

Use a separate login bootstrap script plus an optional `--storage-state` flag on the existing crawler.

This is the balanced option:

- keeps login concerns out of the crawler's main collection flow
- preserves the current public-mode behavior
- lets operators refresh an expired session without changing crawl logic
- avoids brittle automated username/password entry

## Non-Goals

- No fully automated Facebook login flow
- No account/password handling in crawler CLI arguments
- No cookie scraping outside of Playwright session state
- No guarantee of permanent sessions; expiry is expected and should be handled operationally

## User Experience

### First-Time Session Creation

The operator runs a dedicated login script in headed mode:

```bash
python scripts/facebook_login_session.py \
  --storage-state .secrets/facebook-state.json \
  --headed
```

The script opens a browser, waits for the operator to log in manually, then saves the Playwright storage state to the requested path.

### Later Crawl Runs

The operator runs the existing crawler with the saved state:

```bash
python scripts/facebook_reels_export.py \
  --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" \
  --storage-state .secrets/facebook-state.json \
  --limit 200 \
  --output-root output
```

If no storage-state path is provided, the crawler behaves exactly as it does today.

## Architecture

### Login Bootstrap Script

Create a dedicated script, likely `scripts/facebook_login_session.py`, that:

1. bootstraps repo imports the same way as other scripts under `scripts/`
2. starts Playwright Chromium in headed mode
3. opens Facebook
4. waits for the operator to confirm login is complete
5. writes `context.storage_state(path=...)`
6. exits cleanly

This script should do nothing related to reel crawling.

### Collector Changes

Extend the `PlaywrightFacebookCollector` constructor to accept optional browser-context configuration such as:

- `storage_state_path`
- future context options if needed

At context creation time, if `storage_state_path` is provided, pass it into `browser.new_context(...)`. The collector should not attempt to log in, repair sessions, or save state. It should only consume an existing state file.

### CLI Changes

Add an optional `--storage-state` argument to the Facebook Reels CLI and thread it into collector construction.

Behavior rules:

- if `--storage-state` is absent, run in public mode
- if `--storage-state` is present but missing, fail fast with a clear error
- if `--storage-state` is present but expired, fail with a clear instruction to rerun the login bootstrap script

## Login Completion Semantics

Prefer explicit user confirmation over fragile DOM-only detection.

Recommended flow:

1. launch Facebook in headed mode
2. print instructions telling the user to complete login in the opened browser window
3. prompt for Enter in the terminal when they are done
4. optionally perform a light sanity check before saving state

This is preferred because Facebook's login UI can change frequently. Manual confirmation is a more stable boundary than relying on a specific selector.

## Session File Handling

Recommended location:

- `.secrets/facebook-state.json`

Rules:

- session files must not be committed
- the directory should be created automatically if missing
- crawler errors should mention the exact command to refresh the session

Suggested `.gitignore` coverage:

- `.secrets/`

## Error Handling

### Login Bootstrap

- if `--storage-state` is missing, fail argument parsing
- if the browser closes before confirmation, fail with a clear message
- if writing the state file fails, return a non-zero exit code and surface the path error

### Crawler

- if the supplied state file does not exist, return a non-zero exit code with a direct remediation message
- if the page appears to be on a login wall or otherwise fails to show reels, report that the saved session may be expired
- do not silently fall back from authenticated mode to public mode

## Testing Strategy

Unit tests should cover:

- CLI parsing for `--storage-state`
- collector passing `storage_state` into `browser.new_context(...)`
- login bootstrap writing storage state to the requested path
- missing state file failures
- authenticated and unauthenticated collector construction paths

Live verification should cover:

- creating a session file by logging in manually
- reusing the saved file in a later crawl
- observing a clear failure path after intentionally removing or invalidating the session file

## File Impact

Likely files to change:

- Create: `scripts/facebook_login_session.py`
- Modify: `scripts/_bootstrap.py` only if shared bootstrap helpers need reuse
- Modify: `src/gy_crawler/sources/facebook/reels/collector.py`
- Modify: `src/gy_crawler/sources/facebook/reels/cli.py`
- Modify: `scripts/facebook_reels_export.py` only if help text or compatibility wiring needs updates
- Create: `tests/unit/facebook/test_login_session.py`
- Modify: `tests/unit/facebook/test_reels_cli.py`
- Modify: `.gitignore`

## Constraints

- Keep the authenticated path optional
- Do not entangle login bootstrap with crawl execution
- Avoid storing credentials directly in repo config or CLI history
- Keep the public-mode crawler behavior backward compatible
