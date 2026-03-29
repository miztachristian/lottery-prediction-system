#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOMATED POST-MORTEM ANALYSIS
==============================

Reusable tool for weekly draw analysis. Replaces the per-week post_mortem_*.py scripts.

Usage:
    # Normal week (2 draws)
    python post_mortem.py --lotto 3,4,11,29,34,40 --lotto-r 2 --xl 20,30,37,38,40,44 --xl-r 10

    # Super Saturday (4 draws)
    python post_mortem.py --lotto 3,4,11,29,34,40 --lotto-r 2 --xl 20,30,37,38,40,44 --xl-r 10 \
                          --lotto2 4,8,9,10,16,30 --lotto2-r 37 --xl2 4,5,29,33,39,41 --xl2-r 34

    # With explicit date and week number
    python post_mortem.py --date 2026-03-07 --week 12 --lotto ...

    # Save results to predictions_history.json
    python post_mortem.py --save --lotto ...
"""

import argparse
import json
import os
import sys
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional


# --- Prize Tables -----------------------------------------------------------

def get_lotto_prize(matches: int, reserve_hit: bool) -> Tuple[str, float, bool]:
    """Calculate Lotto prize. Returns (description, cash_value, is_free_ticket)."""
    if matches == 6:
        return ("JACKPOT (6+R)" if reserve_hit else "2nd Prize (6)", 0, False)
    elif matches == 5:
        if reserve_hit:
            return ("EUR 100,000 (5+R)", 100_000, False)
        return ("EUR 1,000 (5)", 1_000, False)
    elif matches == 4:
        return ("EUR 50 (4)", 50, False)
    elif matches == 3:
        return ("FREE TICKET (3)", 0, True)
    elif matches == 2 and reserve_hit:
        return ("FREE TICKET (2+R)", 0, True)
    return ("None", 0, False)


def get_xl_prize(matches: int, reserve_hit: bool) -> Tuple[str, float, bool]:
    """Calculate Lotto XL prize. Returns (description, cash_value, is_free_ticket)."""
    if matches == 6:
        return ("EUR 1,000,000 (6)", 1_000_000, False)
    elif matches == 5:
        if reserve_hit:
            return ("EUR 25,000 (5+R)", 25_000, False)
        return ("EUR 1,000 (5)", 1_000, False)
    elif matches == 4:
        if reserve_hit:
            return ("EUR 25 (4+R)", 25, False)
        return ("EUR 15 (4)", 15, False)
    elif matches == 3:
        if reserve_hit:
            return ("EUR 10 (3+R)", 10, False)
        return ("EUR 5 (3)", 5, False)
    elif matches == 2:
        if reserve_hit:
            return ("EUR 2 (2+R)", 2, False)
        return ("EUR 1 (2)", 1, False)
    return ("None", 0, False)


# --- Analysis ---------------------------------------------------------------

def analyze_tickets_vs_draw(tickets: List[Dict], draw_numbers: List[int],
                            draw_reserve: int, game_type: str) -> List[Dict]:
    """Analyze all tickets against a single draw."""
    prize_fn = get_lotto_prize if game_type == "lotto" else get_xl_prize
    results = []

    for i, ticket in enumerate(tickets, 1):
        t_nums = set(ticket["numbers"])
        d_nums = set(draw_numbers)
        matches = len(t_nums.intersection(d_nums))
        matched_nums = sorted(list(t_nums.intersection(d_nums)))
        reserve_hit = ticket["reserve"] == draw_reserve
        prize_name, cash, is_free = prize_fn(matches, reserve_hit)

        results.append({
            "ticket_num": i,
            "numbers": ticket["numbers"],
            "reserve": ticket["reserve"],
            "matches": matches,
            "matched_nums": matched_nums,
            "reserve_hit": reserve_hit,
            "prize": prize_name,
            "cash": cash,
            "free_ticket": is_free,
        })
    return results


def load_config() -> Tuple[List[int], List[Dict]]:
    """Load wheel numbers and tickets from predictions_history.json."""
    history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions_history.json")
    if not os.path.exists(history_path):
        print("ERROR: predictions_history.json not found.")
        sys.exit(1)

    with open(history_path, "r") as f:
        history = json.load(f)

    # Find most recent week with tickets
    for week in reversed(history.get("weeks", [])):
        if "wheel_numbers" in week and "tickets" in week:
            wheel_numbers = week["wheel_numbers"]
            tickets = week["tickets"]
            normalized = []
            for t in tickets:
                normalized.append({
                    "numbers": t["numbers"],
                    "reserve": t["reserve"],
                })
            return wheel_numbers, normalized

    print("ERROR: No week with wheel_numbers and tickets found in predictions_history.json")
    sys.exit(1)


def load_cumulative_history() -> List[Dict]:
    """Load all past weeks that have performance data for cumulative P&L."""
    history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions_history.json")
    if not os.path.exists(history_path):
        return []

    with open(history_path, "r") as f:
        history = json.load(f)

    results = []
    for week in history.get("weeks", []):
        perf = week.get("performance") or week.get("summary")
        if perf:
            summary = perf.get("summary", perf)
            won = summary.get("total_cash_won", 0)
            cost = summary.get("cost", 0)
            results.append({
                "date": week.get("draw_date", "unknown"),
                "won": won,
                "cost": cost,
                "net": won - cost,
            })
    return results


# --- Display -----------------------------------------------------------------

def print_analysis(draws: List[Dict], wheel_numbers: List[int], tickets: List[Dict],
                   week_num: Optional[int] = None, draw_date: Optional[str] = None) -> Dict:
    """Print full post-mortem analysis. Returns summary dict."""
    is_super = len(draws) > 2
    date_str = draw_date or date.today().isoformat()
    week_str = f" (WEEK {week_num})" if week_num else ""
    type_str = " - SUPER SATURDAY" if is_super else ""

    print("=" * 80)
    print(f"POST-MORTEM: {date_str}{type_str}{week_str}")
    print("=" * 80)

    # Actual results
    print(f"\n{'_' * 80}")
    print("ACTUAL RESULTS:")
    print(f"{'_' * 80}")
    for d in draws:
        label = d["label"]
        print(f"  {label:14s} {sorted(d['numbers'])} | Reserve: {d['reserve']}")

    # Wheel numbers
    print(f"\n{'_' * 80}")
    print("YOUR WHEEL NUMBERS:")
    print(f"{'_' * 80}")
    print(f"  {wheel_numbers}")

    # Wheel performance per draw
    print(f"\n{'_' * 80}")
    print("WHEEL PERFORMANCE:")
    print(f"{'_' * 80}")
    for d in draws:
        hits = set(wheel_numbers).intersection(set(d["numbers"]))
        d["wheel_hits"] = len(hits)
        d["wheel_hit_nums"] = sorted(list(hits))
        print(f"  {d['label']:14s} {len(hits)}/12 wheel numbers hit -> "
              f"{sorted(list(hits)) if hits else 'NONE'}")

    # Guarantee status
    print(f"\n{'_' * 80}")
    print("GUARANTEE STATUS:")
    print(f"{'_' * 80}")
    for d in draws:
        if d["wheel_hits"] >= 4:
            print(f"  {d['label']}: GUARANTEE ACTIVATED! (4+ wheel numbers hit)")
        else:
            print(f"  {d['label']}: Guarantee NOT activated (need 4+, got {d['wheel_hits']})")

    # Ticket analysis per draw
    total_cash = 0
    total_free = 0
    all_draw_results = []

    print(f"\n{'_' * 80}")
    print(f"TICKET ANALYSIS ({len(tickets)} tickets played across {len(draws)} draws):")
    print(f"{'_' * 80}")

    for d in draws:
        game_type = d["game_type"]
        results = analyze_tickets_vs_draw(tickets, d["numbers"], d["reserve"], game_type)
        all_draw_results.append({"draw": d, "results": results})

        print(f"\n  {d['label'].upper()} DRAW:")
        for r in results:
            marker = "+" if r["prize"] != "None" else " "
            prize_str = f" | {r['prize']}" if r["prize"] != "None" else ""
            print(f"    {marker} {r['ticket_num']:2d}. {r['numbers']} (R:{r['reserve']:2d}) "
                  f"-> {r['matches']} hits {r['matched_nums']}{prize_str}")

        draw_cash = sum(r["cash"] for r in results)
        draw_free = sum(1 for r in results if r["free_ticket"])
        total_cash += draw_cash
        total_free += draw_free

    # Summary
    cost = len(tickets) * 3
    net = total_cash - cost

    print(f"\n{'=' * 80}")
    print("SUMMARY:")
    print(f"{'=' * 80}")
    print(f"  Total cash won:     EUR {total_cash}")
    print(f"  Free tickets won:   {total_free}")
    print(f"  Cost ({len(tickets)} tickets):  EUR {cost}")
    print(f"  Net result:         EUR {net} {'PROFIT' if net > 0 else 'LOSS'}"
          f"{f' (plus {total_free} free tickets)' if total_free > 0 else ''}")

    # Cumulative P&L
    past = load_cumulative_history()
    if past:
        print(f"\n{'=' * 80}")
        print("CUMULATIVE PERFORMANCE:")
        print(f"{'=' * 80}")
        for p in past:
            print(f"  {p['date']}: EUR {p['won']:>5} won | net EUR {p['won'] - p['cost']}")
        print(f"  {date_str}: EUR {total_cash:>5} won | net EUR {net}")
        print(f"  {'_' * 76}")
        cum_won = sum(p["won"] for p in past) + total_cash
        cum_cost = sum(p["cost"] for p in past) + cost
        print(f"  TOTAL: EUR {cum_won} won | EUR {cum_cost} cost | Net: EUR {cum_won - cum_cost}")

    print("=" * 80)

    return {
        "total_cash": total_cash,
        "free_tickets": total_free,
        "cost": cost,
        "net": net,
        "draws": all_draw_results,
    }


def save_results(draw_date: str, week_num: Optional[int], results: Dict,
                 wheel_numbers: List[int], tickets: List[Dict]):
    """Save results to predictions_history.json."""
    history_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictions_history.json")

    try:
        with open(history_path, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {"weeks": []}

    draw_data = []
    for dr in results["draws"]:
        d = dr["draw"]
        draw_data.append({
            "type": d["game_type"],
            "label": d["label"],
            "numbers": d["numbers"],
            "reserve": d["reserve"],
            "wheel_hits": d.get("wheel_hits", 0),
            "winning_tickets": [
                {
                    "ticket": r["ticket_num"],
                    "matches": r["matches"],
                    "matched_nums": r["matched_nums"],
                    "reserve_hit": r["reserve_hit"],
                    "prize": r["prize"],
                    "cash": r["cash"],
                }
                for r in dr["results"]
                if r["prize"] != "None"
            ],
        })

    entry = {
        "draw_date": draw_date,
        "week": week_num,
        "game": "xl_and_lotto",
        "strategy": "WHEEL_SYSTEM_3IF4",
        "wheel_numbers": wheel_numbers,
        "tickets_played": len(tickets),
        "cost": results["cost"],
        "draws": draw_data,
        "summary": {
            "total_cash_won": results["total_cash"],
            "free_tickets_won": results["free_tickets"],
            "cost": results["cost"],
            "net": results["net"],
        },
        "analyzed_at": datetime.now().isoformat(),
    }

    # Remove existing entry for this date (allow re-running)
    history["weeks"] = [w for w in history["weeks"] if w.get("draw_date") != draw_date]
    history["weeks"].append(entry)
    history["weeks"].sort(key=lambda w: w.get("draw_date", ""))

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nResults saved to predictions_history.json")


# --- CLI ---------------------------------------------------------------------

def parse_numbers(s: str) -> List[int]:
    """Parse comma-separated numbers."""
    return sorted([int(x.strip()) for x in s.split(",")])


def main():
    parser = argparse.ArgumentParser(description="Automated lottery post-mortem analysis")
    parser.add_argument("--date", type=str, default=None, help="Draw date (YYYY-MM-DD)")
    parser.add_argument("--week", type=int, default=None, help="Week number")
    parser.add_argument("--save", action="store_true", help="Save results to predictions_history.json")

    # Draw 1 (always required)
    parser.add_argument("--lotto", type=str, required=True, help="Lotto numbers (comma-separated)")
    parser.add_argument("--lotto-r", type=int, required=True, help="Lotto reserve number")
    parser.add_argument("--xl", type=str, required=True, help="XL numbers (comma-separated)")
    parser.add_argument("--xl-r", type=int, required=True, help="XL reserve number")

    # Draw 2 (Super Saturday - optional)
    parser.add_argument("--lotto2", type=str, default=None, help="Lotto 2 numbers (Super Saturday)")
    parser.add_argument("--lotto2-r", type=int, default=None, help="Lotto 2 reserve (Super Saturday)")
    parser.add_argument("--xl2", type=str, default=None, help="XL 2 numbers (Super Saturday)")
    parser.add_argument("--xl2-r", type=int, default=None, help="XL 2 reserve (Super Saturday)")

    args = parser.parse_args()

    # Build draws list
    draws = [
        {"label": "Lotto", "numbers": parse_numbers(args.lotto), "reserve": args.lotto_r, "game_type": "lotto"},
        {"label": "Lotto XL", "numbers": parse_numbers(args.xl), "reserve": args.xl_r, "game_type": "xl"},
    ]

    is_super = args.lotto2 is not None
    if is_super:
        if not all([args.lotto2, args.lotto2_r is not None, args.xl2, args.xl2_r is not None]):
            parser.error("Super Saturday requires all of: --lotto2, --lotto2-r, --xl2, --xl2-r")
        draws[0]["label"] = "Lotto 1"
        draws[1]["label"] = "Lotto XL 1"
        draws.append({"label": "Lotto 2", "numbers": parse_numbers(args.lotto2),
                       "reserve": args.lotto2_r, "game_type": "lotto"})
        draws.append({"label": "Lotto XL 2", "numbers": parse_numbers(args.xl2),
                       "reserve": args.xl2_r, "game_type": "xl"})

    # Load config
    wheel_numbers, tickets = load_config()
    draw_date = args.date or date.today().isoformat()

    # Run analysis
    results = print_analysis(draws, wheel_numbers, tickets,
                             week_num=args.week, draw_date=draw_date)

    # Save if requested
    if args.save:
        save_results(draw_date, args.week, results, wheel_numbers, tickets)


if __name__ == "__main__":
    main()
