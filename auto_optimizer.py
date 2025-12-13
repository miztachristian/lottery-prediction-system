#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Post-Mortem & Strategy Optimizer
- Fetches latest results automatically
- Analyzes performance of recent predictions
- Updates strategy_state.yaml based on outcomes (The "Learning" Loop)
"""

import os
import sys
import json
import yaml
import glob
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

from data_pipeline import LottoData
from post_mortem import PostMortemAnalyst

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoOptimizer:
    def __init__(self, data_dir: str = "."):
        self.data_dir = data_dir
        self.strategy_path = os.path.join(data_dir, "strategy_state.yaml")
        self.predictions_dir = os.path.join(data_dir, "predictions")
        
    def get_latest_prediction_file(self) -> str:
        """Find the most recent prediction JSON file."""
        files = glob.glob(os.path.join(self.predictions_dir, "prediction_rationale_*.json"))
        if not files:
            return None
        return max(files, key=os.path.getctime)

    def update_and_get_result(self) -> Dict[str, Any]:
        """Scrape latest data and return the most recent draw."""
        logger.info("Updating data to fetch latest results...")
        
        # Initialize data pipeline to scrape
        # We assume config.yaml exists in data_dir
        config_path = os.path.join(self.data_dir, "config.yaml")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        csv_path = config['lottery']['csv_path']
        game = config['lottery']['game']
        
        data = LottoData(csv_path, game=game)
        
        # Force update
        data.update_with_scraped_data(max_pages=2, source="both")
        
        # Get last draw
        last_draw = data.get_last_draw()
        logger.info(f"Latest draw found: {last_draw['date']} - {last_draw['main']} + {last_draw['reserve']}")
        return last_draw

    def optimize_strategy(self, report: Dict, strategy: Dict) -> Dict:
        """
        The Core Learning Loop: Adjust strategy based on report.
        """
        logger.info("Optimizing strategy based on performance...")
        
        # 1. Anchor Adjustment
        # If anchors failed, slightly reduce their weight or rotate
        bad_anchors = report['insights'].get('bad_anchors', [])
        good_anchors = report['insights'].get('good_anchors', [])
        
        xl_anchors = strategy['anchors']['xl']['pairs']
        xl_weights = strategy['anchors']['xl']['weights']
        
        for bad in bad_anchors:
            # Find index of bad anchor
            bad_set = set(bad)
            for i, pair in enumerate(xl_anchors):
                if set(pair) == bad_set:
                    # Decay weight
                    xl_weights[i] = max(0.1, xl_weights[i] * 0.8)
                    logger.info(f"📉 Downgrading failing anchor {pair} weight to {xl_weights[i]:.2f}")
        
        for good in good_anchors:
            good_set = set(good)
            for i, pair in enumerate(xl_anchors):
                if set(pair) == good_set:
                    # Boost weight
                    xl_weights[i] = min(2.0, xl_weights[i] * 1.2)
                    logger.info(f"📈 Boosting successful anchor {pair} weight to {xl_weights[i]:.2f}")

        # 2. Aggression Tuning
        # Check which ticket type performed better
        # This requires parsing the report deeper, but for now let's use a simple heuristic:
        # If average hits < 2.0, increase aggression (we are too conservative/missing trends)
        # If average hits > 3.0, stabilize (keep current mix)
        
        avg_hits = 0
        total_tickets = len(report['xl_performance']['hits'])
        if total_tickets > 0:
            avg_hits = sum(report['xl_performance']['hits']) / total_tickets
            
        logger.info(f"Average hits this week: {avg_hits:.2f}")
        
        if avg_hits < 1.5:
            # Performance poor, increase aggression/variance
            strategy['composition']['aggressive'] = min(0.5, strategy['composition']['aggressive'] + 0.1)
            strategy['composition']['conservative'] = max(0.1, strategy['composition']['conservative'] - 0.1)
            logger.info("⚠️ Performance low. Increasing Aggressive allocation to explore more variance.")
        elif avg_hits > 2.5:
            # Performance good, stick to what works (Balanced)
            strategy['composition']['balanced'] = min(0.8, strategy['composition']['balanced'] + 0.1)
            strategy['composition']['aggressive'] = max(0.1, strategy['composition']['aggressive'] - 0.05)
            logger.info("✅ Performance good. Shifting slightly to Balanced to consolidate.")
        
        # Normalize composition to sum to 1.0
        total = (strategy['composition']['conservative'] + 
                 strategy['composition']['balanced'] + 
                 strategy['composition']['aggressive'])
        if total > 0:
            strategy['composition']['conservative'] /= total
            strategy['composition']['balanced'] /= total
            strategy['composition']['aggressive'] /= total

        # 3. Update Week
        strategy['current_week'] = strategy.get('current_week', 1) + 1
        strategy['last_update'] = datetime.now().strftime("%Y-%m-%d")
        
        return strategy

    def run(self):
        # 1. Find Prediction
        pred_file = self.get_latest_prediction_file()
        if not pred_file:
            logger.error("No prediction file found.")
            return False
            
        logger.info(f"Analyzing prediction file: {pred_file}")
        
        # 2. Get Actual Result
        last_draw = self.update_and_get_result()
        
        # Check if draw is new enough (simple check: is draw date > prediction file creation date?)
        # For robustness, we should check dates in file, but let's assume the latest draw is the target
        # if we are running this on Sunday/Monday.
        
        # 3. Run Post-Mortem
        actual_nums = list(last_draw['main'])
        actual_res = last_draw['reserve']
        
        analyst = PostMortemAnalyst(pred_file, actual_nums, actual_res)
        
        # Capture stdout to suppress print spam, we just want the report file
        # Or modify PostMortemAnalyst to return report. 
        # Since we can't easily modify the class without editing file again, 
        # we'll rely on the side effect: it saves _REPORT.json
        
        analyst.analyze()
        
        report_path = pred_file.replace('.json', '_REPORT.json')
        if not os.path.exists(report_path):
            logger.error("Report generation failed.")
            return False
            
        with open(report_path, 'r') as f:
            report = json.load(f)
            
        # 4. Optimize Strategy
        with open(self.strategy_path, 'r') as f:
            strategy = yaml.safe_load(f)
            
        new_strategy = self.optimize_strategy(report, strategy)
        
        # 5. Save New Strategy
        with open(self.strategy_path, 'w') as f:
            yaml.dump(new_strategy, f)
            
        logger.info("Strategy updated successfully.")
        return True

if __name__ == "__main__":
    optimizer = AutoOptimizer()
    optimizer.run()
