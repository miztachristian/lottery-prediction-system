#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST-MORTEM ANALYSIS: January 24, 2026
Wheel System - Week 6 (12 tickets played)
"""

import json
from datetime import datetime

# Actual results
lotto_result = [3, 7, 8, 36, 42, 44]
lotto_reserve = 26
xl_result = [16, 18, 26, 27, 42, 43]
xl_reserve = 38

# The wheel numbers (consistent)
wheel_numbers = [9, 11, 14, 15, 22, 23, 24, 25, 33, 35, 39, 40]

# The 12 tickets played (including wife's pick)
tickets = [
    {"numbers": [9, 14, 23, 25, 35, 40], "reserve": 11, "note": "Wife's Pick"},
    {"numbers": [9, 11, 14, 15, 22, 23], "reserve": 24, "note": ""},
    {"numbers": [9, 11, 14, 24, 25, 33], "reserve": 22, "note": ""},
    {"numbers": [9, 11, 14, 35, 39, 40], "reserve": 23, "note": ""},
    {"numbers": [9, 15, 22, 24, 25, 35], "reserve": 33, "note": ""},
    {"numbers": [9, 15, 23, 33, 39, 40], "reserve": 25, "note": ""},
    {"numbers": [9, 23, 25, 33, 35, 40], "reserve": 14, "note": ""},
    {"numbers": [11, 22, 23, 25, 35, 39], "reserve": 33, "note": ""},
    {"numbers": [14, 15, 22, 25, 39, 40], "reserve": 9, "note": ""},
    {"numbers": [14, 15, 23, 25, 33, 35], "reserve": 11, "note": ""},
    {"numbers": [14, 22, 23, 24, 35, 40], "reserve": 15, "note": ""},
    {"numbers": [14, 24, 25, 33, 35, 39], "reserve": 22, "note": ""},
]

print("=" * 80)
print("POST-MORTEM: JANUARY 24, 2026 - WHEEL SYSTEM (WEEK 6)")
print("=" * 80)

print(f"\n{'─' * 80}")
print("ACTUAL RESULTS:")
print(f"{'─' * 80}")
print(f"Lotto:    {sorted(lotto_result)} | Reserve: {lotto_reserve}")
print(f"Lotto XL: {sorted(xl_result)} | Reserve: {xl_reserve}")

print(f"\n{'─' * 80}")
print("YOUR WHEEL NUMBERS:")
print(f"{'─' * 80}")
print(f"{wheel_numbers}")

# Check how many wheel numbers hit
lotto_hits_from_wheel = set(wheel_numbers).intersection(set(lotto_result))
xl_hits_from_wheel = set(wheel_numbers).intersection(set(xl_result))

print(f"\n{'─' * 80}")
print("WHEEL PERFORMANCE:")
print(f"{'─' * 80}")
print(f"Lotto draw:  {len(lotto_hits_from_wheel)}/12 wheel numbers hit → {sorted(list(lotto_hits_from_wheel)) if lotto_hits_from_wheel else 'NONE'}")
print(f"XL draw:     {len(xl_hits_from_wheel)}/12 wheel numbers hit → {sorted(list(xl_hits_from_wheel)) if xl_hits_from_wheel else 'NONE'}")

print(f"\n{'─' * 80}")
print("GUARANTEE STATUS:")
print(f"{'─' * 80}")
if len(lotto_hits_from_wheel) >= 4:
    print("🎉 LOTTO: GUARANTEE ACTIVATED! (4+ wheel numbers hit)")
else:
    print(f"   Lotto: Guarantee NOT activated (need 4+, got {len(lotto_hits_from_wheel)})")

if len(xl_hits_from_wheel) >= 4:
    print("🎉 XL: GUARANTEE ACTIVATED! (4+ wheel numbers hit)")
else:
    print(f"   XL: Guarantee NOT activated (need 4+, got {len(xl_hits_from_wheel)})")

# Analyze each ticket
print(f"\n{'─' * 80}")
print("TICKET ANALYSIS (12 tickets played):")
print(f"{'─' * 80}")

lotto_results = []
xl_results = []

for i, ticket in enumerate(tickets, 1):
    ticket_nums = set(ticket['numbers'])
    reserve_num = ticket['reserve']
    
    # Check against Lotto
    lotto_matches = len(ticket_nums.intersection(set(lotto_result)))
    lotto_matched_nums = sorted(list(ticket_nums.intersection(set(lotto_result))))
    lotto_reserve_hit = (reserve_num == lotto_reserve)
    
    # Lotto prizes
    lotto_prize = "None"
    if lotto_matches == 6 and lotto_reserve_hit:
        lotto_prize = "JACKPOT (6+R)"
    elif lotto_matches == 6:
        lotto_prize = "2nd Prize (6)"
    elif lotto_matches == 5 and lotto_reserve_hit:
        lotto_prize = "€100,000 (5+R)"
    elif lotto_matches == 5:
        lotto_prize = "€1,000 (5)"
    elif lotto_matches == 4:
        lotto_prize = "€50 (4)"
    elif lotto_matches == 3:
        lotto_prize = "FREE TICKET (3)"
    
    # Check against XL
    xl_matches = len(ticket_nums.intersection(set(xl_result)))
    xl_matched_nums = sorted(list(ticket_nums.intersection(set(xl_result))))
    xl_reserve_hit = (reserve_num == xl_reserve)
    
    # XL prizes
    xl_prize = "None"
    xl_cash = 0
    if xl_matches == 6 and xl_reserve_hit:
        xl_prize = "JACKPOT (6+R)"
        xl_cash = 1000000
    elif xl_matches == 6:
        xl_prize = "€1,000,000 (6)"
        xl_cash = 1000000
    elif xl_matches == 5 and xl_reserve_hit:
        xl_prize = "€25,000 (5+R)"
        xl_cash = 25000
    elif xl_matches == 5:
        xl_prize = "€1,000 (5)"
        xl_cash = 1000
    elif xl_matches == 4 and xl_reserve_hit:
        xl_prize = "€25 (4+R)"
        xl_cash = 25
    elif xl_matches == 4:
        xl_prize = "€15 (4)"
        xl_cash = 15
    elif xl_matches == 3 and xl_reserve_hit:
        xl_prize = "€10 (3+R)"
        xl_cash = 10
    elif xl_matches == 3:
        xl_prize = "€5 (3)"
        xl_cash = 5
    elif xl_matches == 2 and xl_reserve_hit:
        xl_prize = "€2 (2+R)"
        xl_cash = 2
    elif xl_matches == 2:
        xl_prize = "€1 (2)"
        xl_cash = 1
    
    lotto_results.append({
        'ticket': i,
        'numbers': ticket['numbers'],
        'reserve': reserve_num,
        'matches': lotto_matches,
        'matched_nums': lotto_matched_nums,
        'prize': lotto_prize,
        'note': ticket['note']
    })
    
    xl_results.append({
        'ticket': i,
        'numbers': ticket['numbers'],
        'reserve': reserve_num,
        'matches': xl_matches,
        'matched_nums': xl_matched_nums,
        'prize': xl_prize,
        'cash': xl_cash,
        'note': ticket['note']
    })

# Display Lotto results
print("\nLOTTO DRAW:")
best_lotto = max(lotto_results, key=lambda x: x['matches'])
for r in lotto_results:
    status = "✓" if r['prize'] != "None" else "✗"
    note_str = f" ({r['note']})" if r['note'] else ""
    print(f"  {r['ticket']:2d}. {r['numbers']} (R:{r['reserve']:2d}) → {r['matches']} hits {r['matched_nums']} {status} {r['prize']}{note_str}")

# Display XL results
print("\nLOTTO XL DRAW:")
best_xl = max(xl_results, key=lambda x: x['matches'])
for r in xl_results:
    status = "✓" if r['prize'] != "None" else "✗"
    note_str = f" ({r['note']})" if r['note'] else ""
    print(f"  {r['ticket']:2d}. {r['numbers']} (R:{r['reserve']:2d}) → {r['matches']} hits {r['matched_nums']} {status} {r['prize']}{note_str}")

# Summary
lotto_prizes = [r['prize'] for r in lotto_results if r['prize'] != "None"]
xl_prizes = [r['prize'] for r in xl_results if r['prize'] != "None"]
total_cash = sum(r['cash'] for r in xl_results)

print(f"\n{'=' * 80}")
print("SUMMARY:")
print(f"{'=' * 80}")
print(f"Best Lotto result:  {best_lotto['matches']} hits → {best_lotto['prize']}")
print(f"Best XL result:     {best_xl['matches']} hits → {best_xl['prize']}")
print(f"\nLotto prizes won: {len(lotto_prizes)} → {lotto_prizes if lotto_prizes else 'None'}")
print(f"XL prizes won:    {len(xl_prizes)} → {xl_prizes if xl_prizes else 'None'}")
print(f"\nTotal XL cash won: €{total_cash}")
print(f"Cost of 12 tickets: €{12 * 3}  (€2 base + €1 XL per ticket)")
print(f"Net result: €{total_cash - 36} {'PROFIT' if total_cash > 36 else 'LOSS'}")

print(f"\n{'=' * 80}")
print("WEEK 6 ANALYSIS:")
print(f"{'=' * 80}")

if len(lotto_hits_from_wheel) == 0 and len(xl_hits_from_wheel) == 0:
    print("⚠️  COMPLETE MISS: Zero wheel numbers hit in either draw")
    print("    This is expected ~13.6% of the time (see probability analysis)")
    print("    The wheel is still valid - keep playing the same numbers!")
    
    # Show which numbers hit that weren't in the wheel
    lotto_outside = sorted(list(set(lotto_result) - set(wheel_numbers)))
    xl_outside = sorted(list(set(xl_result) - set(wheel_numbers)))
    
    print(f"\n    Lotto numbers OUTSIDE wheel: {lotto_outside}")
    print(f"    XL numbers OUTSIDE wheel:    {xl_outside}")
    print(f"\n    NOTE: This is random variance, NOT a problem with the wheel.")
    print(f"          Do NOT change your 12 numbers based on this result!")

print("\n" + "=" * 80)
print("CUMULATIVE PERFORMANCE (Weeks 5-6):")
print("=" * 80)
print("Week 5 (Jan 17): XL guarantee activated → €43 won")
print("Week 6 (Jan 24): 0 hits → €0 won")
print("Total: €43 won | Cost: €84 | Net: -€41")
print("\nLong-term expectation: ~1 guarantee activation every 14 weeks")
print("Continue playing the same 12 wheel numbers!")
print("=" * 80)
