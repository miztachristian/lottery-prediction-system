#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRATEGY OPTIMIZER - Monte Carlo Simulation & Wheel Comparison
==============================================================

Compares different wheel configurations to find the best cost/coverage/ROI tradeoff.

Usage:
    python strategy_optimizer.py                    # Run full comparison
    python strategy_optimizer.py --verify-current   # Verify current 12-ticket subset
    python strategy_optimizer.py --find-best-12     # Find optimal 12-of-16 subset
    python strategy_optimizer.py --sims 200000      # Custom simulation count
"""

import argparse
import random
import sys
from itertools import combinations
from math import comb
from typing import List, Dict, Tuple, Optional

from wheel_system import LotteryWheel


# --- Prize Tables (Dutch Lotto / Lotto XL) -----------------------------------

def xl_prize(matches: int, reserve_hit: bool) -> float:
    """XL cash prize."""
    table = {
        (6, True): 1_000_000, (6, False): 1_000_000,
        (5, True): 25_000, (5, False): 1_000,
        (4, True): 25, (4, False): 15,
        (3, True): 10, (3, False): 5,
        (2, True): 2, (2, False): 1,
    }
    return table.get((matches, reserve_hit), 0)


def lotto_prize(matches: int, reserve_hit: bool) -> float:
    """Lotto cash prize. Free tickets valued at EUR 3 (cost of one XL ticket)."""
    table = {
        (6, True): 2_000_000, (6, False): 1_000_000,  # Approximate jackpot
        (5, True): 100_000, (5, False): 1_000,
        (4, True): 50, (4, False): 50,
        (3, True): 3, (3, False): 3,   # Free ticket = EUR 3 value
        (2, True): 3, (2, False): 0,   # 2+R = free ticket
    }
    return table.get((matches, reserve_hit), 0)


# --- Simulation Engine -------------------------------------------------------

def simulate_draw() -> Tuple[List[int], int]:
    """Simulate a single draw: 6 main numbers + 1 reserve from 1-45."""
    all_nums = list(range(1, 46))
    drawn = random.sample(all_nums, 7)
    main = sorted(drawn[:6])
    reserve = drawn[6]
    return main, reserve


def evaluate_tickets(tickets: List[Dict], draw_nums: List[int], draw_reserve: int,
                     prize_fn) -> float:
    """Evaluate all tickets against a draw, return total prize value."""
    total = 0.0
    draw_set = set(draw_nums)
    for t in tickets:
        matches = len(set(t["numbers"]).intersection(draw_set))
        reserve_hit = t["reserve"] == draw_reserve
        total += prize_fn(matches, reserve_hit)
    return total


def simulate_week(tickets: List[Dict], super_saturday: bool = False) -> float:
    """Simulate one week: 2 draws (normal) or 4 draws (Super Saturday)."""
    total = 0.0
    # Lotto + XL draws
    lotto_nums, lotto_r = simulate_draw()
    xl_nums, xl_r = simulate_draw()
    total += evaluate_tickets(tickets, lotto_nums, lotto_r, lotto_prize)
    total += evaluate_tickets(tickets, xl_nums, xl_r, xl_prize)

    if super_saturday:
        lotto2_nums, lotto2_r = simulate_draw()
        xl2_nums, xl2_r = simulate_draw()
        total += evaluate_tickets(tickets, lotto2_nums, lotto2_r, lotto_prize)
        total += evaluate_tickets(tickets, xl2_nums, xl2_r, xl_prize)

    return total


def monte_carlo(tickets: List[Dict], n_sims: int = 100_000,
                cost_per_ticket: float = 3.0,
                super_saturday_freq: float = 1/13) -> Dict:
    """Run Monte Carlo simulation.

    Args:
        tickets: List of ticket dicts with 'numbers' and 'reserve'
        n_sims: Number of simulated weeks
        cost_per_ticket: Cost per ticket in EUR
        super_saturday_freq: Fraction of weeks that are Super Saturday (~1 in 13)
    """
    cost = len(tickets) * cost_per_ticket
    winnings = []

    for _ in range(n_sims):
        is_super = random.random() < super_saturday_freq
        won = simulate_week(tickets, super_saturday=is_super)
        winnings.append(won)

    winnings.sort()
    total_won = sum(winnings)
    avg_won = total_won / n_sims

    # Calculate stats
    wins = [w for w in winnings if w > 0]
    profits = [w for w in winnings if w > cost]
    breakevens = [w for w in winnings if w >= cost]

    return {
        "tickets": len(tickets),
        "cost_per_week": cost,
        "avg_weekly_return": round(avg_won, 2),
        "avg_weekly_profit": round(avg_won - cost, 2),
        "roi_pct": round(100 * (avg_won - cost) / cost, 1),
        "p_any_win": round(100 * len(wins) / n_sims, 1),
        "p_break_even": round(100 * len(breakevens) / n_sims, 1),
        "p_profit": round(100 * len(profits) / n_sims, 1),
        "p10": round(winnings[int(n_sims * 0.10)], 2),
        "p50": round(winnings[int(n_sims * 0.50)], 2),
        "p90": round(winnings[int(n_sims * 0.90)], 2),
        "p99": round(winnings[int(n_sims * 0.99)], 2),
        "max_won": round(max(winnings), 2),
    }


# --- Wheel Ticket Generation ------------------------------------------------

def make_tickets(numbers: List[int], wheel_type: str) -> List[Dict]:
    """Generate tickets with reserve numbers for a wheel type."""
    wheel = LotteryWheel()
    raw_tickets = wheel.generate_wheel(numbers, wheel_type)

    tickets = []
    for i, t_nums in enumerate(raw_tickets):
        available = [n for n in numbers if n not in t_nums]
        reserve = available[i % len(available)] if available else numbers[0]
        tickets.append({"numbers": t_nums, "reserve": reserve})
    return tickets


# --- Subset Optimization ----------------------------------------------------

def find_best_subset(full_tickets: List[List[int]], pool_numbers: List[int],
                     n_keep: int, winning_count: int = 4,
                     guarantee_count: int = 3) -> Tuple[List[int], int, int]:
    """Find the best n_keep tickets from a larger set that maximizes coverage.

    Returns: (best_indices, covered, total)
    """
    wheel = LotteryWheel()

    # All combinations of winning_count numbers from pool
    all_winning = list(combinations(sorted(pool_numbers), winning_count))
    total = len(all_winning)

    best_covered = -1
    best_indices = None

    for indices in combinations(range(len(full_tickets)), n_keep):
        subset = [full_tickets[i] for i in indices]
        covered = 0
        for winning in all_winning:
            winning_set = set(winning)
            for ticket in subset:
                if len(set(ticket).intersection(winning_set)) >= guarantee_count:
                    covered += 1
                    break
        if covered > best_covered:
            best_covered = covered
            best_indices = list(indices)
            if covered == total:
                break  # Can't do better than 100%

    return best_indices, best_covered, total


# --- Comparison Display ------------------------------------------------------

def verify_current_subset():
    """Check whether the current 12-ticket subset holds the 3-if-4 guarantee."""
    wheel_numbers = [9, 11, 14, 15, 22, 23, 24, 25, 33, 35, 39, 40]

    # Current 12 tickets (from post-mortems weeks 6-11)
    current_12 = [
        [9, 14, 23, 25, 35, 40],
        [9, 11, 14, 15, 22, 23],
        [9, 11, 14, 24, 25, 33],
        [9, 11, 14, 35, 39, 40],
        [9, 15, 22, 24, 25, 35],
        [9, 15, 23, 33, 39, 40],
        [9, 23, 25, 33, 35, 40],
        [11, 22, 23, 25, 35, 39],
        [14, 15, 22, 25, 39, 40],
        [14, 15, 23, 25, 33, 35],
        [14, 22, 23, 24, 35, 40],
        [14, 24, 25, 33, 35, 39],
    ]

    wheel = LotteryWheel()
    v, failed, total, covered = wheel.verify_guarantee(current_12, wheel_numbers, 4, 3)

    print("=" * 70)
    print("CURRENT 12-TICKET SUBSET VERIFICATION")
    print("=" * 70)
    print(f"\nGuarantee: 3-if-4 (need 3+ matches when 4 of 12 hit)")
    print(f"Coverage:  {covered}/{total} ({100*covered/total:.1f}%)")
    if v:
        print("Status:    PASS - guarantee holds!")
    else:
        print(f"Status:    FAIL - {len(failed)} gaps")
        print(f"\nFailing combinations (wheel numbers where guarantee breaks):")
        for f in failed:
            print(f"  {list(f)}")

    # Also verify the full 16
    tickets_16 = wheel.generate_3if4_wheel(wheel_numbers)
    v16, _, t16, c16 = wheel.verify_guarantee(tickets_16, wheel_numbers, 4, 3)
    print(f"\nFull 16-ticket wheel: {c16}/{t16} ({100*c16/t16:.1f}%) - {'PASS' if v16 else 'FAIL'}")


def find_best_12():
    """Find the optimal 12 tickets from the 16-ticket 3-if-4 wheel."""
    wheel_numbers = [9, 11, 14, 15, 22, 23, 24, 25, 33, 35, 39, 40]
    wheel = LotteryWheel()
    full_tickets = wheel.generate_3if4_wheel(wheel_numbers)

    print("=" * 70)
    print("FINDING OPTIMAL 12-OF-16 SUBSET")
    print("=" * 70)
    print(f"\nSearching all C(16,12) = {comb(16,12)} subsets...")

    best_idx, covered, total = find_best_subset(full_tickets, wheel_numbers, 12)

    print(f"\nBest 12-ticket subset covers: {covered}/{total} ({100*covered/total:.1f}%)")
    print(f"\nKeep tickets (1-indexed): {[i+1 for i in best_idx]}")
    print(f"Drop tickets (1-indexed): {[i+1 for i in range(16) if i not in best_idx]}")

    print(f"\nOptimal 12 tickets:")
    for j, i in enumerate(best_idx, 1):
        print(f"  {j:2d}. {full_tickets[i]}")

    # Verify the best subset
    subset = [full_tickets[i] for i in best_idx]
    v, failed, t, c = wheel.verify_guarantee(subset, wheel_numbers, 4, 3)
    if not v:
        print(f"\nGap combinations ({len(failed)}):")
        for f in failed:
            print(f"  {list(f)}")

    return subset


def run_comparison(n_sims: int = 100_000):
    """Run Monte Carlo comparison of all strategies."""
    wheel_numbers_12 = [9, 11, 14, 15, 22, 23, 24, 25, 33, 35, 39, 40]
    wheel_numbers_10 = wheel_numbers_12[:10]  # First 10
    wheel_numbers_9 = wheel_numbers_12[:9]    # First 9
    wheel = LotteryWheel()

    strategies = []

    # Strategy A: Current 12-ticket subset
    current_12 = [
        {"numbers": [9, 14, 23, 25, 35, 40], "reserve": 11},
        {"numbers": [9, 11, 14, 15, 22, 23], "reserve": 24},
        {"numbers": [9, 11, 14, 24, 25, 33], "reserve": 22},
        {"numbers": [9, 11, 14, 35, 39, 40], "reserve": 23},
        {"numbers": [9, 15, 22, 24, 25, 35], "reserve": 33},
        {"numbers": [9, 15, 23, 33, 39, 40], "reserve": 25},
        {"numbers": [9, 23, 25, 33, 35, 40], "reserve": 14},
        {"numbers": [11, 22, 23, 25, 35, 39], "reserve": 33},
        {"numbers": [14, 15, 22, 25, 39, 40], "reserve": 9},
        {"numbers": [14, 15, 23, 25, 33, 35], "reserve": 11},
        {"numbers": [14, 22, 23, 24, 35, 40], "reserve": 15},
        {"numbers": [14, 24, 25, 33, 35, 39], "reserve": 22},
    ]
    strategies.append(("A: Current 12/16", current_12, wheel_numbers_12, "3if4"))

    # Strategy B: Full 16-ticket 3-if-4
    tickets_16 = make_tickets(wheel_numbers_12, "3if4")
    strategies.append(("B: Full 3-if-4 (16)", tickets_16, wheel_numbers_12, "3if4"))

    # Strategy C: 3-if-5 (9 tickets)
    tickets_9_3if5 = make_tickets(wheel_numbers_12, "3if5")
    strategies.append(("C: 3-if-5 (9)", tickets_9_3if5, wheel_numbers_12, "3if5"))

    # Strategy D: 10-number pool 3-if-4 (8 tickets)
    tickets_10 = make_tickets(wheel_numbers_10, "3if4_10")
    strategies.append(("D: Pool-10 3-if-4 (8)", tickets_10, wheel_numbers_10, "3if4"))

    # Strategy E: 9-number pool 3-if-4 (7 tickets)
    tickets_9 = make_tickets(wheel_numbers_9, "3if4_9")
    strategies.append(("E: Pool-9 3-if-4 (7)", tickets_9, wheel_numbers_9, "3if4"))

    print("=" * 70)
    print(f"STRATEGY COMPARISON (Monte Carlo, {n_sims:,} simulated weeks)")
    print("=" * 70)

    # Verify guarantees first
    print(f"\n{'_' * 70}")
    print("GUARANTEE VERIFICATION:")
    print(f"{'_' * 70}")
    for name, tickets, pool, wtype in strategies:
        raw = [t["numbers"] for t in tickets]
        if wtype == "3if4":
            _, _, total, covered = wheel.verify_guarantee(raw, pool, 4, 3)
            guar_str = f"3-if-4: {covered}/{total} ({100*covered/total:.1f}%)"
        elif wtype == "3if5":
            _, _, total, covered = wheel.verify_guarantee(raw, pool, 5, 3)
            guar_str = f"3-if-5: {covered}/{total} ({100*covered/total:.1f}%)"
        else:
            guar_str = "N/A"
        print(f"  {name:28s} {guar_str}")

    # Run simulations
    print(f"\n{'_' * 70}")
    print("MONTE CARLO RESULTS:")
    print(f"{'_' * 70}")

    results = []
    for name, tickets, pool, wtype in strategies:
        print(f"\n  Simulating {name}...", end=" ", flush=True)
        r = monte_carlo(tickets, n_sims=n_sims)
        r["name"] = name
        results.append(r)
        print("done")

    # Display comparison table
    print(f"\n{'=' * 70}")
    print("COMPARISON TABLE:")
    print(f"{'=' * 70}")

    header = f"{'Strategy':28s} | {'Tix':>3s} | {'Cost':>5s} | {'Avg Win':>7s} | {'ROI':>6s} | {'P(win)':>6s} | {'P(BE)':>5s}"
    print(header)
    print("-" * len(header))

    for r in results:
        print(f"{r['name']:28s} | {r['tickets']:3d} | EUR{r['cost_per_week']:>3.0f} | "
              f"EUR{r['avg_weekly_return']:>5.1f} | {r['roi_pct']:>5.1f}% | "
              f"{r['p_any_win']:>5.1f}% | {r['p_break_even']:>4.1f}%")

    # Percentile breakdown
    print(f"\n{'_' * 70}")
    print("WEEKLY RETURN PERCENTILES:")
    print(f"{'_' * 70}")

    header2 = f"{'Strategy':28s} | {'P10':>6s} | {'P50':>6s} | {'P90':>6s} | {'P99':>6s} | {'Max':>8s}"
    print(header2)
    print("-" * len(header2))

    for r in results:
        print(f"{r['name']:28s} | EUR{r['p10']:>3.0f} | EUR{r['p50']:>3.0f} | "
              f"EUR{r['p90']:>3.0f} | EUR{r['p99']:>3.0f} | EUR{r['max_won']:>6.0f}")

    # Recommendation
    print(f"\n{'=' * 70}")
    print("ANALYSIS:")
    print(f"{'=' * 70}")

    best_roi = max(results, key=lambda r: r["roi_pct"])
    lowest_cost = min(results, key=lambda r: r["cost_per_week"])
    best_win_rate = max(results, key=lambda r: r["p_any_win"])

    print(f"  Best ROI:          {best_roi['name']} ({best_roi['roi_pct']}%)")
    print(f"  Lowest cost:       {lowest_cost['name']} (EUR {lowest_cost['cost_per_week']}/week)")
    print(f"  Highest win rate:  {best_win_rate['name']} ({best_win_rate['p_any_win']}%)")

    print(f"\n  Key insight: All strategies have negative expected value (as expected")
    print(f"  for lottery). The question is which minimizes losses while maintaining")
    print(f"  a reasonable chance at bigger prizes.")
    print("=" * 70)


# --- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Lottery strategy optimizer")
    parser.add_argument("--verify-current", action="store_true",
                        help="Verify current 12-ticket subset guarantee")
    parser.add_argument("--find-best-12", action="store_true",
                        help="Find optimal 12-of-16 ticket subset")
    parser.add_argument("--sims", type=int, default=100_000,
                        help="Number of Monte Carlo simulations (default: 100000)")
    args = parser.parse_args()

    if args.verify_current:
        verify_current_subset()
    elif args.find_best_12:
        find_best_12()
    else:
        # Default: run everything
        verify_current_subset()
        print()
        find_best_12()
        print()
        run_comparison(n_sims=args.sims)


if __name__ == "__main__":
    main()
