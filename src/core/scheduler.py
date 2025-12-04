"""
Automated scheduler for repository scanner.
Runs scans at configured intervals in the background.
"""
import time
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import signal
import sys

from src.core.config import config
from src.utils.utils import setup_logging

# Setup logging
logger = setup_logging(config.log_file, config.log_level)

# Global scheduler instance
scheduler = None


def run_scan():
    """Execute a scan run."""
    logger.info("\n" + "=" * 60)
    logger.info(f"⏰ Scheduled scan starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Import and run main scanner
        from scan_repos import main
        main()
    except Exception as e:
        logger.error(f"❌ Scheduled scan failed: {e}", exc_info=True)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("\n🛑 Shutdown signal received, stopping scheduler...")
    if scheduler:
        scheduler.shutdown(wait=True)
    logger.info("✓ Scheduler stopped cleanly")
    sys.exit(0)


def main():
    """Main scheduler entry point."""
    global scheduler
    
    logger.info("=" * 60)
    logger.info("📅 Automated Repository Scanner - Scheduler")
    logger.info("=" * 60)
    logger.info(f"Mode: {config.scan_mode.upper()}")
    logger.info(f"Interval: Every {config.scan_interval_hours} hours")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    if not config.enable_scheduler:
        logger.warning("⚠️  Scheduler is disabled in config (ENABLE_SCHEDULER=false)")
        logger.info("To enable, set ENABLE_SCHEDULER=true in your .env file")
        return
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Add job to run at specified intervals
    scheduler.add_job(
        run_scan,
        trigger=IntervalTrigger(hours=config.scan_interval_hours),
        id='scan_job',
        name='Repository Secret Scan',
        replace_existing=True,
        max_instances=1  # Prevent overlapping scans
    )
    
    # Calculate next run time
    next_run = scheduler.get_jobs()[0].next_run_time
    logger.info(f"⏭️  Next scan scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("\nPress Ctrl+C to stop the scheduler\n")
    
    # Optionally run immediately on startup
    run_immediately = input("Run a scan immediately before scheduling? (y/N): ").strip().lower()
    if run_immediately == 'y':
        logger.info("🚀 Running initial scan...")
        run_scan()
    
    try:
        # Start scheduler (blocking)
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n🛑 Scheduler stopped by user")


if __name__ == "__main__":
    main()
