#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST-MORTEM ANALYSIS: January 17, 2026
Wheel System - Week 5
"""

import json
from datetime import datetime

# Actual results
lotto_result = [1, 2, 11, 29, 36, 41]
lotto_reserve = 16
xl_result = [5, 22, 23, 25, 35, 43]
xl_reserve = 31

# Load predictions
with open('predictions_history.json', 'r') as f:
    data = json.load(f)

# Get Week 5 predictions
week_5 = [w for w in data['weeks'] if w['draw_date'] == '2026-01-17'][0]
wheel_numbers = week_5['wheel_numbers']
tickets = week_5['tickets']

print("=" * 80)
print("POST-MORTEM: JANUARY 17, 2026 - WHEEL SYSTEM (WEEK 5)")
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
print(f"Lotto draw:  {len(lotto_hits_from_wheel)}/12 wheel numbers hit → {sorted(list(lotto_hits_from_wheel))}")
print(f"XL draw:     {len(xl_hits_from_wheel)}/12 wheel numbers hit → {sorted(list(xl_hits_from_wheel))}")

if len(lotto_hits_from_wheel) >= 4:
    print("\n🎉 LOTTO: GUARANTEE ACTIVATED! (4+ wheel numbers hit)")
else:
    print(f"\n   Lotto: Guarantee NOT activated (need 4+, got {len(lotto_hits_from_wheel)})")

if len(xl_hits_from_wheel) >= 4:
    print("🎉 XL: GUARANTEE ACTIVATED! (4+ wheel numbers hit)")
else:
    print(f"   XL: Guarantee NOT activated (need 4+, got {len(xl_hits_from_wheel)})")

# Analyze each ticket
print(f"\n{'─' * 80}")
print("TICKET ANALYSIS:")
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
        'prize': lotto_prize
    })
    
    xl_results.append({
        'ticket': i,
        'numbers': ticket['numbers'],
        'reserve': reserve_num,
        'matches': xl_matches,
        'matched_nums': xl_matched_nums,
        'prize': xl_prize,
        'cash': xl_cash
    })

# Display Lotto results
print("\nLOTTO DRAW:")
best_lotto = max(lotto_results, key=lambda x: x['matches'])
for r in lotto_results:
    status = "✓" if r['prize'] != "None" else "✗"
    print(f"  {r['ticket']:2d}. {r['numbers']} (R:{r['reserve']:2d}) → {r['matches']} hits {r['matched_nums']} {status} {r['prize']}")

# Display XL results
print("\nLOTTO XL DRAW:")
best_xl = max(xl_results, key=lambda x: x['matches'])
for r in xl_results:
    status = "✓" if r['prize'] != "None" else "✗"
    print(f"  {r['ticket']:2d}. {r['numbers']} (R:{r['reserve']:2d}) → {r['matches']} hits {r['matched_nums']} {status} {r['prize']}")

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
print(f"Cost of 16 tickets: €{16 * 3}  (€2 base + €1 XL per ticket)")
print(f"Net result: €{total_cash - 48} {'PROFIT' if total_cash > 48 else 'LOSS'}")

print(f"\n{'=' * 80}")
print("WHEEL SYSTEM VALIDATION:")
print(f"{'=' * 80}")

if len(xl_hits_from_wheel) >= 4:
    # Verify the guarantee
    has_3plus = any(r['matches'] >= 3 for r in xl_results)
    print(f"✓ 4+ wheel numbers hit in XL draw ({len(xl_hits_from_wheel)}/12)")
    print(f"✓ Guarantee stated: At least one ticket with 3+ matches")
    if has_3plus:
        print(f"✓ GUARANTEE VERIFIED: {len([r for r in xl_results if r['matches'] >= 3])} tickets with 3+ matches")
        print(f"✓ Mathematical prediction: CORRECT")
    else:
        print(f"✗ GUARANTEE FAILED: No tickets with 3+ matches (this should be impossible!)")
else:
    print(f"○ Guarantee did not activate (need 4+, got {len(xl_hits_from_wheel)} in XL)")

if len(lotto_hits_from_wheel) >= 4:
    has_3plus_lotto = any(r['matches'] >= 3 for r in lotto_results)
    print(f"✓ 4+ wheel numbers hit in Lotto draw ({len(lotto_hits_from_wheel)}/12)")
    if has_3plus_lotto:
        print(f"✓ GUARANTEE VERIFIED: {len([r for r in lotto_results if r['matches'] >= 3])} tickets with 3+ matches")
    else:
        print(f"✗ GUARANTEE FAILED in Lotto")

print("=" * 80)

# Prepare data for JSON update
performance_data = {
    "lotto_actual": lotto_result,
    "lotto_reserve": lotto_reserve,
    "xl_actual": xl_result,
    "xl_reserve": xl_reserve,
    "recorded_at": datetime.now().isoformat(),
    "wheel_performance": {
        "lotto_hits_from_wheel": len(lotto_hits_from_wheel),
        "xl_hits_from_wheel": len(xl_hits_from_wheel),
        "lotto_guarantee_activated": len(lotto_hits_from_wheel) >= 4,
        "xl_guarantee_activated": len(xl_hits_from_wheel) >= 4
    },
    "lotto_results": lotto_results,
    "xl_results": xl_results,
    "summary": {
        "best_lotto_hits": best_lotto['matches'],
        "best_xl_hits": best_xl['matches'],
        "lotto_prizes": lotto_prizes,
        "xl_prizes": xl_prizes,
        "total_cash_won": total_cash,
        "cost": 48,
        "net": total_cash - 48
    }
}

# Update JSON
for week in data['weeks']:
    if week['draw_date'] == '2026-01-17':
        week['performance'] = performance_data
        break

with open('predictions_history.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\n✓ Results saved to predictions_history.json")
