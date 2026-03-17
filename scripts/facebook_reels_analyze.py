from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _bootstrap import ensure_repo_src_on_path


ensure_repo_src_on_path()

from gy_crawler.sources.facebook.reels.analyzer import main


if __name__ == "__main__":
    raise SystemExit(main())
