#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WEEK 5 PREDICTION GENERATOR - Wheel System Implementation
==========================================================

This replaces ALL previous prediction strategies with the mathematically
sound Wheel System approach.

Date: January 17, 2026
Strategy: 3-if-4 Abbreviated Wheel
Guarantee: If 4 of our 12 numbers appear in the winning 6,
           at least one ticket will have 3+ matches.
"""

import json
import datetime
from wheel_system import LotteryWheel, select_wheel_numbers_hybrid

def generate_week5_predictions():
    """
    Generate predictions for January 17, 2026 using the Wheel System.
    """
    
    # Initialize wheel
    wheel = LotteryWheel(pool_size=12, ticket_size=6)
    
    # Select our 12 numbers using hybrid strategy
    # This is reproducible (seeded) so we get the same numbers if run multiple times
    wheel_numbers = select_wheel_numbers_hybrid()
    
    # Generate the 16-ticket wheel with 3-if-4 guarantee
    tickets = wheel.generate_3if4_wheel(wheel_numbers)
    
    # Verify the guarantee before saving
    verified, _, _, _ = wheel.verify_guarantee(tickets, wheel_numbers, winning_count=4, guarantee=3)
    
    if not verified:
        raise RuntimeError("Wheel verification failed! Do not use these tickets.")
    
    # Assign reserve numbers
    # We'll rotate through the wheel numbers that aren't in each ticket
    final_tickets = []
    reserve_rotation = 0
    
    for i, ticket in enumerate(tickets):
        # Find numbers in the wheel that aren't in this ticket
        available_reserves = [n for n in wheel_numbers if n not in ticket]
        # Rotate through them
        reserve = available_reserves[reserve_rotation % len(available_reserves)]
        reserve_rotation += 1
        
        # ALL 16 tickets are Lotto XL (gives entry to BOTH Lotto and XL draws)
        ticket_type = "Lotto XL"
        
        final_tickets.append({
            "numbers": ticket,
            "reserve": reserve,
            "type": ticket_type,
            "rationale": f"Wheel System 3-if-4 (Ticket {i+1}/16) - Valid for BOTH draws"
        })
    
    # Build output data
    output_data = {
        "draw_date": "2026-01-17",
        "game": "xl_and_lotto",
        "predicted_at": datetime.datetime.now().isoformat(),
        "strategy": "WHEEL_SYSTEM_3IF4",
        "strategy_notes": "Week 5: Mathematically guaranteed 3-match if 4 of 12 numbers hit",
        "wheel_numbers": wheel_numbers,
        "guarantee": "If ANY 4 of the 12 wheel numbers appear in the winning 6, at least one ticket has 3+ matches",
        "tickets": final_tickets
    }
    
    # Load existing history
    try:
        with open("predictions_history.json", "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = {"weeks": []}
    
    # Remove any existing entry for this date
    history['weeks'] = [w for w in history['weeks'] if w['draw_date'] != "2026-01-17"]
    
    # Append new predictions
    history['weeks'].append(output_data)
    
    # Save
    with open("predictions_history.json", "w") as f:
        json.dump(history, f, indent=2)
    
    return output_data, wheel_numbers, tickets


def display_predictions(output_data, wheel_numbers, tickets):
    """
    Display the generated predictions in a clear format.
    """
    print("=" * 80)
    print("WHEEL SYSTEM PREDICTIONS - January 17, 2026")
    print("=" * 80)
    
    print(f"\n{'─' * 80}")
    print("THE 12 WHEEL NUMBERS:")
    print(f"{'─' * 80}")
    print(f"  {wheel_numbers}")
    print(f"  Low (1-15):   {[n for n in wheel_numbers if n <= 15]}")
    print(f"  Mid (16-30):  {[n for n in wheel_numbers if 16 <= n <= 30]}")
    print(f"  High (31-45): {[n for n in wheel_numbers if n >= 31]}")
    
    print(f"\n{'─' * 80}")
    print("MATHEMATICAL GUARANTEE:")
    print(f"{'─' * 80}")
    print("  ✓ If 4+ of these 12 numbers appear in the winning 6:")
    print("    → At least ONE ticket will have 3+ matches (FREE TICKET)")
    print("  ✓ If 5+ hit: Very likely to have 4+ matches (€50+)")
    print("  ✓ If all 6 hit from our 12: Strong chance of major prize")
    
    print(f"\n{'─' * 80}")
    print("YOUR 16 LOTTO XL TICKETS:")
    print("(Each ticket enters BOTH the Lotto draw AND the XL draw)")
    print(f"{'─' * 80}")
    
    print("\nAll tickets (Lotto XL - valid for both draws):")
    for i, t in enumerate(output_data['tickets'], 1):
        print(f"  {i:2d}. {t['numbers']}  Reserve: {t['reserve']}")
    
    print(f"\n{'─' * 80}")
    print("PROBABILITY ANALYSIS:")
    print(f"{'─' * 80}")
    
    # Calculate actual probabilities
    from math import comb
    
    # P(exactly k of our 12 are in winning 6) = C(12,k) * C(33,6-k) / C(45,6)
    total_combos = comb(45, 6)  # 8,145,060
    
    probs = {}
    for k in range(7):  # 0 to 6
        if k <= 6 and (6-k) <= 33:
            probs[k] = (comb(12, k) * comb(33, 6-k)) / total_combos
        else:
            probs[k] = 0
    
    print("  Probability that X of our 12 numbers are in the winning 6:")
    print(f"    0 hits: {100*probs[0]:.2f}%")
    print(f"    1 hit:  {100*probs[1]:.2f}%")
    print(f"    2 hits: {100*probs[2]:.2f}%")
    print(f"    3 hits: {100*probs[3]:.2f}%  ← Possible free ticket")
    print(f"    4 hits: {100*probs[4]:.2f}%  ← GUARANTEED free ticket (wheel)")
    print(f"    5 hits: {100*probs[5]:.2f}%  ← Likely €50+")
    print(f"    6 hits: {100*probs[6]:.4f}%  ← JACKPOT territory")
    
    p_4plus = sum(probs[k] for k in range(4, 7))
    print(f"\n  P(4+ hits in ONE draw) = {100*p_4plus:.2f}%")
    
    # With Lotto XL, you get TWO independent draws
    p_miss_both = (1 - p_4plus) ** 2
    p_hit_at_least_one = 1 - p_miss_both
    print(f"  P(4+ hits in EITHER Lotto OR XL draw) = {100*p_hit_at_least_one:.2f}%")
    print(f"  → Expected: 1 guaranteed prize every ~{int(1/p_hit_at_least_one)} weeks")
    
    print(f"\n{'=' * 80}")
    print("LOTTO XL ADVANTAGE:")
    print(f"{'=' * 80}")
    print("""
    With Lotto XL, each ticket enters TWO separate draws:
    
    1. The LOTTO draw (3 hits = free ticket)
    2. The XL draw (3 hits = €5 CASH)
    
    XL PRIZE TABLE:
    ┌─────────────────────┬────────────┐
    │ 6 numbers           │ €1,000,000 │
    │ 5 + reserve         │ €25,000    │
    │ 5 numbers           │ €1,000     │
    │ 4 + reserve         │ €25        │
    │ 4 numbers           │ €15        │
    │ 3 + reserve         │ €10        │
    │ 3 numbers           │ €5         │
    │ 2 + reserve         │ €2         │
    │ 2 numbers           │ €1         │
    └─────────────────────┴────────────┘
    
    This means your 16 tickets give you 32 CHANCES to win!
    
    With our wheel guarantee (3-if-4):
    → If 4+ hit in Lotto draw: At least 1 free ticket
    → If 4+ hit in XL draw: At least €5 cash
    """)
    
    print(f"\n{'=' * 80}")
    print("IMPORTANT NOTES:")
    print(f"{'=' * 80}")
    print("""
    1. These tickets are MATHEMATICALLY DESIGNED, not randomly generated.
    
    2. The GUARANTEE only activates if your numbers hit:
       - If none of the 12 wheel numbers are in the winning 6, you win nothing.
       - If 1-3 of your numbers hit, you MIGHT win (but no guarantee).
       - If 4+ of your numbers hit, you WILL win at least a free ticket.
    
    3. This is a LONG-TERM strategy:
       - Play the SAME 12 numbers every week.
       - Over time, the guarantee will trigger.
       - Do not change numbers based on "hot/cold" analysis.
    
    4. Your 12 numbers should be played CONSISTENTLY for 20+ weeks
       to see the mathematical expectation play out.
    """)
    print("=" * 80)


if __name__ == "__main__":
    output_data, wheel_numbers, tickets = generate_week5_predictions()
    display_predictions(output_data, wheel_numbers, tickets)
    print("\n✓ Predictions saved to predictions_history.json")
