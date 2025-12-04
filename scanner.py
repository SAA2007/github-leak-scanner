#!/usr/bin/env python3
"""
GitHub Leak Scanner - Main Entry Point

Usage:
    python scanner.py              # Run in search mode (default)
    python scanner.py --user       # Run in user mode
    python scanner.py --schedule   # Run with scheduler
"""

import sys
import argparse

# Add src to path for imports
sys.path.insert(0, 'src')

from src.core.scan_repos import main as scan_main
from src.core.scheduler import start_scheduler


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='GitHub Leak Scanner')
    parser.add_argument('--schedule', action='store_true', 
                       help='Run with scheduler (automated scans)')
    parser.add_argument('--user', action='store_true',
                       help='Run in user mode instead of search mode')
    
    args = parser.parse_args()
    
    if args.schedule:
        print("🕐 Starting scheduler...")
        start_scheduler()
    else:
        print("🔍 Starting scan...")
        scan_main()


if __name__ == "__main__":
    main()
