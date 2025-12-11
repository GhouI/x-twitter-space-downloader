import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .constants import PROGRESS_BAR_LENGTH
from .network import download_file_content


def download_chunk(job, headers):
    """Download a single chunk to disk."""
    url, filepath = job
    content = download_file_content(url, headers)
    if content:
        with open(filepath, "wb") as file_handle:
            file_handle.write(content)
        return True
    return False


def print_progress(current, total, start_time):
    """Render a simple progress bar."""
    percent = 100 * (current / float(total))
    elapsed = time.time() - start_time
    rate = current / elapsed if elapsed > 0 else 0

    filled_length = int(PROGRESS_BAR_LENGTH * current // total)
    bar = "█" * filled_length + "-" * (PROGRESS_BAR_LENGTH - filled_length)

    sys.stdout.write(
        f"\rProgress: |{bar}| {percent:.1f}% ({current}/{total}) [{rate:.1f} chunks/s]"
    )
    sys.stdout.flush()


def download_chunks(chunk_jobs, headers, threads):
    """Download all chunks concurrently."""
    print(f"[INFO] Starting download with {threads} threads...")
    start_time = time.time()
    completed = 0
    failures = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(download_chunk, job, headers) for job in chunk_jobs
        ]

        for future in as_completed(futures):
            if future.result():
                completed += 1
                print_progress(completed, len(chunk_jobs), start_time)
            else:
                failures += 1
                print("\n[ERROR] A chunk failed to download.")

    print(f"\n[INFO] Download finished in {time.time() - start_time:.2f}s")
    return failures == 0
