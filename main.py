import os
import re
import shutil
import sys

from twitter_space.cli import interactive_mode, parse_arguments
from twitter_space.constants import DEFAULT_UA, TEMP_DIR
from twitter_space.cookies import load_cookies_from_file
from twitter_space.downloader import download_chunks
from twitter_space.ffmpeg_runner import stitch_audio
from twitter_space.playlist import clean_playlist_url, prepare_playlist


def resolve_cookie_argument(cookie_arg):
    """Resolve a cookie argument that may be a JSON path."""
    if not cookie_arg:
        return None
    if cookie_arg.endswith(".json") and os.path.exists(cookie_arg):
        loaded_cookie = load_cookies_from_file(cookie_arg)
        return loaded_cookie or cookie_arg
    return cookie_arg


def ensure_ffmpeg_available():
    """Validate that FFmpeg is available before downloading."""
    if shutil.which("ffmpeg") is None:
        print("[ERROR] FFmpeg is not installed or not in PATH.")
        sys.exit(1)


def build_headers(cookie_string):
    """Construct request headers, including CSRF token when present."""
    csrf_token = ""
    match = re.search(r"ct0=([^;]+)", cookie_string or "")
    if match:
        csrf_token = match.group(1).strip()

    headers = {
        "User-Agent": DEFAULT_UA,
        "Cookie": cookie_string,
        "Referer": "https://x.com/",
        "Origin": "https://x.com",
    }

    if csrf_token:
        headers["x-csrf-token"] = csrf_token

    return headers


def prepare_args():
    """Handle interactive vs non-interactive argument collection."""
    args = parse_arguments()

    if args.interactive:
        return interactive_mode(args)

    args.cookie = resolve_cookie_argument(args.cookie)
    if not args.cookie:
        args.cookie = load_cookies_from_file("cookies.json")

    if not args.playlist_url or not args.key_url or not args.cookie:
        print("[ERROR] Missing arguments.")
        print(
            "Usage: python main.py [PLAYLIST_URL] [KEY_URL] -c [COOKIE_OR_JSON_PATH]"
        )
        print("OR use interactive mode: python main.py -cli")
        sys.exit(1)

    return args


def main():
    args = prepare_args()
    args.playlist_url = clean_playlist_url(args.playlist_url)

    ensure_ffmpeg_available()
    headers = build_headers(args.cookie)

    try:
        chunk_jobs, local_playlist_path = prepare_playlist(
            args.playlist_url, args.key_url, headers, TEMP_DIR
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    downloads_ok = download_chunks(chunk_jobs, headers, args.threads)
    if not downloads_ok:
        sys.exit(1)

    try:
        stitch_audio(local_playlist_path, args.output)
        print(f"\n[SUCCESS] Saved: {args.output}")
    except RuntimeError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)

    if not args.keep:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        print("[INFO] Temp files cleaned up.")


if __name__ == "__main__":
    main()
