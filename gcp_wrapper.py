#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GCP Wrapper Script
Handles state persistence with Google Cloud Storage (GCS).
Downloads state -> Runs Command -> Uploads state.
"""

import os
import sys
import subprocess
from google.cloud import storage

BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
STATE_FILES = ["strategy_state.yaml", "nl_lotto_xl_history.csv", "config.yaml"]
PREDICTIONS_DIR = "predictions"

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        if blob.exists():
            blob.download_to_filename(destination_file_name)
            print(f"Downloaded {source_blob_name} to {destination_file_name}.")
        else:
            print(f"Blob {source_blob_name} does not exist. Skipping.")
    except Exception as e:
        print(f"Error downloading {source_blob_name}: {e}")

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        print(f"Uploaded {source_file_name} to {destination_blob_name}.")
    except Exception as e:
        print(f"Error uploading {source_file_name}: {e}")

def sync_down():
    """Download all state files from GCS."""
    if not BUCKET_NAME:
        print("GCS_BUCKET_NAME not set. Skipping sync.")
        return

    print("--- Syncing DOWN from GCS ---")
    for f in STATE_FILES:
        download_blob(BUCKET_NAME, f, f)
    
    # Also sync predictions folder if needed (optional, but good for history)
    # For simplicity, we might skip full folder sync or implement it if needed.

def sync_up():
    """Upload all state files and new predictions to GCS."""
    if not BUCKET_NAME:
        return

    print("--- Syncing UP to GCS ---")
    for f in STATE_FILES:
        if os.path.exists(f):
            upload_blob(BUCKET_NAME, f, f)
            
    # Upload predictions
    if os.path.exists(PREDICTIONS_DIR):
        for root, dirs, files in os.walk(PREDICTIONS_DIR):
            for file in files:
                local_path = os.path.join(root, file)
                # Upload if it's new (naive check: just upload everything, GCS handles overwrite)
                upload_blob(BUCKET_NAME, local_path, local_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: python gcp_wrapper.py <script_to_run> [args...]")
        sys.exit(1)

    script = sys.argv[1]
    args = sys.argv[2:]

    # 1. Download State
    sync_down()

    # 2. Run Script
    print(f"--- Running {script} ---")
    result = subprocess.run([sys.executable, script] + args)
    
    # 3. Upload State (only if success)
    if result.returncode == 0:
        sync_up()
    else:
        print("Script failed. Skipping upload to prevent state corruption.")
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
