#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler for automated lottery predictions
Supports cron-style scheduling
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional
import yaml

try:
    from croniter import croniter
except ImportError:
    croniter = None
    print("Warning: croniter not installed. Install with: pip install croniter")

from production_app import ProductionLotterySystem


class PredictionScheduler:
    """Scheduler for automated lottery predictions."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.logger = logging.getLogger(__name__)
        
        if not self.config['scheduling']['enabled']:
            raise ValueError("Scheduling is not enabled in config.yaml")
        
        if croniter is None:
            raise ImportError("croniter package required for scheduling. Install with: pip install croniter")

    def run_prediction(self) -> bool:
        """Execute prediction pipeline."""
        self.logger.info("=" * 70)
        self.logger.info(f"SCHEDULED RUN: {datetime.now()}")
        self.logger.info("=" * 70)
        
        try:
            system = ProductionLotterySystem(config_path=self.config_path)
            success = system.run()
            return success
        except Exception as e:
            self.logger.error(f"Scheduled run failed: {e}", exc_info=True)
            return False

    def get_next_run_time(self, cron_expression: str) -> datetime:
        """
        Get next scheduled run time.
        
        Args:
            cron_expression: Cron-style schedule (e.g., "0 8 * * 3,6")
        
        Returns:
            Next run datetime
        """
        cron = croniter(cron_expression, datetime.now())
        return cron.get_next(datetime)

    def run_scheduler(self):
        """Run continuous scheduler."""
        cron_expr = self.config['scheduling']['cron_schedule']
        
        self.logger.info("=" * 70)
        self.logger.info("LOTTERY PREDICTION SCHEDULER STARTED")
        self.logger.info("=" * 70)
        self.logger.info(f"Schedule: {cron_expr}")
        
        next_run = self.get_next_run_time(cron_expr)
        self.logger.info(f"Next run: {next_run}")
        
        try:
            while True:
                now = datetime.now()
                
                if now >= next_run:
                    # Execute prediction
                    self.run_prediction()
                    
                    # Calculate next run
                    next_run = self.get_next_run_time(cron_expr)
                    self.logger.info(f"Next run: {next_run}")
                
                # Sleep for 1 minute
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}", exc_info=True)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Lottery Prediction Scheduler"
    )
    parser.add_argument("--config", default="config.yaml",
                       help="Path to configuration file")
    parser.add_argument("--run-now", action="store_true",
                       help="Run prediction immediately and exit")
    parser.add_argument("--next-run", action="store_true",
                       help="Show next scheduled run time and exit")
    
    args = parser.parse_args()
    
    scheduler = PredictionScheduler(config_path=args.config)
    
    if args.next_run:
        cron_expr = scheduler.config['scheduling']['cron_schedule']
        next_run = scheduler.get_next_run_time(cron_expr)
        print(f"Next scheduled run: {next_run}")
        print(f"Schedule: {cron_expr}")
        sys.exit(0)
    
    if args.run_now:
        success = scheduler.run_prediction()
        sys.exit(0 if success else 1)
    
    # Run continuous scheduler
    scheduler.run_scheduler()


if __name__ == "__main__":
    main()
