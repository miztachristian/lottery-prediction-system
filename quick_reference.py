#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Reference: Common Tasks & Recipes

Copy-paste ready code snippets for common operations.
"""

# ============================================================================
# 1. QUICK PREDICT (Generate Tickets)
# ============================================================================

from main import LottoSystem

system = LottoSystem("nl_lotto_xl_history.csv", game="xl")
system.train(epochs=30)
tickets, main_probs, reserve_probs = system.predict(
    num_coverage=16, 
    num_convergence=8
)

# Expected output:
#   12 coverage tickets (broad statistical coverage)
#   4 convergence tickets (aggressive, high-variance)


# ============================================================================
# 2. BACKTEST LAST N DRAWS (FAST)
# ============================================================================

system = LottoSystem("nl_lotto_xl_history.csv", game="xl")
engine = system.backtest(
    lookback=20,
    epochs=15,  # Lower for speed
    batch_size=64,
    start_tail=50,  # Only last 50 draws
    num_coverage=16,
    num_convergence=8
)

# Expected output:
#   Backtest summary with 3/4/5/6-hit statistics
#   Coverage rates (% of draws with ≥X-hit)


# ============================================================================
# 3. ANALYZE HOT/COLD NUMBERS
# ============================================================================

from data_pipeline import LottoData

data = LottoData("nl_lotto_xl_history.csv")

# Frequency stats (all time)
freq = data.compute_frequency_stats()
top_freq = sorted(freq.items(), key=lambda x: -x[1])[:10]
print("Top 10 by all-time frequency:")
for ball, f in top_freq:
    print(f"  {ball}: {f:.4f}")

# Hot/cold classification (recent 20 draws)
hot, cold = data.compute_hot_cold(recent_window=20)
print(f"\nHot (recent): {sorted(hot)}")
print(f"Cold (overdue): {sorted(cold)}")

# Gap analysis
gaps = data.compute_gap_stats()
longest_gaps = sorted(gaps.items(), key=lambda x: -x[1])[:10]
print("\nTop 10 overdue (longest gaps):")
for ball, gap in longest_gaps:
    print(f"  {ball}: {gap} draws")


# ============================================================================
# 4. CUSTOM TICKET GENERATION (ADVANCED)
# ============================================================================

from data_pipeline import LottoData, build_sequence_dataset
from ml_model import build_model, train_model, predict_probs
from constraint_generator import TicketGenerator, TicketConfig
import numpy as np

# Load & train
data = LottoData("nl_lotto_xl_history.csv")
df = data.get_df()
X, y_main, y_res, _ = build_sequence_dataset(df, lookback=20)

model = build_model(lookback=20)
# ... train model ...

# Predict
main_probs, _ = predict_probs(model, X[-1:], verbose=0)
main_probs = main_probs[0]

# Custom config: aggressive hot-number bias
config = TicketConfig(
    game="xl",
    ticket_type="convergence",  # All convergence, no coverage
    allow_nonanchor_repeat=False,
    prefer_hot=True,
    random_seed=42
)

gen = TicketGenerator(config)
hot, cold = data.compute_hot_cold(recent_window=25)  # Longer window

# Generate more convergence tickets
tickets_dict = gen.generate(
    main_probs,
    num_coverage=0,  # No coverage
    num_convergence=24,  # All convergence (high-variance strategy)
    hot_numbers=hot,
    cold_numbers=cold
)

for i, ticket in enumerate(tickets_dict['convergence'], 1):
    print(f"{i}: {ticket}")


# ============================================================================
# 5. EVALUATE SPECIFIC TICKETS AGAINST HISTORY
# ============================================================================

from backtest_engine import BacktestEngine

engine = BacktestEngine(game="xl")

# Define some test tickets
test_tickets = [
    [3, 9, 10, 23, 41, 44],
    [9, 15, 20, 21, 40, 44],
]

# Evaluate against each historical draw
data = LottoData("nl_lotto_xl_history.csv")
df = data.get_df()

for _, draw_row in df.tail(10).iterrows():
    actual = {
        'date': str(draw_row.get('date')),
        'main': data.extract_main_numbers(draw_row),
        'reserve': data.extract_reserve(draw_row)
    }
    result = engine.evaluate_set(test_tickets, actual)
    
    print(f"{actual['date']}: Main={sorted(actual['main'])}, Reserve={actual['reserve']}")
    print(f"  → Best match: {result.best_match}, 3+: {result.hits_3}, 4+: {result.hits_4}")

metrics = engine.compute_metrics()
print(f"\nOverall 3-hit coverage: {metrics.coverage_3*100:.1f}%")


# ============================================================================
# 6. EXPORT TICKETS TO CSV
# ============================================================================

import pandas as pd
from datetime import datetime

system = LottoSystem("nl_lotto_xl_history.csv", game="xl")
system.train(epochs=20)
tickets_dict, probs, _ = system.predict()

# Create export
rows = []
for i, ticket in enumerate(tickets_dict['coverage'], 1):
    rows.append({
        'ticket_id': f"C{i:02d}",
        'type': 'coverage',
        'numbers': ','.join(map(str, ticket)),
        'generated': datetime.now().isoformat(),
    })

for i, ticket in enumerate(tickets_dict['convergence'], 1):
    rows.append({
        'ticket_id': f"V{i:02d}",
        'type': 'convergence',
        'numbers': ','.join(map(str, ticket)),
        'generated': datetime.now().isoformat(),
    })

df_export = pd.DataFrame(rows)
df_export.to_csv('tickets_generated.csv', index=False)
print("✓ Exported to tickets_generated.csv")


# ============================================================================
# 7. ANCHOR PERFORMANCE ANALYSIS
# ============================================================================

from data_pipeline import LottoData

data = LottoData("nl_lotto_xl_history.csv")

# XL anchors
ANCHORS_XL = [(9, 10), (20, 21), (32, 33), (21, 44)]

df = data.get_df()

anchor_hits = {str(a): 0 for a in ANCHORS_XL}
anchor_total = {str(a): 0 for a in ANCHORS_XL}

for _, row in df.iterrows():
    actual = data.extract_main_numbers(row)
    
    for anchor in ANCHORS_XL:
        anchor_str = str(anchor)
        anchor_total[anchor_str] += 1
        
        if set(anchor) & actual:
            anchor_hits[anchor_str] += 1

print("Anchor Hit Rates (all-time):")
for anchor in ANCHORS_XL:
    anchor_str = str(anchor)
    rate = anchor_hits[anchor_str] / anchor_total[anchor_str] * 100
    print(f"  {anchor}: {anchor_hits[anchor_str]}/{anchor_total[anchor_str]} = {rate:.1f}%")


# ============================================================================
# 8. PARAMETER SWEEP (FIND BEST CONFIG)
# ============================================================================

import numpy as np

# Test different lookbacks and epoch counts
configs = [
    {'lookback': 15, 'epochs': 20},
    {'lookback': 20, 'epochs': 30},
    {'lookback': 25, 'epochs': 40},
    {'lookback': 30, 'epochs': 50},
]

results = []

for config in configs:
    print(f"\nTesting lookback={config['lookback']}, epochs={config['epochs']}...")
    
    system = LottoSystem("nl_lotto_xl_history.csv", game="xl")
    try:
        system.train(
            lookback=config['lookback'],
            epochs=config['epochs'],
            batch_size=32,
            verbose=0
        )
        
        engine = system.backtest(
            lookback=config['lookback'],
            epochs=10,
            batch_size=32,
            start_tail=30
        )
        
        metrics = engine.metrics
        results.append({
            'lookback': config['lookback'],
            'epochs': config['epochs'],
            'coverage_3': metrics.coverage_3,
            'coverage_5': metrics.coverage_5,
            'avg_match': metrics.avg_match,
        })
        
    except Exception as e:
        print(f"  ERROR: {e}")

# Find best config
df_results = pd.DataFrame(results)
best_idx = df_results['coverage_5'].idxmax()
best_config = df_results.iloc[best_idx]
print(f"\n✓ Best config:")
print(best_config)


# ============================================================================
# 9. WEEKLY AUTOMATION SCRIPT
# ============================================================================

"""
Run this every Friday evening (e.g., via cron or Task Scheduler).

Before running: append latest draw to nl_lotto_xl_history.csv

Example cron job:
  0 21 * * 5 /usr/bin/python3 /path/to/weekly_predict.py
"""

import subprocess
from datetime import datetime
import os

CSV_PATH = "nl_lotto_xl_history.csv"
LOG_PATH = "prediction_log.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    with open(LOG_PATH, 'a') as f:
        f.write(entry + '\n')

try:
    log("Starting weekly prediction...")
    
    # Generate tickets
    result = subprocess.run(
        ["python", "main.py", "--csv", CSV_PATH, "--game", "xl", 
         "--predict", "--epochs", "30", "--num_coverage", "12", "--num_convergence", "4"],
        capture_output=True,
        text=True,
        timeout=3600
    )
    
    if result.returncode == 0:
        log("✓ Prediction complete")
        log("Output:\\n" + result.stdout[-500:])  # Last 500 chars
    else:
        log(f"✗ Prediction failed: {result.stderr}")
        
except Exception as e:
    log(f"✗ Exception: {e}")


# ============================================================================
# 10. COMPARE PREDICTIONS ACROSS MODELS
# ============================================================================

from data_pipeline import LottoData, build_sequence_dataset
from ml_model import build_model, train_model, predict_probs
import numpy as np

data = LottoData("nl_lotto_xl_history.csv")
df = data.get_df()
X, y_main, y_res, _ = build_sequence_dataset(df, lookback=20)

# Train multiple models with different random seeds
predictions = []
for seed in [7, 42, 123, 999]:
    np.random.seed(seed)
    
    model = build_model(lookback=20)
    train_model(model, X[:100], y_main[:100], y_res[:100],
                X[100:], y_main[100:], y_res[100:],
                epochs=15, batch_size=32, verbose=0)
    
    probs, _ = predict_probs(model, X[-1:])
    predictions.append(probs[0])

# Ensemble: average predictions
ensemble_probs = np.mean(predictions, axis=0)
ensemble_std = np.std(predictions, axis=0)

top_idx = np.argsort(-ensemble_probs)[:15] + 1
print("Ensemble prediction (average of 4 models):")
for ball in top_idx:
    print(f"  {ball}: {ensemble_probs[ball-1]:.4f} ± {ensemble_std[ball-1]:.4f}")
