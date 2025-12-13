#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netherlands Lotto / Lotto XL Deep Model with Backtest
- Keras 3 (standalone) on TensorFlow backend
- Robust CSV cleaning
- Dynamic look-back via --lookback
- Aux loss implemented as a layer (Keras 3 compliant)
"""

import argparse, os, math, random, numpy as np, pandas as pd

# Keras 3: pick backend before importing keras
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import tensorflow as tf  # backend runtime
import keras
from keras import layers
import keras.ops as ops

random.seed(7); np.random.seed(7); tf.random.set_seed(7)

BALLS = 45
DEFAULT_K = 20
D_MODEL = 128
N_HEADS = 4
FF_MULT = 4
DROPOUT = 0.25
L2 = 1e-5
POS_WEIGHT = 12.0
LAMBDA_SUM6 = 0.02
LABEL_SMOOTH = 0.02

# NOTE: Changed (21,44) to (22,44) to avoid overlap with (20,21)
ANCHORS = [(9,10),(20,21),(32,33),(22,44)]

# ------------------------
# Data
# ------------------------
def load_csv(path):
    df = pd.read_csv(path)

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date').reset_index(drop=True)

    needed = ['n1','n2','n3','n4','n5','reserve']
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}' in {path}")

    # numeric coercion
    for c in needed + (['n6'] if 'n6' in df.columns else []):
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # drop invalid rows
    df = df.dropna(subset=['n1','n2','n3','n4','n5','reserve']).reset_index(drop=True)
    for c in ['n1','n2','n3','n4','n5','reserve'] + (['n6'] if 'n6' in df.columns else []):
        if c in df.columns:
            df = df[(df[c] >= 1) & (df[c] <= BALLS)]

    if len(df) < 2:
        raise ValueError(f"Not enough valid rows after cleaning {path} (got {len(df)}).")

    return df.reset_index(drop=True)

def onehot_draw(row):
    arr = np.zeros(BALLS, dtype=np.float32)
    cols = ['n1','n2','n3','n4','n5','n6'] if 'n6' in row.index else ['n1','n2','n3','n4','n5']
    for c in cols:
        val = int(row[c])
        if 1 <= val <= BALLS:
            arr[val-1] = 1.0
    return arr

def onehot_reserve(row):
    arr = np.zeros(BALLS, dtype=np.float32)
    val = int(row['reserve'])
    if 1 <= val <= BALLS:
        arr[val-1] = 1.0
    return arr

def build_dataset(df, K=DEFAULT_K):
    if 'n6' not in df.columns:
        df = df.copy()
        df['n6'] = df['n5']

    K_eff = min(K, max(1, len(df) - 1))

    X_list, y_main_list, y_res_list, dates = [], [], [], []
    for i in range(K_eff, len(df)):
        window = df.iloc[i-K_eff:i]
        X_list.append(np.stack([onehot_draw(r) for _, r in window.iterrows()], axis=0))
        y_main_list.append(onehot_draw(df.iloc[i]))
        y_res_list.append(onehot_reserve(df.iloc[i]))
        dates.append(df.iloc[i]['date'] if 'date' in df.columns else i)

    if not X_list:
        raise ValueError(
            f"No training windows produced. Rows={len(df)}, K={K}, K_eff={K_eff}. "
            f"Add more history or lower --lookback."
        )

    return np.stack(X_list), np.stack(y_main_list), np.stack(y_res_list), dates

# ------------------------
# Model
# ------------------------
def build_positional_encoding(max_len, d_model):
    pos = np.arange(max_len)[:, None]
    i = np.arange(d_model)[None, :]
    angle_rates = 1 / np.power(10000, (2*(i//2))/np.float32(d_model))
    angle_rads = pos * angle_rates
    pe = np.zeros((max_len, d_model), dtype=np.float32)
    pe[:, 0::2] = np.sin(angle_rads[:, 0::2])
    pe[:, 1::2] = np.cos(angle_rads[:, 1::2])
    return tf.constant(pe)

class AddPositionalEncoding(layers.Layer):
    def __init__(self, max_len, d_model, **kwargs):
        super().__init__(**kwargs)
        self.max_len = int(max_len)
        self.pe = build_positional_encoding(max_len, d_model)
    def call(self, x):
        return x + self.pe[None, :self.max_len, :]

def transformer_encoder(x, d_model, n_heads, dropout, ff_mult=4):
    y = layers.LayerNormalization()(x)
    y = layers.MultiHeadAttention(n_heads, key_dim=d_model//n_heads, dropout=dropout)(y, y)
    x = layers.Add()([x, layers.Dropout(dropout)(y)])
    y = layers.LayerNormalization()(x)
    y = layers.Dense(d_model*ff_mult, activation="relu")(y)
    y = layers.Dropout(dropout)(y)
    y = layers.Dense(d_model)(y)
    return layers.Add()([x, layers.Dropout(dropout)(y)])

class WeightedBCE(keras.losses.Loss):
    def __init__(self, pos_weight=1.0, label_smooth=0.0, name="weighted_bce"):
        super().__init__(name=name)
        self.pos_weight = ops.convert_to_tensor(pos_weight, dtype="float32")
        self.label_smooth = label_smooth
    def call(self, y_true, y_pred):
        if self.label_smooth > 0.0:
            y_true = y_true * (1.0 - self.label_smooth) + 0.5 * self.label_smooth
        eps = keras.backend.epsilon()
        y_pred = ops.clip(y_pred, eps, 1.0 - eps)
        loss_pos = - y_true * ops.log(y_pred) * self.pos_weight
        loss_neg = - (1.0 - y_true) * ops.log(1.0 - y_pred)
        return ops.mean(loss_pos + loss_neg)

class Sum6Regularizer(layers.Layer):
    """Adds LAMBDA_SUM6 * mean((sum(main)-6)^2) as a model loss."""
    def __init__(self, weight=LAMBDA_SUM6, **kwargs):
        super().__init__(**kwargs)
        self.weight = weight
    def call(self, y_pred_main):
        s = ops.sum(y_pred_main, axis=-1)
        loss = ops.mean(ops.square(s - 6.0))
        self.add_loss(self.weight * loss)
        return y_pred_main

def build_model(K, F):
    inp = keras.Input(shape=(K, F), name="seq")
    x = layers.Conv1D(96, 3, padding="causal", activation="relu", dilation_rate=1,
                      kernel_regularizer=keras.regularizers.l2(L2))(inp)
    x = layers.Conv1D(96, 3, padding="causal", activation="relu", dilation_rate=2,
                      kernel_regularizer=keras.regularizers.l2(L2))(x)
    x = layers.Conv1D(128, 3, padding="causal", activation="relu", dilation_rate=4,
                      kernel_regularizer=keras.regularizers.l2(L2))(x)
    x = layers.Dense(D_MODEL)(x)
    x = AddPositionalEncoding(max_len=K, d_model=D_MODEL)(x)
    for _ in range(2):
        x = transformer_encoder(x, D_MODEL, N_HEADS, DROPOUT, FF_MULT)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(DROPOUT)(x)
    x = layers.Dense(256, activation="relu", kernel_regularizer=keras.regularizers.l2(L2))(x)
    x = layers.Dropout(DROPOUT)(x)

    main = layers.Dense(BALLS, activation="sigmoid", name="main_logits")(x)
    main = Sum6Regularizer(LAMBDA_SUM6, name="sum6_aux")(main)  # attach aux loss
    reserve = layers.Dense(BALLS, activation="softmax", name="reserve")(x)

    model = keras.Model(inp, [main, reserve], name="lotto_multitask")
    main_loss = WeightedBCE(pos_weight=POS_WEIGHT, label_smooth=LABEL_SMOOTH)
    res_loss  = keras.losses.CategoricalCrossentropy()
    model.compile(optimizer=keras.optimizers.Adam(2e-4),
                  loss={"sum6_aux": main_loss, "reserve": res_loss},
                  metrics={"reserve": ["accuracy"]})
    return model

# ------------------------
# Ticket builder
# ------------------------
def parity(n): return n % 2
def band(n):
    if 1<=n<=15: return 'low'
    if 16<=n<=30: return 'mid'
    return 'high'

def build_tickets_from_probs(main_probs, anchors=ANCHORS, tickets=8, allow_repeat_nonanchors=False):
    order = np.argsort(-main_probs) + 1
    used = set(); lines = []
    per = math.ceil(tickets / len(anchors))
    plan = []
    for p in anchors: plan += [p]*per
    plan = plan[:tickets]

    def counts(line):
        o = sum(1 for x in line if parity(x)==1)
        e = len(line)-o
        b = {'low':0,'mid':0,'high':0}
        for x in line: b[band(x)] += 1
        return o,e,b

    def pick_line(pair):
        line = set(pair)
        for n in order:
            if len(line)==6: break
            n = int(n)
            if n in line: continue
            if (n in used) and not allow_repeat_nonanchors:
                continue
            tmp = set(line); tmp.add(n)
            o,e,_ = counts(tmp)
            if o>3 or e>3: continue
            line = tmp
        o,e,_ = counts(line)
        if o!=3:
            need = 3 - o
            for rep in list(line):
                if rep in pair: continue
                for n in order:
                    n = int(n)
                    if n in line: continue
                    if (need>0 and n%2==1) or (need<0 and n%2==0):
                        line.remove(rep); line.add(n)
                        need += -1 if (n%2==1) else 1
                        if need==0: break
                if need==0: break
        _,_,b = counts(line)
        for miss in [k for k,v in b.items() if v==0]:
            for rep in list(line):
                if rep in pair: continue
                for n in order:
                    n = int(n)
                    if n in line: continue
                    if band(n)==miss and ((n%2)==(rep%2)):
                        tmp = set(line); tmp.remove(rep); tmp.add(n)
                        o,e,_ = counts(tmp)
                        if o<=3 and e<=3:
                            line = tmp; break
                _,_,b = counts(line)
                if b[miss]>0: break
        return sorted(line)

    for pair in plan:
        line = pick_line(pair)
        for n in line:
            if n not in pair:
                used.add(n)
        lines.append(line)
    return lines

# ------------------------
# Train + Predict
# ------------------------
def train_and_predict(df, K, tickets=8, epochs=40, batch=64, val_tail=24):
    X, y_main, y_res, _ = build_dataset(df, K=K)
    K_eff = X.shape[1]
    val_tail_eff = min(val_tail, max(1, len(X)//4)) if len(X) > 4 else 1
    i_split = max(1, len(X) - val_tail_eff)

    X_tr, X_val = X[:i_split], X[i_split:]
    y_main_tr, y_main_val = y_main[:i_split], y_main[i_split:]
    y_res_tr,  y_res_val  = y_res[:i_split],  y_res[i_split:]

    model = build_model(K=K_eff, F=X.shape[-1])
    cb = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4)
    ]
    model.fit(X_tr, {"sum6_aux": y_main_tr, "reserve": y_res_tr},
              validation_data=(X_val, {"sum6_aux": y_main_val, "reserve": y_res_val}),
              epochs=epochs, batch_size=batch, verbose=2, callbacks=cb)

    main_p, res_p = model.predict(X[-1:], verbose=0)
    main_p, res_p = main_p[0], res_p[0]
    lines = build_tickets_from_probs(main_p, anchors=ANCHORS, tickets=tickets)
    return lines, main_p, res_p

# ------------------------
# Backtest
# ------------------------
def match_count(line, row):
    draw = {int(row[c]) for c in ['n1','n2','n3','n4','n5','n6'] if c in row.index}
    return len(draw.intersection(set(line)))

def evaluate_set(lines, row):
    counts = [match_count(line, row) for line in lines]
    return {
        "counts": counts,
        "wins3": sum(c>=3 for c in counts),
        "wins4": sum(c>=4 for c in counts),
        "wins5": sum(c>=5 for c in counts),
        "wins6": sum(c>=6 for c in counts),
        "best": max(counts) if counts else 0
    }

def backtest(df, K, tickets=8, epochs=20, batch=64, val_tail=24, start_tail=None):
    if start_tail is not None and start_tail>0 and start_tail < len(df):
        df = df.iloc[-start_tail:].reset_index(drop=True)

    results = []
    totals = {"3":0,"4":0,"5":0,"6":0,"played":0}

    for t in range(2, len(df)):
        df_train = df.iloc[:t]
        df_eval  = df.iloc[t]
        try:
            lines, _, _ = train_and_predict(df_train, K=K, tickets=tickets,
                                            epochs=epochs, batch=batch, val_tail=val_tail)
        except Exception:
            continue
        ev = evaluate_set(lines, df_eval)
        results.append({
            "date": str(df_eval['date']) if 'date' in df.columns else t,
            "best": ev["best"],
            "wins3": ev["wins3"],
            "wins4": ev["wins4"],
            "wins5": ev["wins5"],
            "wins6": ev["wins6"],
            "lines": lines
        })
        totals["3"] += ev["wins3"]
        totals["4"] += ev["wins4"]
        totals["5"] += ev["wins5"]
        totals["6"] += ev["wins6"]
        totals["played"] += tickets
    return results, totals

# ------------------------
# CLI
# ------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to Lotto or Lotto XL history CSV")
    ap.add_argument("--game", choices=["lotto","xl"], default="xl")
    ap.add_argument("--tickets", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--val_tail", type=int, default=24, help="validation window size")
    ap.add_argument("--start_tail", type=int, default=None, help="use only the latest N rows for backtest speed")
    ap.add_argument("--backtest", action="store_true", help="run rolling backtest")
    ap.add_argument("--lookback", type=int, default=DEFAULT_K, help="look-back window K")
    args = ap.parse_args()

    df = load_csv(args.csv)

    if args.backtest:
        results, totals = backtest(df, K=args.lookback, tickets=args.tickets, epochs=args.epochs,
                                   batch=args.batch, val_tail=args.val_tail, start_tail=args.start_tail)
        print("\nBacktest totals:")
        print(totals)
        print("\nLast 3 evaluations:")
        for r in results[-3:]:
            print(r["date"], "best:", r["best"], "wins3:", r["wins3"], "wins4:", r["wins4"])
    else:
        lines, main_p, res_p = train_and_predict(df, K=args.lookback, tickets=args.tickets,
                                                 epochs=args.epochs, batch=args.batch, val_tail=args.val_tail)
        print(f"\nGame: {args.game.upper()} | Tickets: {args.tickets}")
        for i, line in enumerate(lines, 1):
            print(f"{i:02d}) {', '.join(str(n) for n in line)}")
        top_idx = np.argsort(-main_p)[:15] + 1
        print("\nTop-15 balls by main probability:")
        print(", ".join(f"{int(b)}:{main_p[b-1]:.3f}" for b in top_idx))

if __name__ == "__main__":
    main()
