import requests


def download_file_content(url, headers, timeout=10):
    """Download a remote resource to memory."""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as exc:
        print(f"\n[ERROR] Request failed: {url}\nReason: {exc}")
        return None
