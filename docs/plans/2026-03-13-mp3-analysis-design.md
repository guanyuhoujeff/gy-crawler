# MP3 Analysis Batch Design

**Goal:** Analyze every file in `mp3/` via the local `http://localhost:52501/analyze/upload` endpoint and write one Markdown file per MP3 into `result/`.

**Scope**
- Input directory: `mp3/`
- Output directory: `result/`
- Output filename: `[mp3 filename].md`
- Markdown body: raw API JSON wrapped in a fenced `json` code block

**Workflow**
1. Scan `mp3/` for `.mp3` files in sorted order.
2. For each file, derive `result/<mp3 filename>.md`.
3. Skip the file if the Markdown already exists.
4. Upload the MP3 as multipart form data with field name `file`.
5. Parse `response.json()`.
6. Write a Markdown document containing the raw JSON.
7. Continue after per-file failures and print a final success/failure summary.

**Error Handling**
- HTTP errors should be surfaced per file and counted as failures.
- JSON parse errors should be surfaced per file and counted as failures.
- Existing Markdown files should be left untouched.
- The batch should not abort on a single-file failure.

**Implementation Shape**
- A small Python script with pure helper functions for:
  - discovering MP3 paths
  - formatting Markdown from a JSON object
  - analyzing one file through an injectable uploader function
  - processing a batch with skip-existing behavior
- Tests will use `unittest` and temporary directories so they run without the local analyzer service.

**Verification**
- Run the unit tests.
- Run the script against `mp3/`.
- Verify the number of `.md` files in `result/`.
- Inspect a sample Markdown file to confirm it contains a fenced JSON block.
