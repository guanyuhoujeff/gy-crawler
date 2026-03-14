# Gy Crawler Repo Structure Design

## Goal

Restructure `gy-crawler` into a maintainable multi-source crawler repository that can grow to support Facebook Reels, YouTube, podcast, news, and additional sources without collapsing into source-specific ad hoc scripts.

## Chosen Approach

Use a mixed structure:

- keep shared behavior in a small, explicit core
- organize source-specific logic under `sources/`
- support both per-source CLI entrypoints and a future unified top-level CLI

This balances speed and maintainability. It avoids over-engineering a heavy framework up front, while also preventing common crawler concerns from being copy-pasted across sources.

## Top-Level Structure

```text
gy-crawler/
  src/
    gy_crawler/
      cli/
      core/
      sources/
        facebook/
          reels/
        youtube/
          videos/
          channels/
        news/
          sites/
        podcast/
          feeds/
          episodes/
      pipelines/
      storage/
      models/
      utils/
  tests/
    unit/
    integration/
    fixtures/
  scripts/
  docs/
    plans/
    sources/
  data/
    raw/
    processed/
    tmp/
  output/
  config/
  notebooks/
```

## Directory Responsibilities

### `src/gy_crawler/cli/`

Contains unified command-line entrypoints, such as future commands like:

- `crawl`
- `export`
- `debug`

This is the public CLI surface for the repository as a platform.

### `src/gy_crawler/core/`

Contains shared infrastructure that is reusable across at least two sources, such as:

- Playwright browser/session setup
- HTTP client wrappers
- retry/backoff logic
- logging
- shared exceptions
- time and date normalization

This directory must stay small. If logic is specific to one source, it should remain in that source package.

### `src/gy_crawler/sources/`

Primary home for source-specific crawler logic.

Each source is grouped by platform, then by content type. Examples:

- `facebook/reels`
- `youtube/videos`
- `news/sites`
- `podcast/episodes`

Every new crawler starts here.

### `src/gy_crawler/pipelines/`

Contains orchestration for multi-step workflows:

- collect
- parse
- normalize
- export

This is where source modules are composed into end-to-end runs.

### `src/gy_crawler/storage/`

Contains output and persistence rules:

- file naming
- JSON or JSONL writing
- CSV export
- directory path builders

### `src/gy_crawler/models/`

Contains shared record shapes and normalized data structures, such as:

- `FacebookReelRecord`
- `YouTubeVideoRecord`
- `NewsArticleRecord`
- `PodcastEpisodeRecord`

### `src/gy_crawler/utils/`

Contains only small utility helpers. It should not become a dumping ground for unclear ownership.

## Source Module Template

Each crawler package under `sources/<site>/<content_type>/` should follow a stable internal layout:

```text
cli.py
collector.py
parser.py
models.py
paths.py
```

Responsibilities:

- `cli.py`: source-specific executable entrypoint
- `collector.py`: browser automation, API requests, raw data acquisition
- `parser.py`: convert raw HTML/JSON into structured fields
- `models.py`: source-specific or thin record definitions
- `paths.py`: output folder and filename rules

## Execution Model

Support both modes:

1. direct per-source execution, such as:
   - `python -m gy_crawler.sources.facebook.reels.cli`
2. a future unified CLI, such as:
   - `python -m gy_crawler.cli crawl facebook reels ...`

This gives fast local iteration for one source without blocking a cleaner public interface later.

## Mapping Current Files

Recommended target mapping:

- `facebook_reels_export.py` -> `src/gy_crawler/sources/facebook/reels/cli.py`
- `tests/test_facebook_reels_export.py` -> `tests/unit/facebook/test_reels_cli.py`
- `podcasts.py` -> split into `src/gy_crawler/sources/podcast/...` as appropriate
- `podcast_mp3_all/analyze_mp3_batch.py` -> either:
  - `src/gy_crawler/sources/podcast/episodes/...` if it is part of the productized workflow
  - `scripts/` if it is a one-off operational helper
- `podcast_mp3_all/tests/test_analyze_mp3_batch.py` -> `tests/unit/podcast/...`
- `Untitled.ipynb` -> `notebooks/`

## Git Tracking Policy

Recommended to track in git:

- `src/`
- `tests/`
- `docs/`
- `config/`
- `scripts/`
- `README.md`
- `.gitignore`
- future project metadata such as `pyproject.toml`

Recommended to ignore:

- `output/`
- `data/raw/`
- `data/tmp/`
- `__pycache__/`
- `.ipynb_checkpoints/`
- logs
- downloaded media files
- temporary CSV artifacts

## Repository Rules

To keep the repo from regressing into script sprawl:

1. New crawlers always start under `sources/<site>/<content_type>/`
2. Logic moves into `core/` only when reused by at least two sources
3. Formal project logic should not remain at the repo root
4. Raw/intermediate data and final exports must stay separated
5. The `utils/` directory should stay thin and narrowly scoped

## Incremental Migration Plan

Restructure in small steps:

1. create the new package and test skeleton
2. migrate the Facebook Reels crawler first
3. classify podcast code into product code vs. one-off scripts
4. add `.gitignore` rules and formal project metadata
5. add a unified CLI only after at least two sources share common needs

## Constraints

- The repository has just been initialized and must remain uncommitted until the user decides what should be tracked.
- The structure should support near-term work on Facebook Reels and podcast crawling without forcing immediate rewrites of every historical file.
