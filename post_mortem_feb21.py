#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST-MORTEM ANALYSIS: February 21, 2026
Wheel System - Week 10 (12 tickets played)
"""

# Actual results
lotto_result = [4, 5, 12, 30, 35, 39]
lotto_reserve = 25
xl_result = [12, 17, 30, 33, 34, 38]
xl_reserve = 26

# The wheel numbers (consistent)
wheel_numbers = [9, 11, 14, 15, 22, 23, 24, 25, 33, 35, 39, 40]

# The 12 tickets played
tickets = [
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

print("=" * 80)
print("POST-MORTEM: FEBRUARY 21, 2026 - WHEEL SYSTEM (WEEK 10)")
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
lotto_results = []
xl_results = []

for i, ticket in enumerate(tickets, 1):
    ticket_nums = set(ticket['numbers'])
    reserve_num = ticket['reserve']

    # Lotto
    lotto_matches = len(ticket_nums.intersection(set(lotto_result)))
    lotto_matched_nums = sorted(list(ticket_nums.intersection(set(lotto_result))))
    lotto_reserve_hit = (reserve_num == lotto_reserve)
    lotto_prize = "None"
    if lotto_matches == 6: lotto_prize = "JACKPOT" if lotto_reserve_hit else "2nd Prize"
    elif lotto_matches == 5: lotto_prize = "€100,000 (5+R)" if lotto_reserve_hit else "€1,000 (5)"
    elif lotto_matches == 4: lotto_prize = "€50 (4)"
    elif lotto_matches == 3: lotto_prize = "FREE TICKET (3)"

    # XL
    xl_matches = len(ticket_nums.intersection(set(xl_result)))
    xl_matched_nums = sorted(list(ticket_nums.intersection(set(xl_result))))
    xl_reserve_hit = (reserve_num == xl_reserve)
    xl_prize = "None"
    xl_cash = 0
    if xl_matches == 6: xl_prize = "€1,000,000 (6)"; xl_cash = 1000000
    elif xl_matches == 5 and xl_reserve_hit: xl_prize = "€25,000 (5+R)"; xl_cash = 25000
    elif xl_matches == 5: xl_prize = "€1,000 (5)"; xl_cash = 1000
    elif xl_matches == 4 and xl_reserve_hit: xl_prize = "€25 (4+R)"; xl_cash = 25
    elif xl_matches == 4: xl_prize = "€15 (4)"; xl_cash = 15
    elif xl_matches == 3 and xl_reserve_hit: xl_prize = "€10 (3+R)"; xl_cash = 10
    elif xl_matches == 3: xl_prize = "€5 (3)"; xl_cash = 5
    elif xl_matches == 2 and xl_reserve_hit: xl_prize = "€2 (2+R)"; xl_cash = 2
    elif xl_matches == 2: xl_prize = "€1 (2)"; xl_cash = 1

    lotto_results.append({'ticket': i, 'numbers': ticket['numbers'], 'reserve': reserve_num,
                          'matches': lotto_matches, 'matched_nums': lotto_matched_nums, 'prize': lotto_prize})
    xl_results.append({'ticket': i, 'numbers': ticket['numbers'], 'reserve': reserve_num,
                       'matches': xl_matches, 'matched_nums': xl_matched_nums, 'prize': xl_prize, 'cash': xl_cash})

print(f"\n{'─' * 80}")
print("TICKET ANALYSIS (12 tickets played):")
print(f"{'─' * 80}")

print("\nLOTTO DRAW:")
for r in lotto_results:
    status = "✓" if r['prize'] != "None" else "✗"
    print(f"  {r['ticket']:2d}. {r['numbers']} (R:{r['reserve']:2d}) → {r['matches']} hits {r['matched_nums']} {status} {r['prize']}")

print("\nLOTTO XL DRAW:")
for r in xl_results:
    status = "✓" if r['prize'] != "None" else "✗"
    print(f"  {r['ticket']:2d}. {r['numbers']} (R:{r['reserve']:2d}) → {r['matches']} hits {r['matched_nums']} {status} {r['prize']}")

# Summary
best_lotto = max(lotto_results, key=lambda x: x['matches'])
best_xl = max(xl_results, key=lambda x: x['matches'])
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
print(f"Cost of 12 tickets: €36")
print(f"Net result: €{total_cash - 36} {'PROFIT' if total_cash > 36 else 'LOSS'}")

print(f"\n{'=' * 80}")
print("CUMULATIVE PERFORMANCE (Weeks 5-10):")
print(f"{'=' * 80}")
print("Week 5  (Jan 17): XL 4 hits → GUARANTEE ✓ → €43 won | net -€5")
print("Week 6  (Jan 24): 0 hits → €0 won | net -€36")
print("Week 7  (Jan 31): XL 2 hits → €2 won | net -€34")
print("Week 8  (Feb  7): XL 2 hits → €3 won | net -€33")
print("Week 9  (Feb 14): L 1, XL 2 hits → €3 won | net -€33")
print(f"Week 10 (Feb 21): L {len(lotto_hits_from_wheel)}, XL {len(xl_hits_from_wheel)} hits → €{total_cash} won | net €{total_cash - 36}")
print("─" * 80)
prev_won = 43 + 0 + 2 + 3 + 3
prev_cost = 48 + 36 + 36 + 36 + 36
total_won = prev_won + total_cash
total_cost = prev_cost + 36
print(f"TOTAL: €{total_won} won | €{total_cost} cost | Net: €{total_won - total_cost}")
print(f"\nGuarantee activations: 1 in 6 weeks (expected ~1 per 14 weeks)")
print("Keep playing the same 12 wheel numbers!")
print("=" * 80)
