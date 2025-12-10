import os
import re
import argparse
import subprocess
import requests
import sys
import shutil

# Default User Agent to mimic a real browser
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Download Twitter/X Spaces (even protected ones) using a Playlist and Key.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("playlist_url", help="The URL of the master .m3u8 playlist")
    parser.add_argument("key_url", help="The URL of the decryption key (ends in /key?stream_name=...)")
    
    parser.add_argument("-c", "--cookie", required=True, help="The auth cookie string (Use the helper script to get this!)")
    parser.add_argument("-o", "--output", default="twitter_space.m4a", help="Output filename (default: twitter_space.m4a)")
    parser.add_argument("-k", "--keep", action="store_true", help="Keep temporary files (enc.key and playlist) after finishing")
    
    return parser.parse_args()

def download_file(url, filename, headers):
    """Downloads a file from a URL and saves it locally."""
    print(f"[INFO] Downloading {filename}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"[OK] Saved {filename}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download {filename}.")
        print(f"       Server replied: {e}")
        print("       (Check your Cookie string and ensure the Space is still available)")
        sys.exit(1)

def fix_playlist(playlist_path, key_filename, original_playlist_url):
    """
    Edits the .m3u8 file to link the local key and absolute remote chunk URLs.
    """
    print("[INFO] Patching playlist to use local key and remote audio...")
    
    # Calculate base URL for audio chunks (remove filename from the end of the URL)
    base_url = original_playlist_url.rsplit('/', 1)[0] + "/"
    
    with open(playlist_path, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        stripped = line.strip()
        
        # 1. Point Key to local file
        if stripped.startswith("#EXT-X-KEY"):
            # Use Regex to replace URI="..." with URI="enc.key"
            new_line = re.sub(r'URI="[^"]+"', f'URI="{key_filename}"', line)
            new_lines.append(new_line)
            
        # 2. Point Audio Chunks to remote URL (if they aren't already absolute)
        elif stripped and not stripped.startswith("#"):
            if not stripped.startswith("http"):
                new_lines.append(base_url + stripped + "\n")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(playlist_path, "w") as f:
        f.writelines(new_lines)

def run_ffmpeg(playlist_path, output_path):
    """Runs FFmpeg to merge the stream."""
    print(f"[INFO] Starting FFmpeg processing -> {output_path}")
    print("       (This may take time depending on internet speed and space duration...)")
    
    # Check if ffmpeg exists
    if shutil.which("ffmpeg") is None:
        print("[ERROR] 'ffmpeg' is not found in your PATH.")
        print("        Please install FFmpeg to use this tool.")
        sys.exit(1)

    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-v", "warning", # Less verbose output
        "-stats", # Show progress
        "-allowed_extensions", "ALL",
        "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
        "-i", playlist_path,
        "-c", "copy",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Download complete! File saved as: {output_path}")
    except subprocess.CalledProcessError:
        print("\n[ERROR] FFmpeg failed. This usually means the Key file is invalid/empty.")
        print("        Check if your 'Cookie' was correct when downloading the key.")

def main():
    args = parse_arguments()
    
    # Internal temp filenames
    temp_playlist = "temp_playlist.m3u8"
    temp_key = "enc.key"
    
    # Headers for requests
    headers = {
        "User-Agent": DEFAULT_UA,
        "Cookie": args.cookie,
        "Referer": "https://x.com/",
        "Origin": "https://x.com"
    }

    # 1. Download Key
    download_file(args.key_url, temp_key, headers)
    
    # 2. Download Playlist
    download_file(args.playlist_url, temp_playlist, headers)
    
    # 3. Fix Playlist
    fix_playlist(temp_playlist, temp_key, args.playlist_url)
    
    # 4. Process with FFmpeg
    run_ffmpeg(temp_playlist, args.output)
    
    # Cleanup
    if not args.keep:
        try:
            if os.path.exists(temp_playlist): os.remove(temp_playlist)
            if os.path.exists(temp_key): os.remove(temp_key)
            print("[INFO] Temporary files cleaned up.")
        except OSError:
            pass
    else:
        print(f"[INFO] kept temp files: {temp_playlist}, {temp_key}")

if __name__ == "__main__":
    main()
