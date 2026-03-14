# Facebook Reels JSON Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Playwright-based CLI script that collects visible reels from a Facebook profile reels page and writes one JSON file per reel with publish-time metadata into an account-specific directory.

**Architecture:** A standalone Python script will use Playwright sync APIs to load the profile reels page, collect visible reel URLs and account metadata, then visit each reel URL and extract stable page metadata with layered fallbacks. Small pure helper functions will handle normalization, ID parsing, payload building, and time extraction so they can be covered with unit tests independent of live Facebook pages.

**Tech Stack:** Python 3.11, `unittest`, Playwright for Python, JSON, pathlib

---

### Task 1: Create failing helper tests

**Files:**
- Create: `tests/test_facebook_reels_export.py`
- Create: `facebook_reels_export.py`

**Step 1: Write the failing test**

```python
import unittest

import facebook_reels_export


class NormalizeAccountDirTests(unittest.TestCase):
    def test_build_account_directory_name_normalizes_visible_account_name(self):
        self.assertEqual(
            facebook_reels_export.build_account_directory_name("SubudhiIsha1"),
            "facebook_subudhiisha1",
        )
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_facebook_reels_export.NormalizeAccountDirTests -v`
Expected: FAIL because `facebook_reels_export` or the function does not exist yet.

**Step 3: Write minimal implementation**

```python
def build_account_directory_name(account_name):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_facebook_reels_export.NormalizeAccountDirTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_facebook_reels_export.py facebook_reels_export.py
git commit -m "feat: add facebook reels export helpers"
```

### Task 2: Add reel URL parsing tests

**Files:**
- Modify: `tests/test_facebook_reels_export.py`
- Modify: `facebook_reels_export.py`

**Step 1: Write the failing test**

```python
class ReelIdTests(unittest.TestCase):
    def test_extract_reel_id_returns_numeric_segment(self):
        url = "https://www.facebook.com/reel/795067433657541/?s=fb_shorts_profile&stack_idx=0"
        self.assertEqual(facebook_reels_export.extract_reel_id(url), "795067433657541")
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_facebook_reels_export.ReelIdTests -v`
Expected: FAIL because `extract_reel_id` does not exist yet.

**Step 3: Write minimal implementation**

```python
def extract_reel_id(reel_url):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_facebook_reels_export.ReelIdTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_facebook_reels_export.py facebook_reels_export.py
git commit -m "feat: parse facebook reel ids"
```

### Task 3: Add publish-time extraction tests

**Files:**
- Modify: `tests/test_facebook_reels_export.py`
- Modify: `facebook_reels_export.py`

**Step 1: Write the failing test**

```python
class PublishTimeExtractionTests(unittest.TestCase):
    def test_extract_publish_time_prefers_time_datetime_value(self):
        html = '<time datetime="2025-05-05T22:30:00+0000">May 5, 2025</time>'
        result = facebook_reels_export.extract_publish_time_from_html(html)
        self.assertEqual(result["published_time_iso"], "2025-05-05T22:30:00+00:00")
```
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_facebook_reels_export.PublishTimeExtractionTests -v`
Expected: FAIL because the extractor does not exist yet.

**Step 3: Write minimal implementation**

```python
def extract_publish_time_from_html(html):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_facebook_reels_export.PublishTimeExtractionTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_facebook_reels_export.py facebook_reels_export.py
git commit -m "feat: parse publish time from facebook reel markup"
```

### Task 4: Add payload assembly tests

**Files:**
- Modify: `tests/test_facebook_reels_export.py`
- Modify: `facebook_reels_export.py`

**Step 1: Write the failing test**

```python
class ReelPayloadTests(unittest.TestCase):
    def test_build_reel_payload_preserves_required_fields_and_warnings(self):
        payload = facebook_reels_export.build_reel_payload(
            account_name="SubudhiIsha1",
            source_profile_url="https://example.com/profile",
            reel_url="https://www.facebook.com/reel/795067433657541/",
            view_count_visible="19K",
            detail={"published_time": None, "published_time_iso": None, "caption": None},
        )
        self.assertEqual(payload["reel_id"], "795067433657541")
        self.assertIn("missing published time", payload["warnings"][0].lower())
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_facebook_reels_export.ReelPayloadTests -v`
Expected: FAIL because `build_reel_payload` does not exist yet.

**Step 3: Write minimal implementation**

```python
def build_reel_payload(...):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_facebook_reels_export.ReelPayloadTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_facebook_reels_export.py facebook_reels_export.py
git commit -m "feat: build facebook reel json payloads"
```

### Task 5: Add profile collection tests with fakes

**Files:**
- Modify: `tests/test_facebook_reels_export.py`
- Modify: `facebook_reels_export.py`

**Step 1: Write the failing test**

```python
class VisibleReelCollectionTests(unittest.TestCase):
    def test_collect_visible_reels_deduplicates_urls_and_keeps_visible_counts(self):
        page = FakeProfilePage(...)
        result = facebook_reels_export.collect_visible_reels(page, limit=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["view_count_visible"], "19K")
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_facebook_reels_export.VisibleReelCollectionTests -v`
Expected: FAIL because `collect_visible_reels` does not exist yet or returns the wrong shape.

**Step 3: Write minimal implementation**

```python
def collect_visible_reels(page, limit):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_facebook_reels_export.VisibleReelCollectionTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_facebook_reels_export.py facebook_reels_export.py
git commit -m "feat: collect visible reels from facebook profile pages"
```

### Task 6: Add CLI integration tests with mocks

**Files:**
- Modify: `tests/test_facebook_reels_export.py`
- Modify: `facebook_reels_export.py`

**Step 1: Write the failing test**

```python
class MainTests(unittest.TestCase):
    def test_main_writes_one_json_per_visible_reel(self):
        ...
        exit_code = facebook_reels_export.main(
            ["--profile-url", "https://example.com/reels", "--limit", "2", "--output-root", tmpdir]
        )
        self.assertEqual(exit_code, 0)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_facebook_reels_export.MainTests -v`
Expected: FAIL because CLI wiring and file output are incomplete.

**Step 3: Write minimal implementation**

```python
def main(argv=None):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_facebook_reels_export.MainTests -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_facebook_reels_export.py facebook_reels_export.py
git commit -m "feat: add facebook reels export cli"
```

### Task 7: Run full test suite and live verification

**Files:**
- Modify: `facebook_reels_export.py`
- Modify: `tests/test_facebook_reels_export.py`

**Step 1: Run the focused tests**

Run: `python -m unittest tests.test_facebook_reels_export -v`
Expected: PASS

**Step 2: Run the existing regression tests**

Run: `cd podcast_mp3_all && python -m unittest tests.test_analyze_mp3_batch -v`
Expected: PASS

**Step 3: Install Playwright browser dependencies if needed**

Run: `python -m playwright install chromium`
Expected: browser already installed or installs successfully

**Step 4: Run live export against the approved Facebook page**

Run: `python facebook_reels_export.py --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" --limit 10 --output-root output --headless`
Expected: summary showing discovered reels and written JSON files

**Step 5: Verify output files**

Run: `find output -maxdepth 2 -type f | sort`
Expected: JSON files under `output/facebook_subudhiisha1/`

**Step 6: Commit**

```bash
git add facebook_reels_export.py tests/test_facebook_reels_export.py docs/plans/2026-03-14-facebook-reels-json-design.md docs/plans/2026-03-14-facebook-reels-json-export.md
git commit -m "feat: export facebook reels to json"
```

## Notes

- This workspace currently lives inside an untracked subdirectory of the parent repository. Re-check git status before any commit so unrelated parent-level paths are not accidentally staged.
- Keep network-dependent logic thin and push parsing behavior into pure helpers so tests stay fast and deterministic.
