import os
import re
import argparse
import subprocess
import requests
import sys
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Default User Agent
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Multi-threaded Twitter Space Downloader.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("playlist_url", help="The URL of the master .m3u8 playlist")
    parser.add_argument("key_url", help="The URL of the decryption key")
    
    parser.add_argument("-c", "--cookie", required=True, help="The auth cookie string")
    parser.add_argument("-o", "--output", default="twitter_space.m4a", help="Output filename")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Number of download threads (default: 20)")
    parser.add_argument("-k", "--keep", action="store_true", help="Keep temporary folder after finishing")
    
    return parser.parse_args()

def download_file_content(url, headers):
    """Downloads file content to memory."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Request failed: {url}\nReason: {e}")
        return None

def download_chunk(url, filepath, headers, index, total):
    """Worker function to download a single chunk."""
    content = download_file_content(url, headers)
    if content:
        with open(filepath, "wb") as f:
            f.write(content)
        return True
    return False

def print_progress(current, total, start_time):
    """Prints a simple progress bar."""
    percent = 100 * (current / float(total))
    elapsed = time.time() - start_time
    rate = current / elapsed if elapsed > 0 else 0
    
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    sys.stdout.write(f'\rProgress: |{bar}| {percent:.1f}% ({current}/{total}) [{rate:.1f} chunks/s]')
    sys.stdout.flush()

def main():
    args = parse_arguments()
    
    # Check FFmpeg
    if shutil.which("ffmpeg") is None:
        print("[ERROR] FFmpeg is not installed or not in PATH.")
        sys.exit(1)

    # Headers
    headers = {
        "User-Agent": DEFAULT_UA,
        "Cookie": args.cookie,
        "Referer": "https://x.com/",
        "Origin": "https://x.com"
    }

    # Setup Temp Directory
    temp_dir = "temp_download_chunks"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    print("[INFO] Fetching Playlist...")
    playlist_content = download_file_content(args.playlist_url, headers).decode('utf-8')
    if not playlist_content:
        sys.exit(1)

    # Calculate Base URL
    base_url = args.playlist_url.rsplit('/', 1)[0] + "/"
    
    # Parse Playlist for Chunks and Key Metadata
    lines = playlist_content.splitlines()
    chunk_urls = []
    chunk_filenames = []
    key_line_index = -1
    
    new_playlist_lines = []
    
    print("[INFO] Parsing segments...")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXT-X-KEY"):
            # Download the Key
            print("[INFO] Downloading Decryption Key...")
            key_content = download_file_content(args.key_url, headers)
            if not key_content:
                print("[ERROR] Could not download key. Check your cookies.")
                sys.exit(1)
            
            # Save Key Locally
            local_key_path = os.path.join(temp_dir, "enc.key")
            with open(local_key_path, "wb") as f:
                f.write(key_content)
                
            # Update Playlist Line to point to local key
            # We use a regex to preserve the IV if it exists
            new_line = re.sub(r'URI="[^"]+"', f'URI="enc.key"', line)
            new_playlist_lines.append(new_line)
            
        elif line.startswith("#") and not line.startswith("#EXTINF"):
            new_playlist_lines.append(line)
            
        elif line.startswith("#EXTINF"):
            new_playlist_lines.append(line)
            
        else:
            # This is a chunk URL
            if line.startswith("http"):
                full_url = line
            else:
                full_url = base_url + line
            
            # Generate local filename (0001.aac, 0002.aac, etc. to keep order)
            local_filename = f"{len(chunk_urls):05d}.aac"
            local_filepath = os.path.join(temp_dir, local_filename)
            
            chunk_urls.append((full_url, local_filepath))
            chunk_filenames.append(local_filename)
            new_playlist_lines.append(local_filename)

    # Write the new local playlist
    local_playlist_path = os.path.join(temp_dir, "local.m3u8")
    with open(local_playlist_path, "w") as f:
        f.write("\n".join(new_playlist_lines))

    print(f"[INFO] Found {len(chunk_urls)} audio chunks.")
    print(f"[INFO] Starting download with {args.threads} threads...")

    # Multi-threaded Download
    start_time = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for index, (url, path) in enumerate(chunk_urls):
            futures.append(executor.submit(download_chunk, url, path, headers, index, len(chunk_urls)))
            
        for future in as_completed(futures):
            if future.result():
                completed += 1
                print_progress(completed, len(chunk_urls), start_time)
            else:
                print("\n[ERROR] A chunk failed to download.")
    
    print(f"\n[INFO] Download finished in {time.time() - start_time:.2f}s")

    # FFmpeg Stitching
    print(f"[INFO] Stitching files into {args.output}...")
    
    # FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",
        "-allowed_extensions", "ALL",
        "-protocol_whitelist", "file,crypto,data",
        "-i", local_playlist_path,
        "-c", "copy",
        args.output,
        "-v", "error",
        "-stats"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Saved: {args.output}")
    except subprocess.CalledProcessError:
        print("\n[ERROR] FFmpeg stitching failed.")
    
    # Cleanup
    if not args.keep:
        shutil.rmtree(temp_dir)
        print("[INFO] Temp files cleaned up.")

if __name__ == "__main__":
    main()
