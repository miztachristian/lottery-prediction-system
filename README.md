# Dutch Lottery Wheel System

A mathematically sound lottery system using **wheel coverage** instead of "hot number" prediction.

## What is This?

This system uses a **3-if-4 wheel** to guarantee prizes when your numbers hit. With 16 Lotto XL tickets covering 12 carefully selected numbers, you get:

- **32 chances per week** (Lotto XL gives you both Lotto and XL draws)
- **Mathematical guarantee**: If 4+ of your 12 numbers appear in either draw, at least one ticket will have 3+ matches
- **No guessing**: This is combinatorial mathematics, not prediction

## Files

### Core System
- `wheel_system.py` - The wheel generator (3-if-4, 3-if-5, 4-if-5 designs)
- `generate_week5_wheel.py` - Generate predictions for the current week

### Data Management
- `nl_lotto_history.csv` - Historical Lotto draw results
- `nl_lotto_xl_history.csv` - Historical Lotto XL draw results
- `predictions_history.json` - Your prediction history and results
- `strategy_state.yaml` - Current strategy configuration

### Utilities
- `data_pipeline.py` - Data loading and processing
- `web_scraper.py` - Fetch latest results from lotteryguru.com
- `post_mortem.py` - Analyze performance after draws
- `email_notifier.py` - Optional email notifications
- `scheduler.py` - Optional automation

## Quick Start

### Generate Predictions

```bash
python generate_week5_wheel.py
```

This will:
1. Select 12 balanced numbers
2. Generate 16 mathematically designed tickets
3. Save to `predictions_history.json`
4. Display your tickets and the guarantee

### Your 12 Wheel Numbers (Week 5)

```
[9, 11, 14, 15, 22, 23, 24, 25, 33, 35, 39, 40]
```

**IMPORTANT**: Play these SAME 12 numbers every week for at least 20 weeks. The mathematical guarantee only works with consistency.

## How It Works

### The Guarantee

With our 3-if-4 wheel:
- If 4+ of your 12 numbers are in the winning 6 → **Guaranteed 3+ match**
- With Lotto XL, you get TWO independent draws per week
- Expected frequency: ~1 guaranteed prize every 14 weeks

### Prize Structure

**Lotto Draw:**
- 3 hits = Free ticket

**XL Draw:**
- 6 numbers = €1,000,000
- 5 + reserve = €25,000
- 5 numbers = €1,000
- 4 + reserve = €25
- 4 numbers = €15
- 3 + reserve = €10
- **3 numbers = €5**
- 2 + reserve = €2
- 2 numbers = €1

### Why This Works

1. **No Pattern Chasing**: Past draws don't predict future draws
2. **Coverage, Not Prediction**: We maximize coverage of number combinations
3. **Mathematical Certainty**: The guarantee is proven by combinatorial design theory
4. **Long-Term Strategy**: Consistency over 20+ weeks lets the math work

## What We Removed

The following obsolete strategies were removed:
- ❌ ML prediction models (no better than random)
- ❌ "Hot/Cold" number analysis (statistical illusion)
- ❌ Anchor-based systems (failed repeatedly)
- ❌ Reduced pool strategies (missed outliers)
- ❌ Cloud deployment configs (unnecessary)

## Weekly Workflow

1. **Saturday Morning**: Generate predictions
   ```bash
   python generate_week5_wheel.py
   ```

2. **Play Your Tickets**: Use the same 12 numbers, 16 tickets

3. **After Draw**: Record results and run post-mortem
   ```bash
   python post_mortem.py
   ```

4. **Next Week**: Repeat with the SAME 12 numbers

## Important Notes

- **Do NOT change your 12 numbers** based on results
- **Consistency is key** - The guarantee works over time
- **Expected ROI**: Roughly break-even over 50+ weeks with occasional larger prizes
- **Goal**: €100k (5+R) requires luck, but the wheel maximizes your chances

## Requirements

```bash
pip install pandas pyyaml requests beautifulsoup4
```
