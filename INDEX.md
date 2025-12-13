# 📑 Complete File Index & Navigation Guide

## Quick Navigation

**Just want to run it?**
→ Start with `quickstart.bat` (Windows) or `quickstart.sh` (Linux/Mac)

**Want to understand the system?**
→ Read `README.md` first

**Need to tune strategy?**
→ See `STRATEGY_TUNING_GUIDE.md`

**Want hands-on walkthrough?**
→ Open `interactive_notebook.ipynb` in Jupyter

**Need code examples?**
→ Check `quick_reference.py`

---

## 📂 File Structure

### Core System (5 modules)

| File | Size | Purpose | Key Classes |
|------|------|---------|------------|
| `main.py` | 200 loc | Orchestrator & CLI | `LottoSystem` |
| `data_pipeline.py` | 320 loc | Data loading & stats | `LottoData` |
| `ml_model.py` | 280 loc | Transformer model | `build_model()`, `train_model()` |
| `constraint_generator.py` | 380 loc | Anchor-based ticket generation | `TicketGenerator`, `TicketConfig` |
| `backtest_engine.py` | 150 loc | Performance evaluation | `BacktestEngine`, `BacktestResult` |

### Documentation (5 guides)

| File | Purpose | Audience | Reading Time |
|------|---------|----------|--------------|
| `README.md` | Complete guide | All users | 20 min |
| `STRATEGY_TUNING_GUIDE.md` | Advanced tuning | Experts | 30 min |
| `SYSTEM_SUMMARY.md` | High-level overview | Decision makers | 15 min |
| `quick_reference.py` | Code recipes | Developers | As needed |
| `INDEX.md` | This file | Navigators | 5 min |

### Data & Scripts

| File | Purpose |
|------|---------|
| `nl_lotto_xl_history.csv` | Sample XL history (12 draws) |
| `nl_lotto_history.csv` | Sample Lotto history (12 draws) |
| `quickstart.bat` | Windows launcher |
| `quickstart.sh` | Linux/Mac launcher |
| `interactive_notebook.ipynb` | Jupyter notebook |

### Legacy (Keep for reference, but use new system)

| File | Status |
|------|--------|
| `lotto.py` | Superseded by new architecture |
| `nl_lotto.py` | Superseded by new architecture |
| `nl_lotto_deep_model_bt.py` | Superseded by new architecture |

---

## 🚀 Getting Started Paths

### Path 1: I just want to generate tickets (5 minutes)

1. **Run quickstart**
   ```bash
   # Windows:
   quickstart.bat predict
   
   # Linux/Mac:
   bash quickstart.sh predict
   ```

2. **Output**: 12 coverage + 4 convergence tickets
3. **Next**: Buy tickets and play!

---

### Path 2: I want to understand the system (30 minutes)

1. **Read** `README.md` (overview + quick start)
2. **Skim** `STRATEGY_TUNING_GUIDE.md` (profiles A, B, C)
3. **Run** `quickstart.bat demo` (see it in action)
4. **Done**: You understand the core concepts

---

### Path 3: I want to optimize my strategy (1-2 hours)

1. **Read** `STRATEGY_TUNING_GUIDE.md` (full)
2. **Open** `interactive_notebook.ipynb` (hands-on)
3. **Run** `quickstart.bat backtest` (evaluate current)
4. **Experiment** with different hyperparameters:
   ```bash
   python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --lookback 25 --epochs 50
   ```
5. **Pick** best config based on backtest metrics

---

### Path 4: I want to integrate with my own code (2-3 hours)

1. **Read** `quick_reference.py` (recipes 1-6)
2. **Copy** patterns into your code:
   ```python
   from main import LottoSystem
   
   system = LottoSystem("your_csv.csv")
   system.train(epochs=30)
   tickets, probs, _ = system.predict()
   ```
3. **Customize** as needed (recipes 7-10 show advanced patterns)

---

### Path 5: I want to run a full backtest + analysis (30-60 minutes)

1. **Open** `interactive_notebook.ipynb` in Jupyter
2. **Run** cells sequentially (covers all steps)
3. **Generate** visualizations and metrics
4. **Export** results to CSV

---

## 📖 Documentation Map

### By Use Case

**"How do I...?"**

| Question | Answer |
|----------|--------|
| ...start from scratch? | `README.md` → Quick Start |
| ...generate tickets? | `quickstart.bat predict` |
| ...run a backtest? | `quickstart.bat backtest` |
| ...understand anchors? | `README.md` → Core Principles |
| ...tune the strategy? | `STRATEGY_TUNING_GUIDE.md` |
| ...write custom code? | `quick_reference.py` |
| ...debug issues? | `STRATEGY_TUNING_GUIDE.md` → Troubleshooting |
| ...understand the model? | `README.md` → Understanding the Model |
| ...get an overview? | `SYSTEM_SUMMARY.md` |
| ...learn hands-on? | `interactive_notebook.ipynb` |

---

## 🔧 Common Tasks & Where to Find Them

### Task: Generate tickets for this week
**Files**: `main.py`, `quickstart.bat`  
**Time**: 5-10 min  
```bash
quickstart.bat predict
```

### Task: Evaluate if strategy is working
**Files**: `main.py`, `backtest_engine.py`  
**Time**: 10-30 min  
```bash
python main.py --csv nl_lotto_xl_history.csv --game xl --backtest --start_tail 100
```

### Task: Understand why a specific ticket won/lost
**Files**: `backtest_engine.py`, `interactive_notebook.ipynb`  
**Time**: 15 min  
See notebook section 7 (Quick Backtest)

### Task: Optimize for 5-hit rate instead of 3-hit rate
**Files**: `STRATEGY_TUNING_GUIDE.md`, `constraint_generator.py`  
**Time**: 30-60 min  
Read "Goal: Increase 5+6 Hit Rate" section

### Task: Export tickets to CSV
**Files**: `quick_reference.py` (recipe 6)  
**Time**: 10 min  
Copy recipe 6 code

### Task: Run ensemble prediction (multiple models)
**Files**: `quick_reference.py` (recipe 10)  
**Time**: 20 min  
Copy recipe 10 code

### Task: Compare different strategy profiles
**Files**: `STRATEGY_TUNING_GUIDE.md` (profiles A, B, C)  
**Time**: 45 min  
Run backtest with each profile's config, compare metrics

### Task: Add weekly automation
**Files**: `quick_reference.py` (recipe 9)  
**Time**: 15 min  
Copy recipe 9, adapt to your cron/scheduler

---

## 📊 Module Dependencies

```
main.py
  ├── data_pipeline.py
  │   └── (pandas, numpy)
  ├── ml_model.py
  │   └── (tensorflow, keras, numpy)
  ├── constraint_generator.py
  │   └── (numpy)
  └── backtest_engine.py
      └── (numpy, pandas, dataclasses)

interactive_notebook.ipynb
  ├── all modules above
  ├── matplotlib
  └── seaborn
```

**Minimum Requirements**:
```
Python 3.8+
tensorflow >= 2.10
keras >= 3.0
numpy >= 1.20
pandas >= 1.3
```

**Optional**:
```
matplotlib (for plotting)
seaborn (for pretty plots)
jupyter (for notebook)
```

---

## ✅ Verification Checklist

After download/setup, verify:

- [ ] All 5 core modules present: `main.py`, `data_pipeline.py`, `ml_model.py`, `constraint_generator.py`, `backtest_engine.py`
- [ ] CSV files present: `nl_lotto_xl_history.csv`, `nl_lotto_history.csv`
- [ ] All guides present: `README.md`, `STRATEGY_TUNING_GUIDE.md`, `SYSTEM_SUMMARY.md`
- [ ] Scripts present: `quickstart.bat`, `quickstart.sh`
- [ ] Notebook present: `interactive_notebook.ipynb`
- [ ] `quick_reference.py` present
- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install tensorflow keras numpy pandas`

**Quick test**:
```bash
python main.py --help
```
Should show CLI options without errors.

---

## 🎓 Learning Path Recommendation

### Week 1: Learn the System
- Day 1: Read `README.md` (30 min)
- Day 2: Run `quickstart.bat demo` (10 min)
- Day 3: Read `STRATEGY_TUNING_GUIDE.md` profiles (20 min)
- Day 4-5: Play with `interactive_notebook.ipynb` (1 hour)
- Day 6-7: Experiment with different configs (2 hours)

### Week 2: Deploy & Monitor
- Day 1: Choose strategy (A, B, or C)
- Day 2-7: Run `quickstart.bat predict` weekly, track results
- Record metrics: coverage_3, coverage_5, avg_match

### Week 3+: Optimize & Iterate
- Monthly backtest: `python main.py --csv ... --backtest --start_tail 200`
- Analyze results
- Adjust hyperparameters
- Document findings

---

## 🆘 Need Help?

### Technical Issues

1. **"Module not found"**
   - Check all 5 core `.py` files present in same directory
   - Run from correct directory

2. **"Model training too slow"**
   - Use `--batch 128` (larger batches)
   - Use `--lookback 15` (shorter sequences)
   - Use `--start_tail 50` for backtest

3. **"Low backtest scores"**
   - Need more history (50+ draws minimum)
   - Try `--epochs 60` (more training)
   - Try `--lookback 25-30` (longer memory)

### Strategy Questions

**"Which profile should I use?"**
- Conservative/safe? → Profile A
- Aggressive/high-risk? → Profile B
- Balanced? → Profile C
See `STRATEGY_TUNING_GUIDE.md` for full decision tree

**"How do I know if my strategy is working?"**
- Coverage_3 > 30% = good signal
- Coverage_5 > 1% = above random
- Avg_match > 2.5 = model learning
See backtest output in README

### Conceptual Questions

- "What are anchors?" → `README.md` → Core Principles
- "Why Transformer?" → `README.md` → Understanding the Model
- "How does constraint enforcement work?" → `SYSTEM_SUMMARY.md` → Architecture

---

## 📝 Version History

- **v1.0** (Dec 12, 2025): Initial release
  - Clean modular architecture
  - 5 core modules
  - 4 comprehensive guides
  - Jupyter notebook
  - Quick reference recipes
  - Windows/Linux launchers

---

## 📞 Support

**For code issues**: Check module docstrings + quick_reference.py  
**For strategy questions**: Read STRATEGY_TUNING_GUIDE.md  
**For system overview**: Read SYSTEM_SUMMARY.md  
**For hands-on**: Use interactive_notebook.ipynb  
**For examples**: See quick_reference.py (10 recipes)

---

**Happy predicting! 🍀**

*Last updated: December 12, 2025*
