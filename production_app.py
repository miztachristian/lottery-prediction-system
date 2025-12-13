#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production Lottery Prediction System
Optimized for €100k+ wins with email notifications
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
from constraint_generator import TicketGenerator, TicketConfig
from email_notifier import EmailNotifier


class ProductionLotterySystem:
    """Production-ready lottery prediction system."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 70)
        self.logger.info("NETHERLANDS LOTTERY PREDICTION SYSTEM")
        self.logger.info("=" * 70)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'])
        
        # Create logs directory
        log_dir = os.path.dirname(log_config['file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logging
        handlers = []
        
        # File handler
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config['max_file_size_mb'] * 1024 * 1024,
            backupCount=log_config['backup_count']
        )
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
        
        # Console handler
        if log_config['console']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            handlers.append(console_handler)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        for handler in handlers:
            handler.setFormatter(formatter)
        
        logging.basicConfig(level=log_level, handlers=handlers)

    def _setup_directories(self):
        """Create necessary directories."""
        dirs = ['logs', 'backups', 'predictions']
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def update_data(self) -> bool:
        """Update lottery data from web sources."""
        if not self.config['data_update']['auto_update']:
            self.logger.info("Auto-update disabled, skipping data update")
            return True
        
        self.logger.info("Updating lottery data from web sources...")
        
        try:
            csv_path = self.config['lottery']['csv_path']
            game = self.config['lottery']['game']
            
            data = LottoData(csv_path, game=game)
            
            sources = self.config['data_update']['sources']
            max_pages = self.config['data_update']['max_pages']
            
            for source in sources:
                self.logger.info(f"Scraping from {source}...")
                success = data.update_with_scraped_data(
                    max_pages=max_pages,
                    source=source
                )
                
                if not success:
                    self.logger.warning(f"Failed to scrape from {source}")
            
            # Check if we have enough data
            if len(data) < self.config['data_update']['min_draws']:
                self.logger.error(f"Insufficient data: {len(data)} draws (minimum {self.config['data_update']['min_draws']})")
                return False
            
            self.logger.info(f"✓ Data updated: {len(data)} draws available")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating data: {e}", exc_info=True)
            return False

    def generate_predictions(self) -> List[Dict]:
        """
        Generate optimized predictions for high-tier wins.
        
        Returns:
            List of ticket dictionaries
        """
        self.logger.info("=" * 70)
        self.logger.info("GENERATING PREDICTIONS")
        self.logger.info("=" * 70)
        
        try:
            # Load config
            csv_path = self.config['lottery']['csv_path']
            game = self.config['lottery']['game']
            
            # Load data
            self.logger.info(f"Loading data from {csv_path}...")
            data = LottoData(csv_path, game=game)
            self.logger.info(f"Loaded {len(data)} historical draws")
            
            # Build and train enhanced model
            self.logger.info("Training Enhanced ML model (deeper architecture)...")
            model_config = self.config['model']
            
            from data_pipeline import build_sequence_dataset
            X, y_main, y_reserve, dates = build_sequence_dataset(
                data.get_df(),
                lookback=model_config['lookback']
            )
            
            self.logger.info(f"Dataset: {len(X)} sequences, {model_config['lookback']} timesteps")
            
            # Build enhanced model with improved architecture
            model = build_enhanced_model(
                lookback=model_config['lookback'],
                balls=45,
                d_model=192,  # Larger embedding
                n_heads=6,     # More attention heads
                n_layers=4,    # Deeper network
                dropout=0.3,
                pos_weight=12.0,
                lambda_sum6=0.02,
                lambda_diversity=0.01
            )
            
            self.logger.info(f"Model parameters: {model.count_params():,}")
            
            # Train with enhanced techniques
            train_enhanced_model(
                model, X, y_main, y_reserve,
                epochs=model_config['epochs'],
                batch_size=model_config['batch_size'],
                val_size=model_config['val_size'],
                verbose=0
            )
            
            self.logger.info("✓ Enhanced model trained successfully")
            
            # Get predictions
            recent_window = data.get_df().tail(model_config['lookback'])
            from data_pipeline import onehot_draw
            X_recent = np.stack([onehot_draw(row) for _, row in recent_window.iterrows()])
            X_recent = X_recent.reshape(1, model_config['lookback'], 45)
            
            probs_main, probs_reserve = predict_probs_enhanced(model, X_recent)
            
            # Get hot/cold stats
            hot, cold = data.compute_hot_cold(recent_window=20)
            
            self.logger.info(f"Hot numbers: {sorted(hot)}")
            self.logger.info(f"Cold numbers: {sorted(cold)}")
            
            # Generate tickets
            self.logger.info("Generating optimized tickets...")
            ticket_config = self.config['lottery']['tickets']
            
            generator = TicketGenerator(
                probs=probs_main,
                hot=hot,
                cold=cold,
                game=game
            )
            
            # Generate coverage tickets
            coverage_tickets = generator.generate_coverage_tickets(
                n=ticket_config['coverage'],
                top_k=25
            )
            
            # Generate convergence tickets
            convergence_tickets = generator.generate_convergence_tickets(
                n=ticket_config['convergence']
            )
            
            # Assign reserves
            all_tickets = []
            
            for ticket in coverage_tickets:
                reserve = generator.select_reserve_for_ticket(ticket, probs_reserve)
                all_tickets.append({
                    'main_numbers': ticket,
                    'reserve': reserve,
                    'type': 'coverage'
                })
            
            for ticket in convergence_tickets:
                reserve = generator.select_reserve_for_ticket(ticket, probs_reserve)
                all_tickets.append({
                    'main_numbers': ticket,
                    'reserve': reserve,
                    'type': 'convergence'
                })
            
            self.logger.info(f"✓ Generated {len(all_tickets)} tickets")
            self.logger.info(f"  - Coverage: {ticket_config['coverage']}")
            self.logger.info(f"  - Convergence: {ticket_config['convergence']}")
            
            return all_tickets
            
        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}", exc_info=True)
            return []

    def save_predictions(self, tickets: List[Dict], game: str) -> Tuple[str, str]:
        """
        Save predictions to files.
        
        Returns:
            Tuple of (json_path, csv_path)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        game_name = "lotto_xl" if game == "xl" else "lotto"
        
        # Save as JSON
        json_path = f"predictions/predictions_{game_name}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'game': game,
                'tickets': [
                    {
                        'main_numbers': sorted(list(t['main_numbers'])),
                        'reserve': t['reserve'],
                        'type': t['type']
                    }
                    for t in tickets
                ]
            }, f, indent=2)
        
        # Save as CSV
        csv_path = f"predictions/predictions_{game_name}_{timestamp}.csv"
        rows = []
        for i, ticket in enumerate(tickets, 1):
            main = sorted(list(ticket['main_numbers']))
            rows.append({
                'ticket_num': i,
                'n1': main[0],
                'n2': main[1],
                'n3': main[2],
                'n4': main[3],
                'n5': main[4],
                'n6': main[5],
                'reserve': ticket['reserve'],
                'type': ticket['type']
            })
        
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        
        self.logger.info(f"✓ Predictions saved:")
        self.logger.info(f"  - JSON: {json_path}")
        self.logger.info(f"  - CSV: {csv_path}")
        
        return json_path, csv_path

    def send_email(self, tickets: List[Dict], csv_path: str = None) -> bool:
        """Send predictions via email."""
        if not self.config['email']['enabled']:
            self.logger.info("Email notifications disabled")
            return False
        
        self.logger.info("Sending predictions via email...")
        
        try:
            email_config = self.config['email']
            game = self.config['lottery']['game']
            
            notifier = EmailNotifier(
                smtp_server=email_config['smtp_server'],
                smtp_port=email_config['smtp_port'],
                sender_email=email_config['sender_email'],
                sender_password=email_config['sender_password'],
                use_tls=email_config['use_tls']
            )
            
            subject = email_config['subject'].format(
                date=datetime.now().strftime('%Y-%m-%d')
            )
            
            success = notifier.send_predictions(
                recipient_email=email_config['recipient_email'],
                tickets=tickets,
                game=game,
                subject=subject,
                attach_csv=csv_path
            )
            
            if success:
                self.logger.info("✓ Email sent successfully")
            else:
                self.logger.error("✗ Failed to send email")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}", exc_info=True)
            return False

    def run(self) -> bool:
        """Run complete prediction pipeline."""
        self.logger.info("Starting prediction pipeline...")
        
        try:
            # Update data
            if not self.update_data():
                self.logger.error("Data update failed, aborting")
                return False
            
            # Generate predictions
            tickets = self.generate_predictions()
            
            if not tickets:
                self.logger.error("No tickets generated, aborting")
                return False
            
            # Save predictions
            game = self.config['lottery']['game']
            json_path, csv_path = self.save_predictions(tickets, game)
            
            # Send email
            email_sent = self.send_email(tickets, csv_path)
            
            self.logger.info("=" * 70)
            self.logger.info("PREDICTION PIPELINE COMPLETED")
            self.logger.info("=" * 70)
            self.logger.info(f"✓ Generated {len(tickets)} tickets")
            self.logger.info(f"✓ Saved to: {csv_path}")
            self.logger.info(f"✓ Email sent: {'Yes' if email_sent else 'No'}")
            self.logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Production Lottery Prediction System"
    )
    parser.add_argument("--config", default="config.yaml",
                       help="Path to configuration file")
    parser.add_argument("--test-email", action="store_true",
                       help="Send test email and exit")
    
    args = parser.parse_args()
    
    if args.test_email:
        print("Sending test email...")
        from email_notifier import send_test_email
        success = send_test_email(args.config)
        sys.exit(0 if success else 1)
    
    # Run production system
    system = ProductionLotterySystem(config_path=args.config)
    success = system.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
