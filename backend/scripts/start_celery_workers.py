#!/usr/bin/env python3
"""
Script to start Celery workers for different queues
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from univy.celery_config.celery_univy import app

def start_worker(queue_name, concurrency=2, loglevel="info"):
    """Start a Celery worker for a specific queue"""
    cmd = [
        "celery", "-A", "src.univy.celery_config.celery_univy",
        "worker",
        f"--queues={queue_name}",
        f"--concurrency={concurrency}",
        f"--loglevel={loglevel}",
        f"--hostname=worker_{queue_name}@%h",
        "--pool=prefork"
    ]
    
    print(f"Starting worker for queue: {queue_name}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print(f"\nStopping worker for queue: {queue_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error starting worker for {queue_name}: {e}")

def start_all_workers():
    """Start workers for all queues"""
    workers = [
        ("pdf_processing", 2),  # PDF processing - CPU intensive, fewer workers
        ("file_scanning", 4),   # File scanning - I/O intensive, more workers
        ("maintenance", 1),     # Maintenance - low priority, single worker
    ]
    
    print("Starting Celery workers for all queues...")
    print("Press Ctrl+C to stop all workers")
    
    try:
        for queue_name, concurrency in workers:
            start_worker(queue_name, concurrency)
    except KeyboardInterrupt:
        print("\nStopping all workers...")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Celery workers")
    parser.add_argument("--queue", help="Specific queue to start worker for")
    parser.add_argument("--concurrency", type=int, default=2, help="Number of worker processes")
    parser.add_argument("--loglevel", default="info", help="Log level")
    
    args = parser.parse_args()
    
    if args.queue:
        # Start worker for specific queue
        start_worker(args.queue, args.concurrency, args.loglevel)
    else:
        # Start all workers
        start_all_workers() 