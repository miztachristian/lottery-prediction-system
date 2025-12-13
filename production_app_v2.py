#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production Lottery Prediction System (Iterative Learning Edition)
- Phase 1: Prediction with Stored Rationale
- Generates 12 XL + 12 Lotto tickets
- Uses Strategy State for dynamic rules
"""

import os
import sys
import yaml
import logging
from datetime import datetime
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import json

from data_pipeline import LottoData
from ml_model_enhanced import build_enhanced_model, train_enhanced_model, predict_probs_enhanced
from constraint_generator_v2 import TicketGenerator, Ticket
from email_notifier import EmailNotifier


class ProductionLotterySystem:
    """Production-ready lottery prediction system with iterative learning."""

    def __init__(self, config_path: str = "config.yaml", strategy_path: str = "strategy_state.yaml"):
        """
        Args:
            config_path: Path to configuration file
            strategy_path: Path to strategy state file
        """
        self.config = self._load_yaml(config_path)
        self.strategy_state = self._load_yaml(strategy_path)
        self._setup_logging()
        self._setup_directories()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 70)
        self.logger.info("NETHERLANDS LOTTERY PREDICTION SYSTEM (ITERATIVE)")
        self.logger.info("=" * 70)

    def _load_yaml(self, path: str) -> dict:
        """Load YAML file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'])
        
        log_dir = os.path.dirname(log_config['file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        handlers = []
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config['max_file_size_mb'] * 1024 * 1024,
            backupCount=log_config['backup_count']
        )
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
        
        if log_config['console']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            handlers.append(console_handler)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        for handler in handlers:
            handler.setFormatter(formatter)
        
        logging.basicConfig(level=log_level, handlers=handlers)

    def _setup_directories(self):
        """Create necessary directories."""
        dirs = ['logs', 'backups', 'predictions', 'analysis']
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def update_data(self) -> bool:
        """Update lottery data from web sources."""
        if not self.config['data_update']['auto_update']:
            return True
        
        self.logger.info("Updating lottery data...")
        try:
            csv_path = self.config['lottery']['csv_path']
            game = self.config['lottery']['game']
            data = LottoData(csv_path, game=game)
            
            for source in self.config['data_update']['sources']:
                data.update_with_scraped_data(
                    max_pages=self.config['data_update']['max_pages'],
                    source=source
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating data: {e}", exc_info=True)
            return False

    def generate_predictions(self) -> List[Dict]:
        """
        Generate predictions for both XL (Play) and Lotto (Theoretical).
        """
        self.logger.info("=" * 70)
        self.logger.info("GENERATING PREDICTIONS WITH RATIONALE")
        self.logger.info("=" * 70)
        
        try:
            # Load data & Train Model
            csv_path = self.config['lottery']['csv_path']
            data = LottoData(csv_path, game="xl")
            
            # Train Model
            self.logger.info("Training Enhanced ML model...")
            model_config = self.config['model']
            from data_pipeline import build_sequence_dataset, onehot_draw
            
            X, y_main, y_reserve, _ = build_sequence_dataset(data.get_df(), lookback=model_config['lookback'])
            
            model = build_enhanced_model(lookback=model_config['lookback'], balls=45)
            train_enhanced_model(model, X, y_main, y_reserve, epochs=model_config['epochs'], verbose=0)
            
            # Predict
            recent_window = data.get_df().tail(model_config['lookback'])
            X_recent = np.stack([onehot_draw(row) for _, row in recent_window.iterrows()])
            X_recent = X_recent.reshape(1, model_config['lookback'], 45)
            probs_main, probs_reserve = predict_probs_enhanced(model, X_recent)
            probs = probs_main[0] # (45,)
            
            # Get Stats
            hot, cold = data.compute_hot_cold(recent_window=20)
            
            # Initialize Generator with Strategy State
            generator = TicketGenerator(self.strategy_state)
            
            all_tickets = []
            
            # 1. Generate 12 XL Tickets (Actual Play)
            self.logger.info("Generating 12 Lotto XL tickets (Actual Play)...")
            xl_tickets = generator.generate_set("xl", 12, probs, hot, cold)
            all_tickets.extend(xl_tickets)
            
            # 2. Generate 12 Lotto Tickets (Theoretical)
            self.logger.info("Generating 12 Lotto tickets (Theoretical)...")
            lotto_tickets = generator.generate_set("lotto", 12, probs, hot, cold)
            all_tickets.extend(lotto_tickets)
            
            # Convert to dicts
            results = []
            for t in all_tickets:
                # Select reserve (simple max prob for now)
                reserve = np.argmax(probs_reserve[0]) + 1
                results.append({
                    'main_numbers': t.numbers,
                    'reserve': int(reserve),
                    'type': t.ticket_type,
                    'strategy': t.strategy,
                    'rationale': t.rationale
                })
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}", exc_info=True)
            return []

    def save_predictions(self, tickets: List[Dict]) -> Tuple[str, str]:
        """Save predictions with rationale."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON (Full Detail)
        json_path = f"predictions/prediction_rationale_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'week': self.strategy_state.get('current_week', 1),
                'tickets': tickets
            }, f, indent=2)
            
        # CSV (For Email/Printing)
        csv_path = f"predictions/tickets_{timestamp}.csv"
        rows = []
        for i, t in enumerate(tickets, 1):
            row = {
                'Ticket #': i,
                'Type': t['type'],
                'Strategy': t['strategy'],
                'Numbers': "-".join(map(str, t['main_numbers'])),
                'Reserve': t['reserve'],
                'Rationale': t['rationale']
            }
            rows.append(row)
        
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        
        return json_path, csv_path

    def send_email(self, tickets: List[Dict], csv_path: str) -> bool:
        """Send email with rationale summary."""
        if not self.config['email']['enabled']:
            return False
            
        try:
            email_config = self.config['email']
            notifier = EmailNotifier(
                email_config['smtp_server'],
                email_config['smtp_port'],
                email_config['sender_email'],
                email_config['sender_password'],
                email_config['use_tls']
            )
            
            subject = f"🇳🇱 Lotto Strategy - Week {self.strategy_state.get('current_week', 1)} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Custom body generator for rationale
            # We'll just use the standard one for now but pass the CSV
            # Ideally we'd update EmailNotifier to show rationale, but CSV is good for now.
            
            return notifier.send_predictions(
                email_config['recipient_email'],
                tickets, # This might need adaptation if EmailNotifier expects specific format
                "xl",
                subject,
                csv_path
            )
        except Exception as e:
            self.logger.error(f"Email failed: {e}", exc_info=True)
            return False

    def run(self):
        """Execute Phase 1."""
        if not self.update_data(): return False
        
        tickets = self.generate_predictions()
        if not tickets: return False
        
        json_path, csv_path = self.save_predictions(tickets)
        self.logger.info(f"Saved rationale to {json_path}")
        
        self.send_email(tickets, csv_path)
        return True

if __name__ == "__main__":
    sys.exit(0 if ProductionLotterySystem().run() else 1)
