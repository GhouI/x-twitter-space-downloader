import os
import re
import shutil
import urllib.parse

from .constants import KEY_FILENAME, LOCAL_PLAYLIST_NAME, TEMP_DIR
from .network import download_file_content


def clean_playlist_url(url):
    """Extract the real .m3u8 URL when an authorized_status wrapper is provided."""
    if "authorized_status" in url and "url=" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            query_string = urllib.parse.parse_qs(parsed.query)
            if "url" in query_string:
                real_url = query_string["url"][0]
                print("[INFO] Detected API wrapper URL. Extracting real playlist URL...")
                return real_url
        except Exception as exc:
            print(f"[WARN] Tried to parse wrapper URL but failed: {exc}")
            return url
    return url


def _ensure_temp_dir(temp_dir):
    """Reset the temp directory to a clean state."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)


def prepare_playlist(playlist_url, key_url, headers, temp_dir=TEMP_DIR):
    """Download the remote playlist, rewrite references, and return chunk jobs."""
    _ensure_temp_dir(temp_dir)

    print("[INFO] Fetching Playlist...")
    content_raw = download_file_content(playlist_url, headers)
    if not content_raw:
        raise ValueError("Failed to download playlist.")

    playlist_content = content_raw.decode("utf-8")
    base_url = playlist_url.rsplit("/", 1)[0] + "/"
    lines = playlist_content.splitlines()
    chunk_jobs = []
    new_playlist_lines = []

    print("[INFO] Parsing segments...")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXT-X-KEY"):
            print(f"[INFO] Downloading Decryption Key from: {key_url}")
            key_content = download_file_content(key_url, headers)
            if not key_content:
                raise ValueError("Could not download key. Check your cookies.")

            if key_content.startswith(b"#EXTM3U"):
                raise ValueError(
                    "Key URL returned a playlist file. Use the correct decryption key URL."
                )

            if len(key_content) != 16:
                print("\n[CRITICAL ERROR] Invalid Key File Downloaded!")
                print(f"Expected 16 bytes, but got {len(key_content)} bytes.")
                try:
                    print(f"Content preview: {key_content.decode('utf-8')[:100]}")
                except Exception:
                    print(f"Content preview (hex): {key_content.hex()[:20]}...")
                raise ValueError("Twitter rejected your cookies. Please refresh them.")

            local_key_path = os.path.join(temp_dir, KEY_FILENAME)
            with open(local_key_path, "wb") as file_handle:
                file_handle.write(key_content)

            new_line = re.sub(r'URI="[^"]+"', f'URI="{KEY_FILENAME}"', line)
            new_playlist_lines.append(new_line)
        elif line.startswith("#") and not line.startswith("#EXTINF"):
            new_playlist_lines.append(line)
        elif line.startswith("#EXTINF"):
            new_playlist_lines.append(line)
        else:
            full_url = line if line.startswith("http") else base_url + line
            local_filename = f"{len(chunk_jobs):05d}.aac"
            local_filepath = os.path.join(temp_dir, local_filename)
            chunk_jobs.append((full_url, local_filepath))
            new_playlist_lines.append(local_filename)

    local_playlist_path = os.path.join(temp_dir, LOCAL_PLAYLIST_NAME)
    with open(local_playlist_path, "w") as file_handle:
        file_handle.write("\n".join(new_playlist_lines))

    print(f"[INFO] Found {len(chunk_jobs)} audio chunks.")
    return chunk_jobs, local_playlist_path
