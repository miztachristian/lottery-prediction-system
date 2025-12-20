# Netherlands Lottery Prediction System

A production-ready ML-based lottery prediction system for Netherlands Lotto and Lotto XL, built on the anchor-cluster framework with constraint-aware ticket generation and rolling backtesting.

## 🎯 Core Principles

1. **Anchor-Cluster Framework**: Every ticket includes strategically chosen anchor numbers/pairs
   - **XL**: (9-10), (20-21), (32-33), (21-44)
   - **Lotto**: 21, 23, 40, 41, 44

2. **Constraint Enforcement**: Every ticket must satisfy
   - 3 odd / 3 even numbers
   - Low (1-15) / Mid (16-30) / High (31-45) spread
   - Anchor inclusion

3. **Two-Tier Strategy**
   - **Coverage Tickets (70%)**: Broad statistical coverage, consistent 3-4 hit potential
   - **Convergence Tickets (30%)**: Aggressive cluster stacking, designed for €10k+ outcomes

4. **Dynamic Hot/Cold Stats**: 
   - Hot numbers: frequent in recent draws (bias toward in tickets)
   - Cold/Overdue: long gaps since last appearance (included in support slots)

## 📦 Architecture

### Modules

| Module | Purpose |
|--------|---------|
| `data_pipeline.py` | Load CSV, compute frequency/gap stats, hot/cold classification |
| `ml_model.py` | Transformer-based encoder; predicts probabilities for main + reserve |
| `constraint_generator.py` | Enforce anchor, parity, spread constraints; coverage/convergence split |
| `backtest_engine.py` | Evaluate ticket performance against historical draws |
| `main.py` | Orchestrator: trains, predicts, backtests |

### Data Flow

```
CSV → LottoData (clean + stats)
  ↓
build_sequence_dataset (one-hot windows)
  ↓
build_model (Transformer) → train
  ↓
predict_probs (main + reserve probabilities)
  ↓
TicketGenerator (apply constraints)
  ↓
Tickets {coverage, convergence}
  ↓
BacktestEngine (evaluate vs actual draws)
```

## 🚀 Quick Start

### 1. Update Data (Recommended)

Fetch latest historical draws from the web to improve model accuracy:

```bash
# Lotto XL
python main.py --csv nl_lotto_xl_history.csv --game xl --update-data --scrape-pages 10

# Lotto  
python main.py --csv nl_lotto_history.csv --game lotto --update-data --scrape-pages 10
```

### 2. Generate Predictions

```bash
python main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 20
```

### 3. Run Backtest

```bash
python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50
```
- Top-15 balls by model probability

### Backtest (Evaluate Strategy)

```bash
python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 50
```

**Output**:
- Hit statistics (3/4/5/6-match coverage)
- Average matches per ticket
- Anchor performance analysis

### Options

```
--csv PATH              History CSV (required)
--game {xl,lotto}       Game type (default: xl)
--predict               Generate tickets [default mode]
--backtest              Run rolling backtest
--epochs N              Training epochs (default: 40)
--batch N               Batch size (default: 64)
--lookback N            History window K (default: 20)
--num_coverage N        Coverage tickets (default: 12)
--num_convergence N     Convergence tickets (default: 4)
--start_tail N          Use only last N draws for backtest speed
--seed N                Random seed (default: 7)
```

## 📊 Backtest Metrics

After backtesting, you'll see:

```
BACKTEST SUMMARY
Total Draws Evaluated: 50
Total Tickets Played: 800

Hit Statistics:
  3-hits: 156 (31.2% of draws)
  4-hits: 52 (10.4% of draws)
  5-hits: 8 (1.6% of draws)
  5+reserve: 2 (0.4% of draws)
  6-hits: 0 (0.0% of draws)

Average Match: 2.47 per ticket
```

**Interpretation**:
- **Coverage %**: Probability of getting at least X-hit in a week
- **Average Match**: Baseline expectation (>2.5 is good signal)
- **5+6 hit rate**: Focus for high-tier improvements

## 🧠 Understanding the Model

### Architecture

- **Input**: Sequence of 20 historical draws (one-hot encoded, 45-dim each)
- **Encoder**: Conv1D layers → positional encoding → 2× Transformer blocks
- **Outputs**:
  - **Main**: 45-dim sigmoid (multi-label) → probability for each ball
  - **Reserve**: 45-dim softmax (categorical) → single reserve prediction

### Loss Function

- **Main**: Weighted Binary Cross-Entropy (pos_weight=12, accounts for imbalance)
- **Reserve**: Categorical Cross-Entropy
- **Aux**: Sum-6 regularizer (encourage predicted probabilities to sum ≈ 6)
- **Label Smoothing**: Prevents overconfidence

### Why Transformer?

- Captures temporal patterns in draw history
- Attention mechanism weights recent draws more heavily
- Better than simple RNN for sparse, high-dimensional input

## 🔥 Strategy Tuning

### To Increase 3-Hit Coverage

```python
system = LottoSystem(csv_path, game="xl")
system.train(lookback=25, epochs=50)  # Longer history, more training
tickets, _, _ = system.predict(num_coverage=20)  # More coverage tickets
```

### To Target 5+6 Wins

```python
# Increase convergence tickets (more aggressive cluster stacking)
tickets, _, _ = system.predict(num_coverage=12, num_convergence=12)
```

### To Adjust Anchor Bias

Edit `constraint_generator.py`:
```python
# Increase weight toward hot numbers in tickets
config = TicketConfig(prefer_hot=True, allow_nonanchor_repeat=False)
```

## 📈 Weekly Automation (Ideal Workflow)

**Friday 21:00**
```bash
python main.py --csv nl_lotto_xl_history.csv --game xl --predict --epochs 30
# Buy the generated tickets
```

**Saturday Morning** (after draw)
```bash
# Append new draw to CSV, rerun to update stats
python main.py --csv nl_lotto_xl_history.csv --game xl --predict
```

**Sunday Afternoon**
```bash
# Backtest to evaluate what worked
python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 20
# Adjust strategy based on metrics
```

## 🛠️ Advanced Usage

### Custom Backtesting

```python
from data_pipeline import LottoData
from ml_model import build_model, train_model, predict_probs
from constraint_generator import TicketGenerator
from backtest_engine import BacktestEngine

# Load data
data = LottoData("nl_lotto_xl_history.csv")
df = data.get_df()

# Train & predict
X, y_main, y_res, _ = build_sequence_dataset(df, lookback=20)
model = build_model(lookback=20)
# ... training ...

# Generate tickets with custom constraints
gen = TicketGenerator()
tickets = gen.generate(probs, num_coverage=24, num_convergence=0)

# Evaluate
engine = BacktestEngine()
for ticket, actual_draw in zip(tickets, draws):
    engine.evaluate_set(ticket, actual_draw)

metrics = engine.compute_metrics()
print(f"5-hit rate: {metrics.coverage_5:.1%}")
```

### Analyzing Anchor Performance

```python
# After backtest
results_df = engine.get_results_df()
results_df['date'] = pd.to_datetime(results_df['date'])
results_df.to_csv('backtest_results.csv', index=False)

# Analyze which anchors performed best
anchor_hits = {}  # Populate from results_df
```

## ⚠️ Key Insights

1. **Pure randomness cannot be beaten** — but structure can optimize within noise
2. **Over-coverage without intent** leads to endless 2-3 hits, never breaking into big wins
3. **High-tier wins require**:
   - Anchor correctness (if anchor appears, 3+ hit very likely)
   - Cluster convergence (multiple correlated numbers on same ticket)
   - Willingness to sacrifice "safe" tickets for variance
4. **The biggest mistake**: too much spread, not enough intent
5. **Expected Value**: Even with 30% 3-hit rate, ROI is negative (cost €1, avg return €0.60) — this is a stochastic game, not a money-maker

## 📝 Data Format

CSVs must have columns:
- `date`: Draw date (ISO format)
- `n1`, `n2`, `n3`, `n4`, `n5`, `n6`: Main numbers (1-45)
- `reserve`: Reserve number (1-45)
- Optional: `game`, `source`

Example:
```csv
date,n1,n2,n3,n4,n5,n6,reserve,game,source
2025-07-12,3,7,9,15,31,41,38,Lotto XL,https://...
```

## 🎓 References

### Theory
- **Multi-label classification**: Binary cross-entropy on each ball independently
- **Class imbalance**: Only 6/45 balls "positive" per draw → weighted loss
- **Temporal modeling**: Transformer captures draw sequences
- **Constraint satisfaction**: Post-hoc enforcement preserves model predictions while fixing structure

### Related Reading
- Attention is All You Need (Vaswani et al., 2017)
- Lottery Prediction via ML (Okumuş & Sevinç, 2015)
- Constraint satisfaction in optimization (Russell & Norvig)

## 📞 Support

For issues or improvements, consider:
1. Check CSV format (columns, date parsing)
2. Verify history length (need 30+ draws minimum)
3. Try different `--lookback` values (15-30)
4. Inspect backtest metrics for signal (coverage >30% is good)

---

**Disclaimer**: Lottery games are inherently random. This system optimizes ticket structure within probabilistic bounds but does not guarantee wins. Play responsibly.
