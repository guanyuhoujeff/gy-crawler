# Repo Structure Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize `gy-crawler` into a mixed core-plus-sources package structure that supports multiple crawler types while preserving current functionality.

**Architecture:** The migration will introduce a Python package under `src/gy_crawler`, move current crawler code into source-specific modules, split tests into unit and integration tiers, and separate code from generated outputs. The work should proceed incrementally, starting with skeleton directories and the existing Facebook Reels crawler, then classifying podcast-related code before broader cleanup.

**Tech Stack:** Python 3.11, unittest, pathlib, git, Playwright

---

### Task 1: Create package skeleton

**Files:**
- Create: `src/gy_crawler/__init__.py`
- Create: `src/gy_crawler/cli/__init__.py`
- Create: `src/gy_crawler/core/__init__.py`
- Create: `src/gy_crawler/sources/__init__.py`
- Create: `src/gy_crawler/sources/facebook/__init__.py`
- Create: `src/gy_crawler/sources/facebook/reels/__init__.py`
- Create: `src/gy_crawler/pipelines/__init__.py`
- Create: `src/gy_crawler/storage/__init__.py`
- Create: `src/gy_crawler/models/__init__.py`
- Create: `src/gy_crawler/utils/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/fixtures/.gitkeep`
- Create: `scripts/.gitkeep`
- Create: `config/.gitkeep`
- Create: `notebooks/.gitkeep`

**Step 1: Create the empty package files**

Create the exact paths above with minimal contents.

**Step 2: Verify the tree exists**

Run: `find src tests scripts config notebooks -maxdepth 4 -type f | sort`
Expected: the new package skeleton files are present.

**Step 3: Commit**

```bash
git add src tests scripts config notebooks
git commit -m "chore: add gy crawler package skeleton"
```

### Task 2: Add project metadata and import path configuration

**Files:**
- Create: `pyproject.toml`
- Modify: `README.md`

**Step 1: Write minimal project metadata**

Create `pyproject.toml` with a minimal Python project definition that supports `src/` layout and local imports during development.

**Step 2: Document local setup**

Update `README.md` with the recommended setup and test commands using the new package layout.

**Step 3: Verify imports work**

Run: `python -c "import sys; sys.path.insert(0, 'src'); import gy_crawler; print('ok')"`
Expected: prints `ok`

**Step 4: Commit**

```bash
git add pyproject.toml README.md
git commit -m "chore: add project metadata for src layout"
```

### Task 3: Migrate the Facebook Reels crawler

**Files:**
- Create: `src/gy_crawler/sources/facebook/reels/cli.py`
- Create: `src/gy_crawler/sources/facebook/reels/collector.py`
- Create: `src/gy_crawler/sources/facebook/reels/parser.py`
- Create: `src/gy_crawler/sources/facebook/reels/models.py`
- Create: `src/gy_crawler/sources/facebook/reels/paths.py`
- Modify: `facebook_reels_export.py`
- Modify: `tests/test_facebook_reels_export.py`
- Create: `tests/unit/facebook/test_reels_cli.py`

**Step 1: Write failing import or behavior tests for the new module path**

Move or rewrite the current Facebook tests so they target the new package path under `tests/unit/facebook/`.

**Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.unit.facebook.test_reels_cli -v`
Expected: FAIL because the new module path is not implemented yet.

**Step 3: Move minimal implementation into the new package**

Split the current single-file script by responsibility:

- CLI argument parsing in `cli.py`
- Playwright collection in `collector.py`
- publish-time and caption extraction in `parser.py`
- payload structure in `models.py`
- directory naming and file path helpers in `paths.py`

Keep `facebook_reels_export.py` only as a temporary compatibility shim or remove it after imports are updated.

**Step 4: Run the migrated tests**

Run: `python -m unittest tests.unit.facebook.test_reels_cli -v`
Expected: PASS

**Step 5: Run live verification**

Run: `python -m gy_crawler.sources.facebook.reels.cli --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --limit 10 --output-root output`
Expected: JSON files are written under the account-specific directory.

**Step 6: Commit**

```bash
git add src/gy_crawler/sources/facebook/reels tests/unit/facebook/test_reels_cli.py
git commit -m "feat: migrate facebook reels crawler into package layout"
```

### Task 4: Reclassify podcast code

**Files:**
- Modify: `podcasts.py`
- Modify: `podcast_mp3_all/analyze_mp3_batch.py`
- Modify: `podcast_mp3_all/tests/test_analyze_mp3_batch.py`
- Create: `src/gy_crawler/sources/podcast/__init__.py`
- Create: `src/gy_crawler/sources/podcast/episodes/__init__.py`
- Create: `src/gy_crawler/sources/podcast/feeds/__init__.py`
- Create: `tests/unit/podcast/__init__.py`

**Step 1: Inspect podcast scripts and decide ownership**

Determine which parts are durable product code and which are one-off operational scripts.

**Step 2: Write tests for the first podcast module you plan to migrate**

Add or move tests under `tests/unit/podcast/` for the productized parts.

**Step 3: Run tests to verify they fail if module paths changed**

Run the specific migrated unit tests.
Expected: initial failures due to missing or moved imports.

**Step 4: Move product logic into `src/gy_crawler/sources/podcast/...`**

Keep one-off utilities in `scripts/` if they are not part of the long-term crawler API.

**Step 5: Re-run podcast tests**

Run: `python -m unittest tests.unit.podcast -v`
Expected: PASS for migrated podcast tests.

**Step 6: Commit**

```bash
git add src/gy_crawler/sources/podcast tests/unit/podcast scripts
git commit -m "refactor: organize podcast crawler code"
```

### Task 5: Split repository data and generated outputs from tracked code

**Files:**
- Create: `.gitignore`
- Modify: `output/`
- Modify: `podcast_mp3_all/`
- Modify: `Untitled.ipynb`

**Step 1: Add ignore rules**

Write `.gitignore` rules for:

- `__pycache__/`
- `.ipynb_checkpoints/`
- `output/`
- `data/raw/`
- `data/tmp/`
- `*.log`
- downloaded media files as appropriate

**Step 2: Move exploratory notebook**

Move `Untitled.ipynb` into `notebooks/` and rename it to something descriptive if it is worth keeping.

**Step 3: Verify status shows only intended tracked files**

Run: `git status --short`
Expected: generated outputs and caches no longer appear as untracked items.

**Step 4: Commit**

```bash
git add .gitignore notebooks
git commit -m "chore: ignore generated crawler artifacts"
```

### Task 6: Prepare a unified CLI without overbuilding it

**Files:**
- Create: `src/gy_crawler/cli/main.py`
- Modify: `README.md`

**Step 1: Write a failing test for a thin CLI dispatcher**

Add a test that imports a top-level CLI and verifies it can dispatch at least the Facebook Reels command.

**Step 2: Run the CLI test to verify it fails**

Run the new CLI unit test.
Expected: FAIL because the dispatcher does not exist yet.

**Step 3: Implement a minimal dispatcher**

Support one routed command first, such as Facebook Reels. Do not generalize further until a second source needs it.

**Step 4: Run the CLI test**

Expected: PASS

**Step 5: Commit**

```bash
git add src/gy_crawler/cli/main.py README.md
git commit -m "feat: add minimal unified crawler cli"
```

### Task 7: Full verification

**Files:**
- Modify: any files touched above as needed

**Step 1: Run Facebook unit tests**

Run: `python -m unittest tests.unit.facebook.test_reels_cli -v`
Expected: PASS

**Step 2: Run podcast unit tests**

Run: `python -m unittest tests.unit.podcast -v`
Expected: PASS for migrated tests

**Step 3: Run legacy regression tests that remain relevant**

Run: `cd podcast_mp3_all && python -m unittest tests.test_analyze_mp3_batch -v`
Expected: PASS until the old tree is fully retired

**Step 4: Run live Facebook verification**

Run: `python -m gy_crawler.sources.facebook.reels.cli --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --limit 10 --output-root output`
Expected: successful crawl and JSON output

**Step 5: Inspect repository status**

Run: `git status --short`
Expected: only intentional tracked files or known migration leftovers remain

**Step 6: Commit**

```bash
git add .
git commit -m "refactor: reorganize gy crawler repository"
```

## Notes

- The user explicitly requested no commit at this stage. Treat every commit command in this plan as future execution guidance, not something to do now.
- Do not delete legacy files until the migrated module path is verified and tests are green.
- Move shared code into `core/` only after it is reused by at least two sources.
