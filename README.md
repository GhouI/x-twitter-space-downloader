# Twitter Space Downloader

A robust tool to download encrypted Twitter (X) Spaces using Python and FFmpeg. This tool automatically handles the complex process of linking local decryption keys with remote audio chunks. This works for subscription (Super Follow) Spaces as well.

## How It Works

- Accepts the playlist URL (.m3u8), decryption key URL, and auth cookies (string or `cookies.json`).
- Normalizes wrapper URLs, fetches the playlist, and rewrites it to point to locally saved encryption keys and chunk files.
- Downloads chunks concurrently for speed, reporting progress as it goes.
- Hands the local playlist to FFmpeg to stitch all segments into a single `.m4a` file.
- Cleans up the temporary chunk folder unless you opt to keep it.

## Requirements

1. **Python 3**: [Download Here](https://www.python.org/downloads/)
2. **FFmpeg**: Must be installed and accessible in your terminal.
   - Windows: `winget install ffmpeg`
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
3. **Python Libraries**:
```bash
pip install requests
```

## Quick Start Guide

### Step 1: Get Authentication Cookies

You need your specific session cookies to download the decryption key.

1. Install the Cookie-Editor extension for your browser: [Chrome Web Store Link](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
2. Go to Twitter/X.
3. Open the extension and find the values for:
   - `auth_token`
   - `ct0`
4. Save these strings; you will need them for the command in Step 3.

### Step 2: Get the URLs (Playlist & Key)

1. Open the Twitter Space in your browser.
2. Press F12 to open Developer Tools and click the Console tab.
3. Paste the contents of `browser_help.js` (provided with this tool) and hit Enter.
4. Refresh the page or click "Play" on the Space.
5. Look at the Console. The script will highlight the URLs in Green (Playlist) and Cyan (Key) as they appear.
   - **Note**: If they don't appear immediately, try scrubbing/seeking through the audio timeline.

### Step 3: Provide Cookies (where to place `cookies.json`)

- Preferred: Save a file named `cookies.json` in the project root (same folder as `main.py`). It can be the Cookie-Editor export (list of objects) or a simple dictionary of key-value pairs. The program auto-loads it if `-c` is not supplied.
- Optional: Keep a separate cookie export elsewhere and pass its path with `-c path/to/cookies.json`.
- Alternative: Paste the raw string directly with `-c "auth_token=...; ct0=...; other_cookie=..."`.

### Step 4: Run the Command

Construct your command using the data from Steps 1 & 2:
```bash
python main.py "PASTE_PLAYLIST_URL_HERE" "PASTE_KEY_URL_HERE" -c "auth_token=PASTE_TOKEN_HERE; ct0=PASTE_CT0_HERE"
```

To run interactively (prompts for inputs):
```bash
python main.py -cli
```

## Troubleshooting

### FFmpeg Error: "Invalid data found"

- This usually means the Key file (`enc.key`) is empty or contains an error message (like "Unauthorized").
- **Fix**: Ensure you copied the full cookie string correctly (`auth_token` and `ct0`).

### "403 Forbidden"

- Your cookies might have expired, or the Space has ended and is no longer available.
- **Fix**: Refresh the Twitter page and grab the new `auth_token` and `ct0`.

### Windows "ffmpeg is not recognized"

- You installed FFmpeg but didn't restart your terminal, or you didn't add it to your System PATH.

## FAQ

- **Where do I put `cookies.json`?**
  - Place it in the same directory as `main.py` so it is auto-loaded. You can also pass a custom path with `-c path/to/cookies.json`.

- **How do I supply cookies without a file?**
  - Pass the raw string:  
    `python main.py "PLAYLIST" "KEY" -c "auth_token=...; ct0=..."`

- **Can I keep the downloaded chunks for debugging?**
  - Yes: add `-k` to keep the `temp_download_chunks` folder. Example:  
    `python main.py "PLAYLIST" "KEY" -c cookies.json -k`

- **How do I adjust speed vs. network load?**
  - Change thread count: `-t 10` (slower) or `-t 40` (faster if your connection and host allow). Example:  
    `python main.py "PLAYLIST" "KEY" -c cookies.json -t 30`

- **I pasted the playlist URL as the key by mistake. What happens?**
  - The tool will detect if the key response looks like a playlist and exit with a clear error. Grab the correct key URL from DevTools and rerun.

- **The Space is long; how large is the file?**
  - Expect roughly 1 MB per minute for typical mono AAC streams. A 60-minute Space is usually around 60–70 MB.

- **Do I need to rerun everything if a few chunks fail?**
  - Yes, rerun the command. If failures persist, lower `-t` or ensure your connection is stable.
