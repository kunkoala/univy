#!/usr/bin/env python3
"""
Script to start Celery beat scheduler for periodic tasks
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from univy.celery_config.celery_univy import app

def start_beat_scheduler():
    """Start the Celery beat scheduler"""
    cmd = [
        "celery", "-A", "src.univy.celery_config.celery_univy",
        "beat",
        "--loglevel=info",
        "--scheduler=celery.beat.PersistentScheduler"
    ]
    
    print("Starting Celery beat scheduler...")
    print(f"Command: {' '.join(cmd)}")
    print("Press Ctrl+C to stop the scheduler")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopping Celery beat scheduler...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting beat scheduler: {e}")

if __name__ == "__main__":
    start_beat_scheduler() 