#!/usr/bin/env python3
"""
Start maintenance Celery worker
"""

import subprocess
import sys

def start_maintenance_worker():
    cmd = [
        "celery", "-A", "univy.celery_config.celery_univy",
        "worker",
        "--queues=maintenance",
        "--concurrency=1",
        "--loglevel=info",
        "--hostname=worker_maintenance@%h",
        "--pool=prefork"
    ]
    
    print("Starting maintenance worker...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopping maintenance worker...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting maintenance worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_maintenance_worker() 