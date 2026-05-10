#!/usr/bin/env python3
"""
SEO Lens Job Queue Worker

This worker processes async SEO analysis jobs from the Redis queue.
Run this as a separate process alongside the main API server.

Usage:
    python worker.py                    # Run with default settings
    python worker.py --interval 2.0     # Poll every 2 seconds
    python worker.py --once             # Process one job and exit
"""
import asyncio
import argparse
import signal
import sys
from src.config.logger_config import setup_logger
from src.webhooks.services.job_queue import job_queue

logger = setup_logger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


async def run_worker(poll_interval: float = 1.0, run_once: bool = False):
    """
    Run the job queue worker
    
    Args:
        poll_interval: Seconds between polling for new jobs
        run_once: If True, process one job and exit
    """
    logger.info("=" * 60)
    logger.info("SEO Lens Job Queue Worker")
    logger.info("=" * 60)
    logger.info(f"Poll interval: {poll_interval}s")
    logger.info(f"Mode: {'Single job' if run_once else 'Continuous'}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        if run_once:
            # Process one job and exit
            job_data = await job_queue.dequeue()
            if job_data:
                result = await job_queue.process_job(job_data)
                logger.info(f"Processed job: {result}")
            else:
                logger.info("No jobs in queue")
        else:
            # Run continuously until shutdown
            while not shutdown_requested:
                try:
                    # Dequeue a job
                    job_data = await job_queue.dequeue()
                    
                    if job_data:
                        # Process the job
                        result = await job_queue.process_job(job_data)
                        logger.info(f"Successfully processed job: {result}")
                    else:
                        # No jobs, wait before polling again
                        await asyncio.sleep(poll_interval)
                except Exception as e:
                    logger.error(f"Error processing job: {e}", exc_info=True)
                    # Wait before retrying
                    await asyncio.sleep(poll_interval)
                    
        logger.info("Worker stopped gracefully")
        
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="SEO Lens Job Queue Worker - Process async SEO analysis jobs"
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=1.0,
        help="Polling interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--once", "-o",
        action="store_true",
        help="Process one job and exit"
    )
    
    args = parser.parse_args()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the worker
    asyncio.run(run_worker(poll_interval=args.interval, run_once=args.once))


if __name__ == "__main__":
    main()
