import subprocess


def stitch_audio(local_playlist_path, output_path):
    """Invoke FFmpeg to stitch audio chunks together."""
    cmd = [
        "ffmpeg",
        "-y",
        "-allowed_extensions",
        "ALL",
        "-protocol_whitelist",
        "file,crypto,data",
        "-i",
        local_playlist_path,
        "-c",
        "copy",
        output_path,
        "-v",
        "error",
        "-stats",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("FFmpeg stitching failed.") from exc
