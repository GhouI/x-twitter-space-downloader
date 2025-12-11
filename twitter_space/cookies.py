import json
import os


def load_cookies_from_file(filepath="cookies.json"):
    """Load cookies from a JSON file that may be a list or dictionary export."""
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r") as file_handle:
            data = json.load(file_handle)

        cookie_parts = []

        if isinstance(data, list):
            for cookie in data:
                if isinstance(cookie, dict):
                    name = cookie.get("name")
                    value = cookie.get("value")
                    if name and value is not None:
                        cookie_parts.append(f"{name}={value}")
        elif isinstance(data, dict):
            for name, value in data.items():
                if value is not None:
                    cookie_parts.append(f"{name}={value}")

        if not cookie_parts:
            print(f"[WARN] {filepath} appears to be empty or invalid.")
            return None

        cookie_string = "; ".join(cookie_parts)
        print(f"[INFO] Automatically loaded {len(cookie_parts)} cookies from {filepath}")
        return cookie_string

    except json.JSONDecodeError:
        print(f"[ERROR] {filepath} is not valid JSON.")
        return None
    except Exception as exc:
        print(f"[ERROR] Error reading {filepath}: {exc}")
        return None
