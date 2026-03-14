import argparse

from gy_crawler.sources.facebook.reels import cli as facebook_reels_cli


def build_parser():
    parser = argparse.ArgumentParser(prog="gy-crawler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl_parser = subparsers.add_parser("crawl")
    crawl_subparsers = crawl_parser.add_subparsers(dest="source", required=True)

    facebook_parser = crawl_subparsers.add_parser("facebook")
    facebook_subparsers = facebook_parser.add_subparsers(dest="content_type", required=True)

    facebook_subparsers.add_parser("reels")
    return parser


def main(argv=None):
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command == "crawl" and args.source == "facebook" and args.content_type == "reels":
        return facebook_reels_cli.main(remaining)

    parser.error("Unsupported command")
