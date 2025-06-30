#!/usr/bin/env python3
"""
Start file scanning Celery worker
"""

import subprocess
import sys

def start_file_scanning_worker():
    cmd = [
        "celery", "-A", "univy.celery_config.celery_univy",
        "worker",
        "--queues=file_scanning",
        "--concurrency=4",
        "--loglevel=info",
        "--hostname=worker_file_scanning@%h",
        "--pool=prefork"
    ]
    
    print("Starting file scanning worker...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopping file scanning worker...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting file scanning worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_file_scanning_worker() 