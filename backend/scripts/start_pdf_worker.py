#!/usr/bin/env python3
"""
Start PDF processing Celery worker
"""

import subprocess
import sys

def start_pdf_worker():
    cmd = [
        "celery", "-A", "univy.celery_config.celery_univy",
        "worker",
        "--queues=pdf_processing",
        "--concurrency=2",
        "--loglevel=info",
        "--hostname=worker_pdf_processing@%h",
        "--pool=prefork"
    ]
    
    print("Starting PDF processing worker...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopping PDF processing worker...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting PDF worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_pdf_worker() 