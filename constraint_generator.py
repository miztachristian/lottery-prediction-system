#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constraint-Based Ticket Generator
- Enforces anchors, 3-odd/3-even, low/mid/high spread
- Supports coverage (broad) and convergence (aggressive) ticket types
"""

import numpy as np
from typing import List, Set, Tuple, Dict
from dataclasses import dataclass

BALLS = 45

# Anchor definitions per spec
ANCHORS_XL = [(9, 10), (20, 21), (32, 33), (21, 44)]
ANCHORS_LOTTO = [21, 23, 40, 41, 44]  # Single anchors for Lotto


@dataclass
class TicketConfig:
    """Configuration for ticket generation."""
    game: str = "xl"  # "xl" or "lotto"
    ticket_type: str = "coverage"  # "coverage" or "convergence"
    allow_nonanchor_repeat: bool = False  # Allow non-anchor numbers across tickets
    prefer_hot: bool = True  # Bias toward hot numbers
    prefer_overdue: bool = True  # Include overdue in support slots
    random_seed: int = 7


def parity(n: int) -> int:
    """Return 0 if even, 1 if odd."""
    return n % 2


def band(n: int) -> str:
    """Return 'low' (1-15), 'mid' (16-30), 'high' (31-45)."""
    if 1 <= n <= 15:
        return "low"
    if 16 <= n <= 30:
        return "mid"
    return "high"


def count_constraints(ticket: Set[int]) -> Tuple[int, int, Dict[str, int]]:
    """
    Analyze ticket constraints.

    Returns:
        (odd_count, even_count, band_counts)
    """
    odd_count = sum(1 for n in ticket if parity(n) == 1)
    even_count = len(ticket) - odd_count
    band_counts = {"low": 0, "mid": 0, "high": 0}
    for n in ticket:
        band_counts[band(n)] += 1
    return odd_count, even_count, band_counts


def is_valid_ticket(ticket: Set[int]) -> bool:
    """Check if ticket satisfies all constraints."""
    if len(ticket) != 6:
        return False

    odd, even, bands = count_constraints(ticket)

    # Check parity
    if odd != 3 or even != 3:
        return False

    # Check spread
    if 0 in bands.values():  # Missing a band
        return False

    return True


class TicketGenerator:
    """Generate lottery tickets with constraints."""

    def __init__(self, config: TicketConfig = None):
        self.config = config or TicketConfig()
        np.random.seed(self.config.random_seed)

    def generate_coverage_tickets(
        self,
        probabilities: np.ndarray,
        num_tickets: int = 12,
        hot_numbers: Set[int] = None,
        cold_numbers: Set[int] = None,
    ) -> List[List[int]]:
        """
        Generate coverage tickets: broad statistical coverage, mixed anchors.

        Args:
            probabilities: Array of 45 ball probabilities (from model)
            num_tickets: Number of tickets to generate
            hot_numbers: Set of recently hot numbers (bias toward these)
            cold_numbers: Set of overdue numbers (include in support)

        Returns:
            List of tickets (each ticket is sorted list of 6 numbers)
        """
        hot_numbers = hot_numbers or set()
        cold_numbers = cold_numbers or set()

        # Get ranked balls by probability
        ranked = np.argsort(-probabilities) + 1

        tickets = []
        used_nonanchors = set()  # Track non-anchor usage for diversity

        anchors = ANCHORS_XL if self.config.game == "xl" else [(a,) for a in ANCHORS_LOTTO]

        for i in range(num_tickets):
            # Rotate anchor selection
            if self.config.game == "xl":
                anchor = anchors[i % len(anchors)]
            else:
                # For Lotto, pick one anchor
                anchor = (anchors[i % len(anchors)][0],)

            ticket = self._build_ticket(
                anchor,
                ranked,
                used_nonanchors,
                hot_numbers,
                cold_numbers,
                allow_repeat=self.config.allow_nonanchor_repeat,
            )

            if ticket:
                tickets.append(sorted(ticket))
                # Track non-anchor usage
                for n in ticket:
                    if n not in anchor:
                        used_nonanchors.add(n)

        return tickets

    def generate_convergence_tickets(
        self,
        probabilities: np.ndarray,
        num_tickets: int = 4,
        hot_numbers: Set[int] = None,
    ) -> List[List[int]]:
        """
        Generate convergence tickets: aggressive cluster stacking.
        Uses multiple anchors or correlated high-probability numbers.

        Args:
            probabilities: Array of 45 ball probabilities
            num_tickets: Number of tickets to generate
            hot_numbers: Set of hot numbers (emphasize)

        Returns:
            List of tickets
        """
        hot_numbers = hot_numbers or set()
        ranked = np.argsort(-probabilities) + 1

        tickets = []
        anchors = ANCHORS_XL if self.config.game == "xl" else [(a,) for a in ANCHORS_LOTTO]

        for i in range(num_tickets):
            # Use multiple anchors or top-probability numbers
            if self.config.game == "xl":
                # Stack 2 anchors + 4 top correlates
                anchor_idx1 = i % len(anchors)
                anchor_idx2 = (i + 1) % len(anchors)
                anchor = set(anchors[anchor_idx1]) | set(anchors[anchor_idx2])
            else:
                # Use 2-3 anchors
                anchor = set([anchors[i % len(anchors)][0], anchors[(i + 1) % len(anchors)][0]])

            # Fill remaining slots with top-probability numbers
            ticket = set(anchor)
            for n in ranked:
                if len(ticket) == 6:
                    break
                n = int(n)
                if n not in ticket:
                    ticket.add(n)

            # Post-process to enforce constraints
            ticket = self._enforce_constraints(ticket)

            if ticket and is_valid_ticket(ticket):
                tickets.append(sorted(list(ticket)))

        return tickets

    def _build_ticket(
        self,
        anchor: Tuple[int, ...],
        ranked_balls: np.ndarray,
        used_nonanchors: Set[int],
        hot_numbers: Set[int],
        cold_numbers: Set[int],
        allow_repeat: bool = False,
    ) -> Set[int]:
        """
        Build a single ticket starting with anchor.

        Strategy:
        1. Start with anchor
        2. Add high-probability balls
        3. Bias toward hot; include overdue in support slots
        4. Enforce 3-odd/3-even and low/mid/high
        """
        ticket = set(anchor)

        for n in ranked_balls:
            if len(ticket) == 6:
                break

            n = int(n)
            if n in ticket:
                continue

            # Skip non-anchors if already used (diversity)
            if not allow_repeat and n not in anchor and n in used_nonanchors:
                continue

            # Try adding this number
            test_ticket = ticket | {n}

            # Check constraints
            odd, even, bands = count_constraints(test_ticket)
            if odd > 3 or even > 3:
                continue  # Skip if violates parity

            if 0 not in bands.values() or len(test_ticket) <= 4:  # Still building or all bands covered
                ticket = test_ticket
            else:
                # If all bands covered and 6 numbers, done
                if len(test_ticket) == 6:
                    ticket = test_ticket

        # Post-process to fix constraints
        ticket = self._enforce_constraints(ticket)

        return ticket if is_valid_ticket(ticket) else None

    def _enforce_constraints(self, ticket: Set[int], available_pool: np.ndarray = None) -> Set[int]:
        """
        Fix a ticket to satisfy all constraints.

        Tries to preserve existing numbers; swaps only when needed.
        """
        max_iters = 10
        iteration = 0

        while not is_valid_ticket(ticket) and iteration < max_iters:
            iteration += 1
            odd, even, bands = count_constraints(ticket)

            # Fix size
            if len(ticket) < 6:
                # Add a random valid number
                for n in range(1, BALLS + 1):
                    if n not in ticket:
                        test = ticket | {n}
                        if len(test) <= 6:
                            ticket = test
                            break

            if len(ticket) > 6:
                ticket = set(list(ticket)[:6])

            # Fix parity
            if odd > 3:
                # Remove an odd number, replace with even
                odd_nums = [n for n in ticket if parity(n) == 1]
                for rem in odd_nums:
                    for add in range(1, BALLS + 1):
                        if parity(add) == 0 and add not in ticket:
                            ticket.remove(rem)
                            ticket.add(add)
                            break
                    if sum(1 for n in ticket if parity(n) == 1) <= 3:
                        break

            if even > 3:
                # Remove an even, replace with odd
                even_nums = [n for n in ticket if parity(n) == 0]
                for rem in even_nums:
                    for add in range(1, BALLS + 1):
                        if parity(add) == 1 and add not in ticket:
                            ticket.remove(rem)
                            ticket.add(add)
                            break
                    if sum(1 for n in ticket if parity(n) == 0) <= 3:
                        break

            # Fix band coverage
            bands = {"low": 0, "mid": 0, "high": 0}
            for n in ticket:
                bands[band(n)] += 1

            for missing_band in [b for b, count in bands.items() if count == 0]:
                # Find a number in the missing band to add
                for candidate in range(1, BALLS + 1):
                    if band(candidate) == missing_band and candidate not in ticket:
                        # Remove a non-anchor number from an over-represented band
                        for remove_band in [b for b, count in bands.items() if count > 1]:
                            for remove_num in list(ticket):
                                if band(remove_num) == remove_band:
                                    ticket.remove(remove_num)
                                    ticket.add(candidate)
                                    break
                        break

        return ticket

    def generate(
        self,
        probabilities: np.ndarray,
        num_coverage: int = 16,
        num_convergence: int = 8,
        hot_numbers: Set[int] = None,
        cold_numbers: Set[int] = None,
    ) -> Dict[str, List[List[int]]]:
        """
        Generate full ticket set: coverage + convergence.

        Args:
            probabilities: Array of 45 ball probabilities
            num_coverage: Number of coverage tickets
            num_convergence: Number of convergence tickets
            hot_numbers: Set of hot numbers
            cold_numbers: Set of cold/overdue numbers

        Returns:
            Dict with 'coverage' and 'convergence' keys, each containing list of tickets
        """
        coverage = self.generate_coverage_tickets(
            probabilities, num_coverage, hot_numbers, cold_numbers
        )
        convergence = self.generate_convergence_tickets(
            probabilities, num_convergence, hot_numbers
        )

        return {"coverage": coverage, "convergence": convergence}
