#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Mortem Analysis Engine (Phase 2)
- Compares predictions vs actual results
- Generates performance report
- Identifies what went right/wrong
"""

import json
import sys
import os
import ast
import yaml
import pandas as pd
from datetime import datetime
from typing import List, Dict, Set

class PostMortemAnalyst:
    def __init__(self, prediction_file: str, actual_numbers: List[int], actual_reserve: int):
        self.prediction_file = prediction_file
        self.actual_numbers = set(actual_numbers)
        self.actual_reserve = actual_reserve
        
        with open(prediction_file, 'r') as f:
            self.data = json.load(f)
            
    def analyze(self):
        print("="*70)
        print(f"POST-MORTEM ANALYSIS: Week {self.data.get('week', '?')}")
        print(f"Draw Result: {sorted(list(self.actual_numbers))} + {self.actual_reserve}")
        print("="*70)
        
        report = {
            'xl_performance': {'hits': [], 'prizes': []},
            'lotto_performance': {'hits': [], 'prizes': []},
            'insights': {'good_anchors': [], 'bad_anchors': [], 'missed_opportunities': []}
        }
        
        print("\n--- TICKET PERFORMANCE ---")
        
        for t in self.data['tickets']:
            nums = set(t['main_numbers'])
            matches = nums.intersection(self.actual_numbers)
            hit_count = len(matches)
            res_match = t['reserve'] == self.actual_reserve
            
            # Prize Tier Logic (Simplified)
            tier = "None"
            if hit_count == 6: tier = "Jackpot (6+0)"
            elif hit_count == 5 and res_match: tier = "Tier 2 (5+1)"
            elif hit_count == 5: tier = "Tier 3 (5+0)"
            elif hit_count == 4: tier = "Tier 4 (4+0)"
            elif hit_count == 3: tier = "Tier 5 (3+0)"
            elif hit_count == 2 and res_match: tier = "Tier 6 (2+1)"
            
            # Log
            status = f"{hit_count} Hits"
            if res_match: status += " + Reserve"
            if tier != "None": status += f" [{tier}]"
            
            print(f"Ticket ({t['type']}) {sorted(list(nums))}: {status}")
            print(f"  Rationale: {t['rationale']}")
            
            # Categorize
            cat = 'xl_performance' if 'XL' in t['type'] else 'lotto_performance'
            report[cat]['hits'].append(hit_count)
            if tier != "None": report[cat]['prizes'].append(tier)
            
            # Analyze Rationale
            if "Anchors" in t['rationale']:
                # Extract anchors from rationale string (simple parsing)
                # "Anchors [9, 10]: ..."
                try:
                    start = t['rationale'].find('[')
                    end = t['rationale'].find(']')
                    if start != -1 and end != -1:
                        # Use ast.literal_eval for security (avoids code injection)
                        anchors = ast.literal_eval(t['rationale'][start:end+1])
                        anchor_hits = set(anchors).intersection(self.actual_numbers)
                        if len(anchor_hits) == len(anchors):
                            report['insights']['good_anchors'].append(anchors)
                            print(f"  ✅ Anchor Success: {anchors}")
                        elif len(anchor_hits) == 0:
                            report['insights']['bad_anchors'].append(anchors)
                            print(f"  ❌ Anchor Fail: {anchors}")
                except (ValueError, SyntaxError):
                    pass  # Skip if parsing fails

        print("\n--- SUMMARY ---")
        avg_xl = sum(report['xl_performance']['hits']) / len(report['xl_performance']['hits']) if report['xl_performance']['hits'] else 0
        avg_lotto = sum(report['lotto_performance']['hits']) / len(report['lotto_performance']['hits']) if report['lotto_performance']['hits'] else 0
        
        print(f"Avg Hits (XL): {avg_xl:.2f}")
        print(f"Avg Hits (Lotto): {avg_lotto:.2f}")
        print(f"Prizes Won: {report['xl_performance']['prizes'] + report['lotto_performance']['prizes']}")
        
        # Save Report
        report_path = self.prediction_file.replace('.json', '_REPORT.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python post_mortem.py <prediction_json> <n1,n2,n3,n4,n5,n6> <reserve>")
        sys.exit(1)
        
    pred_file = sys.argv[1]
    nums = [int(x) for x in sys.argv[2].split(',')]
    res = int(sys.argv[3])
    
    analyst = PostMortemAnalyst(pred_file, nums, res)
    analyst.analyze()
