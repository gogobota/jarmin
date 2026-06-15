import os
import sys
import subprocess
import urllib.request
from pathlib import Path

def get_remote_md5(url):
    """Fetch the MD5 hash from the official OSM planet mirror."""
    md5_url = url + ".md5"
    print(f"Fetching expected MD5 from {md5_url}...")
    try:
        with urllib.request.urlopen(md5_url) as response:
            data = response.read().decode('utf-8').strip()
            # The format is usually "hash  filename"
            expected_md5 = data.split()[0]
            return expected_md5
    except Exception as e:
        print(f"Warning: Could not fetch MD5 from {md5_url}. Error: {e}")
        return None

def verify_md5(filepath, expected_md5):
    """Verify the MD5 hash of the local file."""
    print(f"Verifying MD5 hash of {filepath}...")
    # Using the system's md5/md5sum command is much faster for a 90GB file than doing it in pure Python
    if sys.platform == "darwin":
        cmd = ["md5", "-q", str(filepath)]
    else:
        cmd = ["md5sum", str(filepath)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        local_md5 = result.stdout.strip().split()[0]
        if local_md5 == expected_md5:
            print("MD5 hash matches! File integrity verified.")
            return True
        else:
            print(f"MD5 hash mismatch! Expected: {expected_md5}, Got: {local_md5}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error calculating MD5: {e}")
        return False

def download_planet(url, dest_path):
    """
    Download the planet file using curl with resuming enabled.
    Validates MD5 upon completion.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    expected_md5 = get_remote_md5(url)
    
    if dest_path.exists():
        print(f"Found existing file at {dest_path}.")
        if expected_md5:
            if verify_md5(dest_path, expected_md5):
                print("Existing file is complete and verified. Skipping download.")
                return True
            else:
                print("Existing file is incomplete or corrupted. Resuming/Restarting download...")
        else:
            print("Could not fetch remote MD5 to verify existing file. Proceeding with curl resume to check completion...")

    print(f"Downloading (or resuming) {url} to {dest_path} using curl...")
    cmd = [
        "curl",
        "--fail",
        "--location",
        "--continue-at", "-", # Resume if file exists
        "--output", str(dest_path),
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Download finished.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading file: curl exited with status {e.returncode}")
        return False

    if expected_md5:
        return verify_md5(dest_path, expected_md5)
    else:
        print("Skipping final MD5 verification because remote hash could not be retrieved.")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 downloader.py <url> <destination_path>")
        sys.exit(1)
    
    url = sys.argv[1]
    dest = sys.argv[2]
    
    success = download_planet(url, dest)
    if not success:
        sys.exit(1)
