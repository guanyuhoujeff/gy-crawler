# gy-crawler

Multi-source crawler workspace for Facebook Reels, podcast feeds, and future YouTube/news crawlers.

## Layout

```text
src/gy_crawler/
  cli/
  sources/
    facebook/reels/
    podcast/feeds/
    podcast/episodes/
tests/
docs/
scripts/
notebooks/
output/
```

## Setup

```bash
conda create -n gy-crawler python=3.12 -y
conda activate gy-crawler
pip install -e .
python -m playwright install chromium
```

## Commands

Facebook Reels:

```bash
python scripts/facebook_reels_export.py \
  --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" \
  --limit 10 \
  --output-root output
```

Facebook login session bootstrap:

```bash
python3 scripts/facebook_login_session.py \
  --storage-state .secrets/facebook-state.json \
  --headed
```

Facebook Reels all visible crawl:

```bash
python3 scripts/facebook_reels_export.py \
  --profile-url "https://www.facebook.com/imoneytalkalex/reels/" \
  --storage-state .secrets/facebook-state.json \
  --all-visible \
  --max-idle-scrolls 5 \
  --delay-seconds 2 \
  --output-root output
```


```bash
python -m gy_crawler.sources.facebook.reels.cli \
  --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab" \
  --limit 10 \
  --output-root output
```

Unified CLI:

```bash
python -m gy_crawler.cli.main crawl facebook reels \
  --profile-url "https://www.facebook.com/profile.php?id=100070097403579&sk=reels_tab"
```

Podcast episode analyzer:

```bash
python -m gy_crawler.sources.podcast.episodes.analyzer \
  --input-dir data/raw/podcast/episodes/audio \
  --output-dir data/processed/podcast/episode_analysis/markdown
```

Podcast feed downloader:

```bash
python scripts/podcast_feed_download.py \
  --rss-url "https://feed.firstory.me/rss/user/ckgt4pmfa3cjt0812r7uko63o" \
  --output-dir data/raw/podcast/episodes/audio
```

## Tests

```bash
python -m unittest tests.unit.facebook.test_reels_cli tests.unit.podcast.test_episode_analyzer tests.unit.test_cli_main -v
```
