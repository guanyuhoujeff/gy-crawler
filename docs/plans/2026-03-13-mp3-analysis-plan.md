# MP3 Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a batch analyzer that uploads every file in `mp3/` to the local analyzer service and writes raw JSON responses into `result/[mp3 filename].md`.

**Architecture:** A standalone Python script will scan `mp3/`, skip already-generated Markdown files in `result/`, call the local upload endpoint once per file, and write the raw JSON response into fenced Markdown. The script will keep running after per-file failures and print a final summary so interrupted or partially failing runs remain usable.

**Tech Stack:** Python 3, `requests`, `unittest`, local HTTP analyzer on `localhost:52501`

---

### Task 1: Write the batch workflow tests

**Files:**
- Create: `tests/test_analyze_mp3_batch.py`
- Test: `tests/test_analyze_mp3_batch.py`

**Step 1: Write the failing test**

```python
def test_format_markdown_wraps_raw_json_in_fenced_block(self):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analyze_mp3_batch -v`
Expected: FAIL because the script module does not exist yet.

**Step 3: Write minimal implementation**

```python
def format_markdown(payload):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_analyze_mp3_batch -v`
Expected: PASS for the new test.

**Step 5: Commit**

```bash
git add tests/test_analyze_mp3_batch.py analyze_mp3_batch.py
git commit -m "test: add analyzer markdown formatting coverage"
```

### Task 2: Add batch-processing behavior

**Files:**
- Modify: `analyze_mp3_batch.py`
- Modify: `tests/test_analyze_mp3_batch.py`
- Test: `tests/test_analyze_mp3_batch.py`

**Step 1: Write the failing test**

```python
def test_process_batch_skips_existing_results_and_continues_after_failures(self):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analyze_mp3_batch -v`
Expected: FAIL because skip-existing and continue-on-error behavior is missing.

**Step 3: Write minimal implementation**

```python
def process_batch(...):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_analyze_mp3_batch -v`
Expected: PASS for the batch behavior tests.

**Step 5: Commit**

```bash
git add tests/test_analyze_mp3_batch.py analyze_mp3_batch.py
git commit -m "feat: add batch mp3 analysis workflow"
```

### Task 3: Exercise the real analyzer service

**Files:**
- Modify: `analyze_mp3_batch.py`
- Create: `result/*.md`

**Step 1: Write the failing test**

```python
def test_cli_defaults_to_mp3_and_result_directories(self):
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_analyze_mp3_batch -v`
Expected: FAIL because the CLI contract is incomplete.

**Step 3: Write minimal implementation**

```python
def main():
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_analyze_mp3_batch -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_analyze_mp3_batch.py analyze_mp3_batch.py result
git commit -m "feat: generate markdown analysis results for mp3 files"
```

### Task 4: Verify against the real dataset

**Files:**
- Modify: `result/*.md`

**Step 1: Run the analyzer**

Run: `python3 analyze_mp3_batch.py`
Expected: Markdown files are created in `result/`.

**Step 2: Verify the output count**

Run: `find result -maxdepth 1 -type f -name '*.md' | wc -l`
Expected: matches the number of `.mp3` files in `mp3/`, unless some files fail and are reported explicitly.

**Step 3: Verify a sample output**

Run: `sed -n '1,40p' result/001_2026-03-13.mp3.md`
Expected: fenced JSON Markdown.

**Step 4: Commit**

```bash
git add analyze_mp3_batch.py tests/test_analyze_mp3_batch.py result docs/plans
git commit -m "feat: batch analyze mp3 files into markdown"
```
