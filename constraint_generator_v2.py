#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constraint-Based Ticket Generator with Rationale
- Enforces anchors, 3-odd/3-even, low/mid/high spread
- Generates explicit rationale for every decision
"""

import numpy as np
import random
from typing import List, Set, Tuple, Dict, Optional
from dataclasses import dataclass, field

BALLS = 45

@dataclass
class Ticket:
    numbers: List[int]
    rationale: str
    ticket_type: str  # "XL Play" or "Lotto Theoretical"
    strategy: str     # "Conservative", "Balanced", "Aggressive"

class TicketGenerator:
    """Generate lottery tickets with constraints and rationale."""

    def __init__(self, strategy_state: dict):
        self.state = strategy_state
        self.rng = np.random.RandomState()

    def _get_anchors(self, game_type: str) -> List[Set[int]]:
        """Get anchor sets based on game type."""
        if game_type == "xl":
            # XL uses pairs: [[9, 10], [20, 21], ...]
            raw_pairs = self.state['anchors']['xl']['pairs']
            return [set(p) for p in raw_pairs]
        else:
            # Lotto uses singles: [21, 23, ...]
            raw_singles = self.state['anchors']['lotto']['singles']
            return [{s} for s in raw_singles]

    def _classify_number(self, n: int, hot: Set[int], cold: Set[int]) -> str:
        if n in hot: return "Hot"
        if n in cold: return "Cold/Overdue"
        return "Neutral"

    def generate_ticket(self, 
                       game_type: str, 
                       probs: np.ndarray, 
                       hot: Set[int], 
                       cold: Set[int],
                       strategy: str = "Balanced") -> Optional[Ticket]:
        """
        Generate a single ticket with rationale.
        """
        rationale_parts = []
        numbers = set()
        
        # 1. Select Anchors
        anchors = self._get_anchors(game_type)
        
        # Determine if we use anchors (based on usage_rate)
        usage_rate = self.state['anchors'][game_type]['usage_rate']
        use_anchor = self.rng.random() < usage_rate
        
        if use_anchor:
            # Pick an anchor set
            anchor_set = self.rng.choice(anchors)
            numbers.update(anchor_set)
            rationale_parts.append(f"Anchors {sorted(list(anchor_set))}: Core foundation based on {game_type.upper()} strategy.")
        else:
            rationale_parts.append("No fixed anchors: Exploring open combinations for coverage.")

        # 2. Fill remaining slots
        # Strategy influences selection:
        # Conservative: Mostly Hot + High Prob
        # Balanced: Mix of Hot/Neutral + Prob
        # Aggressive: Include Cold/Overdue + Clusters
        
        attempts = 0
        while len(numbers) < 6 and attempts < 100:
            attempts += 1
            
            # Calculate needs
            needed = 6 - len(numbers)
            current_odd = sum(1 for n in numbers if n % 2 != 0)
            current_even = len(numbers) - current_odd
            
            # Target 3 odd / 3 even
            need_odd = max(0, 3 - current_odd)
            need_even = max(0, 3 - current_even)
            
            # Filter candidates
            candidates = []
            
            # Sort all balls by probability
            sorted_indices = np.argsort(probs)[::-1] # High to low
            
            # Select pool based on strategy
            if strategy == "Conservative":
                # Top 15 probs + Hot
                pool = set(sorted_indices[:15] + 1) | hot
            elif strategy == "Aggressive":
                # Top 25 + Cold
                pool = set(sorted_indices[:25] + 1) | cold
            else: # Balanced
                # Top 20 + Hot + some Cold
                pool = set(sorted_indices[:20] + 1) | hot | set(list(cold)[:2])
                
            # Remove already selected
            pool = pool - numbers
            
            # Filter by parity needs if critical
            if len(numbers) >= 4: # Late stage, enforce strict parity
                if need_odd > 0 and need_even == 0:
                    pool = {n for n in pool if n % 2 != 0}
                elif need_even > 0 and need_odd == 0:
                    pool = {n for n in pool if n % 2 == 0}
            
            if not pool:
                # Fallback to all numbers if pool empty
                pool = set(range(1, 46)) - numbers
            
            # Pick one
            # Weight by probability
            pool_list = list(pool)
            pool_probs = probs[np.array(pool_list) - 1]
            pool_probs = pool_probs / pool_probs.sum()
            
            pick = self.rng.choice(pool_list, p=pool_probs)
            numbers.add(pick)
            
        if len(numbers) != 6:
            return None # Failed to fill
            
        # 3. Validate Constraints
        odd = sum(1 for n in numbers if n % 2 != 0)
        even = 6 - odd
        
        low = sum(1 for n in numbers if n <= 15)
        mid = sum(1 for n in numbers if 16 <= n <= 30)
        high = sum(1 for n in numbers if n >= 31)
        
        # Strict check
        if odd != 3 or even != 3:
            return None
        if low == 0 or mid == 0 or high == 0:
            return None
            
        # 4. Build Rationale
        # Classify support numbers
        support = sorted(list(numbers - (anchor_set if use_anchor else set())))
        support_desc = []
        for n in support:
            cls = self._classify_number(n, hot, cold)
            support_desc.append(f"{n}({cls})")
            
        rationale_parts.append(f"Support: {', '.join(support_desc)}.")
        rationale_parts.append(f"Structure: {odd}Odd/{even}Even, Spread {low}L-{mid}M-{high}H.")
        rationale_parts.append(f"Strategy: {strategy} - {'Riskier cold numbers included' if strategy == 'Aggressive' else 'Focus on high probability'}.")
        
        return Ticket(
            numbers=sorted(list(numbers)),
            rationale=" ".join(rationale_parts),
            ticket_type=f"{game_type.upper()} Set",
            strategy=strategy
        )

    def generate_set(self, 
                    game_type: str, 
                    count: int, 
                    probs: np.ndarray, 
                    hot: Set[int], 
                    cold: Set[int]) -> List[Ticket]:
        """Generate a set of tickets with mixed strategies."""
        tickets = []
        
        # Distribution from strategy state
        n_conservative = int(count * self.state['composition']['conservative'])
        n_aggressive = int(count * self.state['composition']['aggressive'])
        n_balanced = count - n_conservative - n_aggressive
        
        strategies = (["Conservative"] * n_conservative + 
                     ["Aggressive"] * n_aggressive + 
                     ["Balanced"] * n_balanced)
        
        random.shuffle(strategies)
        
        for strat in strategies:
            # Try to generate valid ticket
            generated = False
            for _ in range(50): # Retry limit
                t = self.generate_ticket(game_type, probs, hot, cold, strat)
                if t:
                    tickets.append(t)
                    generated = True
                    break
            
            if not generated:
                # Fallback: try with Balanced strategy if original failed
                for _ in range(50):
                    t = self.generate_ticket(game_type, probs, hot, cold, "Balanced")
                    if t:
                        tickets.append(t)
                        break
        
        # Log warning if we couldn't generate enough tickets
        if len(tickets) < count:
            import logging
            logging.warning(f"Could only generate {len(tickets)}/{count} tickets")
        
        return tickets
