import argparse
import os

from .cookies import load_cookies_from_file


def parse_arguments():
    """Parse CLI arguments for the downloader."""
    parser = argparse.ArgumentParser(
        description="Multi-threaded Twitter Space Downloader.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "playlist_url", nargs="?", help="The URL of the master .m3u8 playlist"
    )
    parser.add_argument("key_url", nargs="?", help="The URL of the decryption key")
    parser.add_argument(
        "-c", "--cookie", help="The auth cookie string (or path to json)"
    )
    parser.add_argument(
        "-o", "--output", default="twitter_space.m4a", help="Output filename"
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=20,
        help="Number of download threads (default: 20)",
    )
    parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        help="Keep temporary folder after finishing",
    )
    parser.add_argument(
        "-cli",
        "--interactive",
        action="store_true",
        help="Run in interactive mode (prompt for inputs)",
    )

    return parser.parse_args()


def interactive_mode(args):
    """Collect required inputs interactively."""
    print("\n--- Interactive Mode ---")

    if not args.playlist_url:
        args.playlist_url = input("Enter Playlist URL (.m3u8): ").strip()
        while not args.playlist_url:
            print("Playlist URL is required.")
            args.playlist_url = input("Enter Playlist URL (.m3u8): ").strip()

    if not args.key_url:
        args.key_url = input("Enter Key URL: ").strip()
        while not args.key_url:
            if ".m3u8" in args.key_url:
                print(
                    "[WARN] You pasted a Playlist URL (.m3u8) into the Key URL field!"
                )
                confirm = input("Are you sure? (y/n): ")
                if confirm.lower() != "y":
                    args.key_url = ""
                    continue

            if not args.key_url:
                print("Key URL is required.")
                args.key_url = input("Enter Key URL: ").strip()

    if not args.cookie:
        args.cookie = load_cookies_from_file("cookies.json")
        if not args.cookie:
            print("\nCookies not found in 'cookies.json'.")
            print(
                "Option A: Paste the path to your json file (e.g., 'my_cookies.json')"
            )
            print("Option B: Paste the raw cookie string (auth_token=...; ct0=...)")
            user_input = input("> ").strip()

            if user_input.endswith(".json") and os.path.exists(user_input):
                args.cookie = load_cookies_from_file(user_input)
            else:
                if user_input.startswith('"') and user_input.endswith('"'):
                    user_input = user_input[1:-1]
                args.cookie = user_input

            while not args.cookie:
                print("Cookie string (or valid json file) is required.")
                user_input = input("> ").strip()
                if user_input.endswith(".json") and os.path.exists(user_input):
                    args.cookie = load_cookies_from_file(user_input)
                else:
                    if user_input.startswith('"') and user_input.endswith('"'):
                        user_input = user_input[1:-1]
                    args.cookie = user_input
    else:
        if args.cookie.endswith(".json") and os.path.exists(args.cookie):
            loaded_cookie = load_cookies_from_file(args.cookie)
            args.cookie = loaded_cookie or args.cookie

    new_output = input(f"Output Filename [default: {args.output}]: ").strip()
    if new_output:
        args.output = new_output
        if not args.output.endswith(".m4a"):
            args.output += ".m4a"

    print("\n------------------------")
    return args
