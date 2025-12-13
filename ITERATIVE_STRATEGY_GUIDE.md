# Iterative Lottery Strategy System

## Overview
This system implements a structured "Plan-Do-Check-Act" cycle for lottery prediction, moving beyond simple number guessing to a strategy-based approach.

## Workflow

### 1. Friday: Prediction (Phase 1)
Run the new production app to generate tickets with explicit rationale.

```bash
python production_app_v2.py
```

**Outputs:**
- `predictions/prediction_rationale_YYYYMMDD.json`: Full data with rationale.
- `predictions/tickets_YYYYMMDD.csv`: Printable tickets.
- Email notification.

**Key Features:**
- Generates **12 XL Tickets** (Actual Play) using XL anchors (pairs).
- Generates **12 Lotto Tickets** (Theoretical) using Lotto anchors (singles).
- Enforces strict constraints (3 Odd/3 Even, Spread).
- Records **WHY** every ticket was generated.

### 2. Sunday: Post-Mortem (Phase 2)
After the draw, analyze performance against the rationale.

```bash
# Example: Draw was 5, 12, 23, 34, 40, 44 with Reserve 2
python post_mortem.py predictions/prediction_rationale_YYYYMMDD.json 5,12,23,34,40,44 2
```

**Outputs:**
- Console report of hits/misses per ticket.
- Identification of successful/failed anchors.
- `_REPORT.json` file.

### 3. Monday: Strategy Update (Phase 3)
Edit `strategy_state.yaml` based on the post-mortem findings.

- **If XL anchors (9,10) missed:** Lower their weight or rotate them out.
- **If "Aggressive" tickets performed best:** Increase aggressive allocation.
- **If Odd/Even balance was off:** Adjust tolerance.

## Configuration Files

### `strategy_state.yaml`
The "brain" of the system. Stores:
- Active anchors and their weights.
- Hot/Cold number lists.
- Aggression levels (Conservative vs Aggressive split).

### `config.yaml`
Technical settings (Email, Paths, Model params).

## Files Created
- `production_app_v2.py`: The new main engine.
- `constraint_generator_v2.py`: Logic for rationale generation.
- `post_mortem.py`: Analysis tool.
- `strategy_state.yaml`: Memory file.

## Next Steps
1. **Run `python production_app_v2.py`** to generate your first set of "Rational" tickets.
2. **Wait for the draw.**
3. **Run `post_mortem.py`** to see how your strategy performed.
4. **Update `strategy_state.yaml`** to improve for next week.
