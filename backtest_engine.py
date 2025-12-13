#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Engine: Simulate strategy over historical data.
- Evaluates ticket performance against actual draws
- Computes metrics: hit rates, prize tiers, anchor performance
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class BacktestResult:
    """Result for a single draw evaluation."""
    date: str
    best_match: int  # Best match count across all tickets
    hits_3: int  # Number of tickets with 3+ matches
    hits_4: int
    hits_5: int
    hits_5_reserve: int
    hits_6: int
    tickets: List[List[int]]  # Tickets that hit 3+
    matched_counts: List[int]  # Match count per ticket


@dataclass
class BacktestMetrics:
    """Aggregate metrics across backtest."""
    total_draws: int
    total_tickets: int
    hits_3_total: int
    hits_4_total: int
    hits_5_total: int
    hits_5_reserve_total: int
    hits_6_total: int
    
    # Rates
    coverage_3: float  # % of draws with at least one 3-hit
    coverage_4: float
    coverage_5: float
    coverage_5_reserve: float
    coverage_6: float
    
    # Average match per ticket
    avg_match: float
    
    # Anchor hit analysis
    anchor_hits: Dict[str, int] = None


class BacktestEngine:
    """Evaluate ticket set performance against actual draws."""

    def __init__(self, game: str = "xl"):
        self.game = game
        self.results = []
        self.metrics = None

    def evaluate_ticket(self, ticket: List[int], actual_draw: Dict) -> int:
        """
        Count matches between ticket and actual draw.

        Args:
            ticket: List of 6 numbers
            actual_draw: Dict with 'main' (set of 6) and 'reserve' (int)

        Returns:
            Match count (0-6)
        """
        ticket_set = set(ticket)
        main_set = actual_draw.get("main", set())
        matches = len(ticket_set & main_set)
        return matches

    def evaluate_set(
        self, tickets: List[List[int]], actual_draw: Dict
    ) -> BacktestResult:
        """
        Evaluate full ticket set against one draw.

        Args:
            tickets: List of tickets
            actual_draw: Dict with 'main' (set of 6) and 'reserve' (int)

        Returns:
            BacktestResult with match statistics
        """
        matched_counts = [self.evaluate_ticket(t, actual_draw) for t in tickets]

        result = BacktestResult(
            date=actual_draw.get("date", ""),
            best_match=max(matched_counts) if matched_counts else 0,
            hits_3=sum(1 for m in matched_counts if m >= 3),
            hits_4=sum(1 for m in matched_counts if m >= 4),
            hits_5=sum(1 for m in matched_counts if m >= 5),
            hits_5_reserve=sum(1 for m in matched_counts if m == 5),  # Separate 5+reserve
            hits_6=sum(1 for m in matched_counts if m >= 6),
            tickets=[t for t, m in zip(tickets, matched_counts) if m >= 3],
            matched_counts=matched_counts,
        )

        self.results.append(result)
        return result

    def compute_metrics(self) -> BacktestMetrics:
        """Compute aggregate metrics from all evaluations."""
        if not self.results:
            raise ValueError("No backtest results. Run evaluate_set first.")

        total_draws = len(self.results)
        total_tickets = sum(len(r.matched_counts) for r in self.results)

        hits_3 = sum(r.hits_3 for r in self.results)
        hits_4 = sum(r.hits_4 for r in self.results)
        hits_5 = sum(r.hits_5 for r in self.results)
        hits_5_reserve = sum(r.hits_5_reserve for r in self.results)
        hits_6 = sum(r.hits_6 for r in self.results)

        coverage_3 = sum(1 for r in self.results if r.hits_3 > 0) / total_draws if total_draws > 0 else 0
        coverage_4 = sum(1 for r in self.results if r.hits_4 > 0) / total_draws if total_draws > 0 else 0
        coverage_5 = sum(1 for r in self.results if r.hits_5 > 0) / total_draws if total_draws > 0 else 0
        coverage_5_reserve = sum(1 for r in self.results if r.hits_5_reserve > 0) / total_draws if total_draws > 0 else 0
        coverage_6 = sum(1 for r in self.results if r.hits_6 > 0) / total_draws if total_draws > 0 else 0

        all_matches = [m for r in self.results for m in r.matched_counts]
        avg_match = np.mean(all_matches) if all_matches else 0

        metrics = BacktestMetrics(
            total_draws=total_draws,
            total_tickets=total_tickets,
            hits_3_total=hits_3,
            hits_4_total=hits_4,
            hits_5_total=hits_5,
            hits_5_reserve_total=hits_5_reserve,
            hits_6_total=hits_6,
            coverage_3=coverage_3,
            coverage_4=coverage_4,
            coverage_5=coverage_5,
            coverage_5_reserve=coverage_5_reserve,
            coverage_6=coverage_6,
            avg_match=avg_match,
        )

        self.metrics = metrics
        return metrics

    def print_summary(self):
        """Print backtest summary."""
        if not self.metrics:
            raise ValueError("Call compute_metrics first.")

        m = self.metrics
        print(f"\n{'='*70}")
        print(f"BACKTEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Draws Evaluated: {m.total_draws}")
        print(f"Total Tickets Played: {m.total_tickets}")
        print(f"\nHit Statistics:")
        print(f"  3-hits: {m.hits_3_total:4d} ({m.coverage_3*100:.1f}% of draws)")
        print(f"  4-hits: {m.hits_4_total:4d} ({m.coverage_4*100:.1f}% of draws)")
        print(f"  5-hits: {m.hits_5_total:4d} ({m.coverage_5*100:.1f}% of draws)")
        print(f"  5+reserve: {m.hits_5_reserve_total:4d} ({m.coverage_5_reserve*100:.1f}% of draws)")
        print(f"  6-hits: {m.hits_6_total:4d} ({m.coverage_6*100:.1f}% of draws)")
        print(f"\nAverage Match: {m.avg_match:.2f} per ticket")
        print(f"{'='*70}\n")

    def get_results_df(self) -> pd.DataFrame:
        """Return results as DataFrame."""
        records = [asdict(r) for r in self.results]
        return pd.DataFrame(records)
