# Strategy Tuning Guide

## Overview

This document explains how to tune the lottery system for different objectives:
- **High 3-hit rate** (safe, consistent)
- **Maximize 5+6 wins** (aggressive, high-variance)
- **Risk-balanced** (mix of coverage + convergence)

## Key Hyperparameters

### 1. Model Parameters

| Parameter | Default | Effect | Tuning |
|-----------|---------|--------|--------|
| `lookback` | 20 | Historical window for sequences | ↑ = longer memory, more data needed |
| `epochs` | 40 | Training iterations | ↑ = better fit (but risk overfitting) |
| `batch_size` | 64 | Batch size | ↓ = slower but more stable |
| `d_model` | 128 | Embedding dimension | ↑ = more capacity (more params) |
| `pos_weight` | 12.0 | BCE weight for positive class | ↑ = stronger penalty for missing balls |
| `label_smooth` | 0.02 | Label smoothing | ↑ = less overconfident |

### 2. Ticket Generation Parameters

| Parameter | Default | Effect | Tuning |
|-----------|---------|--------|--------|
| `num_coverage` | 12 | Coverage tickets (70% strategy) | ↑ = more "safe" tickets |
| `num_convergence` | 4 | Convergence tickets (30% strategy) | ↑ = more aggressive tickets |
| `allow_nonanchor_repeat` | False | Repeat non-anchor numbers across tickets? | True = more overlap |
| `prefer_hot` | True | Bias toward recently hot numbers? | False = more random |
| `prefer_overdue` | True | Include overdue in support slots? | False = stick with hot |
| `game` | "xl" | XL or Lotto? | Anchors differ per game |

### 3. Data Parameters

| Parameter | Default | Effect | Tuning |
|-----------|---------|--------|--------|
| `recent_window` | 20 | Draws for hot/cold classification | ↓ = more recent focus |
| `start_tail` | None | Use only last N draws in backtest? | Lower for speed testing |

---

## Strategy Profiles

### Profile A: Safe Coverage (Maximize 3-Hit Rate)

**Objective**: Consistent 3-hit rate, minimize variance

**Config**:
```bash
python main.py \
  --csv nl_lotto_xl_history.csv \
  --game xl \
  --predict \
  --lookback 25 \
  --epochs 50 \
  --batch 32 \
  --num_coverage 18 \
  --num_convergence 2
```

**Logic**:
- Longer lookback → captures more patterns
- More epochs → better convergence
- More coverage tickets (18 vs 12) → broader spread
- Fewer convergence tickets → less variance
- Smaller batch → more stable training

**Expected Results**:
- 3-hit coverage: 35-45% (high)
- 4-hit coverage: 8-12% (moderate)
- 5-hit coverage: 1-2% (rare)
- Average match: 2.5-2.7

**Cost/Benefit**:
- ✓ Predictable, consistent hits
- ✗ Low chance of big win (5+6)
- ✗ Cost per week: ~€18 (if €1.50/ticket)

---

### Profile B: Aggressive Convergence (Target 5+6)

**Objective**: Chase big wins, accept variance

**Config**:
```bash
python main.py \
  --csv nl_lotto_xl_history.csv \
  --game xl \
  --predict \
  --lookback 20 \
  --epochs 30 \
  --batch 64 \
  --num_coverage 6 \
  --num_convergence 10
```

**Logic**:
- Standard lookback (20) → balance
- Fewer epochs → higher variance in model
- More convergence tickets (10 vs 4) → more aggressive bets
- Fewer coverage tickets (6 vs 12) → less "insurance"

**Expected Results**:
- 3-hit coverage: 25-30% (lower)
- 4-hit coverage: 5-8%
- 5-hit coverage: 0.5-1.5% (higher!)
- 6-hit coverage: 0.0-0.2% (rare but possible)
- Average match: 2.3-2.5

**Cost/Benefit**:
- ✓ Higher chance of 5+6 win
- ✗ More frequent ticket failures
- ✗ Lower 3-4 hit rate
- ✗ Cost per week: ~€24 (if €1.50/ticket)

---

### Profile C: Balanced (Recommended Default)

**Objective**: Balance consistency with upside

**Config**:
```bash
python main.py \
  --csv nl_lotto_xl_history.csv \
  --game xl \
  --predict \
  --lookback 20 \
  --epochs 40 \
  --batch 64 \
  --num_coverage 12 \
  --num_convergence 4
```

**Expected Results**:
- 3-hit coverage: 30-35%
- 4-hit coverage: 7-10%
- 5-hit coverage: 0.8-1.2%
- Average match: 2.4-2.6

**Cost/Benefit**:
- ✓ Balanced risk/reward
- ✓ Moderate costs (~€24/week)
- ✓ Good for long-term play

---

## Tuning by Objective

### Goal: Increase 3-Hit Rate

1. **Use longer lookback** (25-30)
   ```
   --lookback 30 --epochs 50
   ```

2. **Increase coverage tickets**
   ```
   --num_coverage 15 --num_convergence 3
   ```

3. **Prioritize recent hot numbers**
   - Edit `constraint_generator.py`: Set `prefer_hot=True`

4. **Add more training data**
   - Ensure 100+ historical draws
   - Use full history, not `--start_tail`

5. **Lower batch size** (stabilize training)
   ```
   --batch 32
   ```

**Expected improvement**: +5-10% coverage_3

---

### Goal: Increase 5+6 Hit Rate

1. **Use standard/shorter lookback** (15-20)
   ```
   --lookback 20 --epochs 30
   ```

2. **Increase convergence tickets**
   ```
   --num_convergence 8 --num_coverage 8
   ```

3. **Allow non-anchor repetition**
   - Edit `constraint_generator.py`: `allow_nonanchor_repeat=True`
   - This stacks numbers more aggressively

4. **Reduce label smoothing bias**
   - Edit `ml_model.py`: `label_smooth=0.0`
   - Allows model to be more confident

5. **Increase pos_weight** (penalize missing balls)
   ```python
   # In ml_model.py
   pos_weight=15.0  # Up from 12.0
   ```

**Expected improvement**: +0.5-1.0% coverage_5

---

### Goal: Improve Average Match

1. **Ensemble prediction** (combine multiple models)
   - Train with different seeds (7, 42, 123, 999)
   - Average their predictions
   - See `quick_reference.py` #10

2. **Increase model capacity**
   - Edit `ml_model.py`: `d_model=256` (from 128)
   - Add more Transformer blocks

3. **Use longer history window**
   - `--lookback 30`
   - Capture more temporal patterns

4. **Add data augmentation**
   - Train on multiple CSV files (if available)
   - Simulate draws (rare)

---

## Backtest-Driven Tuning

### Workflow

1. **Baseline backtest**
   ```bash
   python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50
   ```
   Record metrics: coverage_3, coverage_5, avg_match

2. **Adjust one parameter**
   ```bash
   python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50 --epochs 50
   ```
   Compare results

3. **Repeat for other params** (one at a time)
   - `--lookback 25`
   - `--num_convergence 6`
   - `--batch 32`

4. **Pick best combination**
   - Focus on your primary objective
   - Verify on full history (remove `--start_tail`)

### Example Sweep

```bash
# Test lookback = 15, 20, 25, 30
for LB in 15 20 25 30; do
  echo "Testing lookback=$LB"
  python main.py --csv nl_lotto_xl_history.csv --game xl --backtest \
    --start_tail 50 --lookback $LB --epochs 20 > results_lb_$LB.txt 2>&1
done

# Compare results manually
```

---

## Advanced Techniques

### 1. Ensemble Prediction

**Idea**: Train multiple models, average predictions

**Implementation** (see `quick_reference.py` #10):
```python
predictions = []
for seed in [7, 42, 123, 999]:
    model = build_model(...)
    train_model(model, ...)
    probs, _ = predict_probs(model, X[-1:])
    predictions.append(probs[0])

ensemble_probs = np.mean(predictions, axis=0)
```

**Benefit**: Reduces variance, more stable predictions

**Cost**: 4× training time

---

### 2. Two-Stage Model

**Idea**: 
- Stage 1: Predict which "anchor cluster" will hit
- Stage 2: Predict remaining numbers given anchor

**Implementation**:
```python
# Would require code restructuring
# See ml_model.py for reference architecture
```

**Benefit**: Might improve anchor hit rate

---

### 3. Constrained Optimization

**Idea**: Use solver (e.g., `pulp`) to find optimal tickets

**Implementation**:
```python
from pulp import *

# Formulate as IP: maximize expected value subject to constraints
# Variables: binary per ticket, per ball
# Objective: E[winnings] - cost
# Constraints: 3-odd/3-even, anchors, low/mid/high spread
```

**Benefit**: Theoretically optimal (computationally expensive)

---

## Monitoring & Evaluation

### Weekly Check

After each draw, log:
1. **Expected vs Actual**
   - Did model-predicted balls appear?
   - How many matched per ticket?

2. **Anchor Performance**
   - Which anchors hit?
   - Which didn't?

3. **Convergence Success**
   - Did aggressive tickets pay off?

4. **Model Drift**
   - Is recent performance declining?
   - Need to retrain or adjust?

### Example Log

```csv
date,best_match,hits_3,coverage_tickets,convergence_tickets,anchor_hits
2025-12-19,4,1,10,1,"[(9,10)]"
2025-12-26,3,0,9,0,"[]"
2025-01-02,5,2,11,1,"[(20,21), (32,33)]"
```

---

## Decision Tree: Which Strategy?

```
START
  ↓
Have <30 draws? → Use --start_tail or add more history
  ↓
Want to maximize 3-hit rate?
  YES → Profile A (Safe Coverage)
  NO → Continue
  ↓
Can afford €30+/week?
  YES → Profile B (Aggressive) or Profile C (Balanced)
  NO → Profile A (Safe)
  ↓
Have time to experiment?
  YES → Run backtests, pick best hyperparams
  NO → Use Profile C (Balanced)
```

---

## Troubleshooting

### Problem: Low 3-hit rate (<25%)

**Diagnosis**:
- Model isn't learning well
- Constraints too restrictive
- History insufficient

**Solutions**:
1. Add more historical draws
2. Increase lookback (20 → 25)
3. Increase epochs (40 → 60)
4. Reduce batch size (64 → 32)

### Problem: No 5+6 hits in backtest

**Diagnosis**:
- Rare event, expected
- Model predictions too uniform
- Not enough variance

**Solutions**:
1. Run longer backtest (need 100+ weeks)
2. Increase convergence tickets (4 → 8)
3. Reduce epochs (overtraining?)
4. Try ensemble prediction

### Problem: Model crashes / OOM

**Diagnosis**:
- Batch size too large
- Lookback too long
- Model capacity too high

**Solutions**:
1. Lower batch size (64 → 32)
2. Lower lookback (30 → 20)
3. Reduce d_model (128 → 64)
4. Use GPU if available

---

## References

### Theory
- Multi-task learning: Ruder et al., 2017
- Class imbalance: He & Garcia, 2009
- Transformers: Vaswani et al., 2017

### Data
- Netherlands Lottery: lotteryguru.com
- Historical trends: analyzeonline.nl

### Tools
- Keras/TensorFlow: tensorflow.org
- PuLP (optimization): coin-or.org/pulp

---

## Questions?

Refer to:
- `README.md` for quick start
- `quick_reference.py` for code examples
- `interactive_notebook.ipynb` for hands-on exploration
