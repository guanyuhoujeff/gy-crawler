import argparse
import json
import sys
from pathlib import Path

from .collector import PlaywrightFacebookCollector, collect_visible_reels
from .downloader import download_reel
from .models import build_reel_payload
from .paths import build_account_directory_name, extract_reel_id


def build_storage_state_refresh_message(storage_state_path):
    return (
        "Rerun the login bootstrap to refresh the saved Facebook session:\n"
        f"python3 scripts/facebook_login_session.py --storage-state {storage_state_path} --headed"
    )


def write_payload(output_dir, payload):
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{payload['content_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_reels(
    profile_url,
    output_root,
    limit,
    all_visible,
    collector,
    collected_at=None,
    scroll=True,
    max_scrolls=10,
    max_idle_scrolls=2,
    download=False,
    cookies_from_browser=None,
):
    profile = collector.collect_profile(
        profile_url,
        limit,
        all_visible=all_visible,
        scroll=scroll,
        max_scrolls=max_scrolls,
        max_idle_scrolls=max_idle_scrolls,
    )
    output_dir = Path(output_root) / build_account_directory_name(profile["account_name"])
    summary = {"discovered": len(profile["reels"]), "written": 0, "failed": 0, "downloaded": 0, "download_failed": 0}

    for reel in profile["reels"]:
        try:
            detail = collector.collect_reel_detail(reel["reel_url"])
        except Exception as exc:  # noqa: BLE001
            detail = {
                "published_time": None,
                "published_time_iso": None,
                "caption": None,
                "warnings": [f"Detail extraction failed: {exc}"],
            }
            summary["failed"] += 1

        payload = build_reel_payload(
            account_name=profile["account_name"],
            source_profile_url=profile["source_profile_url"],
            reel_url=reel["reel_url"],
            view_count_visible=reel.get("view_count_visible"),
            detail=detail,
            collected_at=collected_at,
        )
        write_payload(output_dir, payload)
        summary["written"] += 1

        if download:
            reel_id = extract_reel_id(reel["reel_url"])
            try:
                result = download_reel(
                    reel_url=reel["reel_url"],
                    output_dir=output_dir,
                    reel_id=reel_id,
                    cookies_from_browser=cookies_from_browser,
                )
                if result:
                    summary["downloaded"] += 1
                    print(f"  downloaded {result.name}")
                else:
                    summary["download_failed"] += 1
                    print(f"  download returned no file for reel {reel_id}", file=sys.stderr)
            except Exception as exc:  # noqa: BLE001
                summary["download_failed"] += 1
                print(f"  download failed for reel {reel_id}: {exc}", file=sys.stderr)

    return summary, output_dir


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-url", required=True)
    parser.add_argument("--output-root", default="raw_file_output/fb_reels")
    parser.add_argument("--storage-state")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--limit", type=int)
    mode_group.add_argument(
        "--all-visible",
        action="store_true",
        help="Scroll until the reels page stops surfacing new visible reels",
    )
    parser.set_defaults(scroll=True)
    parser.add_argument(
        "--no-scroll",
        dest="scroll",
        action="store_false",
        help="Disable scrolling and only collect currently loaded reels",
    )
    parser.add_argument("--max-scrolls", type=int, default=10)
    parser.add_argument("--max-idle-scrolls", type=int, default=2)
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window")
    parser.add_argument("--delay-seconds", type=float, default=1.5)
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download reel videos via yt-dlp after collecting metadata",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to extract cookies from for yt-dlp (e.g. chrome, firefox)",
    )
    args = parser.parse_args(argv)
    if not args.all_visible and args.limit is None:
        args.limit = 10
    return args


def main(argv=None, collector=None, collected_at=None):
    args = parse_args(argv)
    managed_collector = collector
    storage_state_path = None

    if args.storage_state:
        storage_state_path = Path(args.storage_state)
        if not storage_state_path.is_file():
            print(
                (
                    f"Storage state file not found: {storage_state_path}\n"
                    f"{build_storage_state_refresh_message(storage_state_path)}"
                ),
                file=sys.stderr,
            )
            return 1

    try:
        if managed_collector is None:
            managed_collector = PlaywrightFacebookCollector(
                headless=not args.headed,
                delay_seconds=args.delay_seconds,
                storage_state_path=str(storage_state_path) if storage_state_path else None,
            ).__enter__()

        summary, output_dir = export_reels(
            profile_url=args.profile_url,
            output_root=args.output_root,
            limit=args.limit,
            all_visible=args.all_visible,
            collector=managed_collector,
            collected_at=collected_at,
            scroll=args.scroll,
            max_scrolls=args.max_scrolls,
            max_idle_scrolls=args.max_idle_scrolls,
            download=args.download,
            cookies_from_browser=args.cookies_from_browser,
        )
    except Exception as exc:  # noqa: BLE001
        if storage_state_path is not None:
            print(
                (
                    f"{exc}\n"
                    "The saved Facebook session may be expired.\n"
                    f"{build_storage_state_refresh_message(storage_state_path)}"
                ),
                file=sys.stderr,
            )
        else:
            print(str(exc), file=sys.stderr)
        return 1
    finally:
        if collector is None and managed_collector is not None:
            managed_collector.__exit__(None, None, None)

    parts = ["discovered={discovered}", "written={written}", "failed={failed}"]
    if args.download:
        parts.extend(["downloaded={downloaded}", "download_failed={download_failed}"])
    parts.append("output_dir={output_dir}")
    print(
        " ".join(parts).format(output_dir=output_dir, **summary)
    )
    return 0 if summary["written"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
