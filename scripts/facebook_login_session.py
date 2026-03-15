from pathlib import Path
import sys
import argparse

from playwright.sync_api import sync_playwright


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _bootstrap import ensure_repo_src_on_path


ensure_repo_src_on_path()


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.set_defaults(headed=True)
    parser.add_argument(
        "--storage-state",
        required=True,
        help="Path to write the saved Playwright storage state JSON file",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with a visible browser window",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    storage_state_path = Path(args.storage_state)
    storage_state_path.parent.mkdir(parents=True, exist_ok=True)

    playwright = sync_playwright().start()
    browser = None
    context = None

    try:
        browser = playwright.chromium.launch(headless=not args.headed)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        print("Complete Facebook login in the opened browser, then press Enter here to save the session.")
        input()
        context.storage_state(path=str(storage_state_path))
    finally:
        if context is not None:
            context.close()
        if browser is not None:
            browser.close()
        playwright.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
