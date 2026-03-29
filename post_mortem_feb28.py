#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST-MORTEM ANALYSIS: February 28, 2026 (SUPER SATURDAY)
Wheel System - Week 11 (12 tickets played)
"""

# Actual results
# Draw 1 (Trekking)
lotto1_result = [3, 4, 11, 29, 34, 40]
lotto1_reserve = 2
xl1_result = [20, 30, 37, 38, 40, 44]
xl1_reserve = 10

# Draw 2 (Super Saturday)
lotto2_result = [4, 8, 9, 10, 16, 30]
lotto2_reserve = 37
xl2_result = [4, 5, 29, 33, 39, 41]
xl2_reserve = 34

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
print("POST-MORTEM: FEBRUARY 28, 2026 - SUPER SATURDAY (WEEK 11)")
print("=" * 80)

print(f"\n{'─' * 80}")
print("ACTUAL RESULTS:")
print(f"{'─' * 80}")
print(f"Lotto 1:      {sorted(lotto1_result)} | Reserve: {lotto1_reserve}")
print(f"Lotto XL 1:   {sorted(xl1_result)} | Reserve: {xl1_reserve}")
print(f"Lotto 2:      {sorted(lotto2_result)} | Reserve: {lotto2_reserve}")
print(f"Lotto XL 2:   {sorted(xl2_result)} | Reserve: {xl2_reserve}")

print(f"\n{'─' * 80}")
print("YOUR WHEEL NUMBERS:")
print(f"{'─' * 80}")
print(f"{wheel_numbers}")

# Check how many wheel numbers hit
l1_hits = set(wheel_numbers).intersection(set(lotto1_result))
xl1_hits = set(wheel_numbers).intersection(set(xl1_result))
l2_hits = set(wheel_numbers).intersection(set(lotto2_result))
xl2_hits = set(wheel_numbers).intersection(set(xl2_result))

print(f"\n{'─' * 80}")
print("WHEEL PERFORMANCE:")
print(f"{'─' * 80}")
print(f"Lotto 1 draw:  {len(l1_hits)}/12 wheel numbers hit → {sorted(list(l1_hits)) if l1_hits else 'NONE'}")
print(f"XL 1 draw:     {len(xl1_hits)}/12 wheel numbers hit → {sorted(list(xl1_hits)) if xl1_hits else 'NONE'}")
print(f"Lotto 2 draw:  {len(l2_hits)}/12 wheel numbers hit → {sorted(list(l2_hits)) if l2_hits else 'NONE'}")
print(f"XL 2 draw:     {len(xl2_hits)}/12 wheel numbers hit → {sorted(list(xl2_hits)) if xl2_hits else 'NONE'}")

def get_lotto_prize(matches, reserve_hit):
    if matches == 6: return "JACKPOT" if reserve_hit else "2nd Prize"
    elif matches == 5: return "€100,000 (5+R)" if reserve_hit else "€1,000 (5)"
    elif matches == 4: return "€50 (4)"
    elif matches == 3: return "FREE TICKET (3)"
    elif matches == 2 and reserve_hit: return "FREE TICKET (2+R)"
    return "None"

def get_xl_prize(matches, reserve_hit):
    cash = 0
    prize = "None"
    if matches == 6: prize = "€1,000,000 (6)"; cash = 1000000
    elif matches == 5 and reserve_hit: prize = "€25,000 (5+R)"; cash = 25000
    elif matches == 5: prize = "€1,000 (5)"; cash = 1000
    elif matches == 4 and reserve_hit: prize = "€25 (4+R)"; cash = 25
    elif matches == 4: prize = "€15 (4)"; cash = 15
    elif matches == 3 and reserve_hit: prize = "€10 (3+R)"; cash = 10
    elif matches == 3: prize = "€5 (3)"; cash = 5
    elif matches == 2 and reserve_hit: prize = "€2 (2+R)"; cash = 2
    elif matches == 2: prize = "€1 (2)"; cash = 1
    return prize, cash

# Analyze each ticket
all_prizes = []
total_cash = 0
free_tickets = 0

print(f"\n{'─' * 80}")
print("TICKET ANALYSIS (12 tickets played across 4 draws):")
print(f"{'─' * 80}")

for i, ticket in enumerate(tickets, 1):
    t_nums = set(ticket['numbers'])
    r_num = ticket['reserve']
    
    # Draw 1
    l1_m = len(t_nums.intersection(set(lotto1_result)))
    l1_r = r_num == lotto1_reserve
    l1_pz = get_lotto_prize(l1_m, l1_r)
    
    xl1_m = len(t_nums.intersection(set(xl1_result)))
    xl1_r = r_num == xl1_reserve
    xl1_pz, xl1_c = get_xl_prize(xl1_m, xl1_r)
    
    # Draw 2
    l2_m = len(t_nums.intersection(set(lotto2_result)))
    l2_r = r_num == lotto2_reserve
    l2_pz = get_lotto_prize(l2_m, l2_r)
    
    xl2_m = len(t_nums.intersection(set(xl2_result)))
    xl2_r = r_num == xl2_reserve
    xl2_pz, xl2_c = get_xl_prize(xl2_m, xl2_r)
    
    ticket_cash = xl1_c + xl2_c
    ticket_free = sum(1 for p in [l1_pz, l2_pz] if "FREE TICKET" in p)
    
    if ticket_cash > 0 or ticket_free > 0:
        print(f"Ticket {i:2d} {ticket['numbers']} (R:{r_num:2d}) WINS:")
        if l1_pz != "None": print(f"  - Lotto 1: {l1_pz}")
        if xl1_pz != "None": print(f"  - XL 1:    {xl1_pz}")
        if l2_pz != "None": print(f"  - Lotto 2: {l2_pz}")
        if xl2_pz != "None": print(f"  - XL 2:    {xl2_pz}")
        all_prizes.append(f"T{i}")
        total_cash += ticket_cash
        free_tickets += ticket_free

if not all_prizes:
    print("No winning tickets this week.")

print(f"\n{'=' * 80}")
print("SUMMARY:")
print(f"{'=' * 80}")
print(f"Total cash won: €{total_cash}")
print(f"Free tickets won: {free_tickets}")
print(f"Cost of 12 tickets: €36")
net_cash = total_cash - 36
print(f"Net result: €{net_cash} {'PROFIT' if net_cash > 0 else 'LOSS'} (plus {free_tickets} free tickets)")

print(f"\n{'=' * 80}")
print("CUMULATIVE PERFORMANCE (Weeks 5-11):")
print(f"{'=' * 80}")
print("Week 5  (Jan 17): \t€43 won | \tnet -€5")
print("Week 6  (Jan 24): \t€0 won  | \tnet -€36")
print("Week 7  (Jan 31): \t€2 won  | \tnet -€34")
print("Week 8  (Feb  7): \t€3 won  | \tnet -€33")
print("Week 9  (Feb 14): \t€3 won  | \tnet -€33")
print("Week 10 (Feb 21): \t€0 won  | \tnet -€36")
print(f"Week 11 (Feb 28): \t€{total_cash} won  | \tnet €{net_cash}")
print("─" * 80)
prev_won = 43 + 0 + 2 + 3 + 3 + 0
prev_cost = 48 + 36 + 36 + 36 + 36 + 36
total_won = prev_won + total_cash
total_cost = prev_cost + 36
print(f"TOTAL: €{total_won} won | €{total_cost} cost | Net: €{total_won - total_cost} (plus {free_tickets} free tickets)")
print(f"\nGuarantee activations: 1 in 7 weeks (expected ~1 per 14 weeks)")
print("=" * 80)
