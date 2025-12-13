# nl_lotto_deep_model.py
"""
Deep Learning Lottery Predictor for Netherlands Lotto / Lotto XL
---------------------------------------------------------------
Usage examples:
    python nl_lotto_deep_model.py --game xl --csv nl_lotto_xl_history.csv --tickets 8
    python nl_lotto_deep_model.py --game lotto --csv nl_lotto_history.csv --tickets 12
"""

import argparse, numpy as np, pandas as pd, tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# -----------------------------
# Helpers
# -----------------------------
BALLS = 45
# NOTE: Changed (21,44) to (22,44) to avoid overlap with (20,21)
ANCHORS = [(9,10),(20,21),(32,33),(22,44)]

def load_data(csv_path, K=20):
    df = pd.read_csv(csv_path)
    
    # Validate required columns exist
    required_cols = ["date", "n1", "n2", "n3", "n4", "n5", "n6", "reserve"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")
    
    # Parse date with error handling
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    # Validate numeric columns
    for col in ["n1", "n2", "n3", "n4", "n5", "n6", "reserve"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["n1", "n2", "n3", "n4", "n5", "n6", "reserve"])
    
    if len(df) < K + 1:
        raise ValueError(f"Not enough valid data rows. Need at least {K+1}, got {len(df)}")

    def draw_to_onehot(row):
        arr = np.zeros(BALLS, dtype=np.float32)
        for c in ["n1","n2","n3","n4","n5","n6"]:
            arr[int(row[c])-1] = 1.0
        return arr

    def reserve_to_onehot(row):
        arr = np.zeros(BALLS, dtype=np.float32)
        arr[int(row["reserve"])-1] = 1.0
        return arr

    X, y_main, y_res = [], [], []
    for i in range(K, len(df)):
        window = df.iloc[i-K:i]
        X.append(np.stack([draw_to_onehot(r) for _,r in window.iterrows()], axis=0))
        y_main.append(draw_to_onehot(df.iloc[i]))
        y_res.append(reserve_to_onehot(df.iloc[i]))
    return np.stack(X), np.stack(y_main), np.stack(y_res)

def build_model(K=20, F=45):
    inp = keras.Input(shape=(K,F))
    x = layers.Conv1D(64, 3, padding="causal", activation="relu")(inp)
    x = layers.Conv1D(64, 3, padding="causal", activation="relu", dilation_rate=2)(x)
    x = layers.Bidirectional(layers.LSTM(64))(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)

    main = layers.Dense(F, activation="sigmoid", name="main")(x)
    res  = layers.Dense(F, activation="softmax", name="reserve")(x)

    model = keras.Model(inp, [main, res])
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss={"main":"binary_crossentropy","reserve":"categorical_crossentropy"},
        metrics={"reserve":"accuracy"}
    )
    return model

# Enforce ticket rules: anchors, 3 odd / 3 even, low/mid/high
def enforce_rules(probs, anchors=ANCHORS, tickets=8):
    ranked = np.argsort(-probs) + 1
    pool = ranked.tolist()
    out = []

    def band(n):
        if 1<=n<=15: return "low"
        if 16<=n<=30: return "mid"
        return "high"

    for i in range(tickets):
        pair = anchors[i % len(anchors)]
        line = set(pair)
        for n in pool:
            if len(line)==6: break
            if n in line: continue
            line.add(n)
        # fix odd/even
        odds = [n for n in line if n%2==1]
        evens= [n for n in line if n%2==0]
        while len(odds)>3:
            swap = odds.pop()
            for c in pool:
                if c%2==0 and c not in line: line.remove(swap); line.add(c); break
        while len(evens)>3:
            swap = evens.pop()
            for c in pool:
                if c%2==1 and c not in line: line.remove(swap); line.add(c); break
        # ensure low/mid/high
        bands = {b:0 for b in ["low","mid","high"]}
        for n in line: bands[band(n)]+=1
        for need in [b for b,v in bands.items() if v==0]:
            for swap in list(line):
                for c in pool:
                    if c not in line and band(c)==need:
                        line.remove(swap); line.add(c); break
                if need not in [b for b,v in bands.items() if v==0]: break
        out.append(sorted(line))
    return out

# -----------------------------
# Main
# -----------------------------
if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to Lotto or Lotto XL CSV")
    ap.add_argument("--game", choices=["lotto","xl"], required=True)
    ap.add_argument("--tickets", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=15)
    args = ap.parse_args()

    X, y_main, y_res = load_data(args.csv, K=20)
    split = int(0.9*len(X))
    X_train, X_val = X[:split], X[split:]
    y_main_train, y_main_val = y_main[:split], y_main[split:]
    y_res_train, y_res_val = y_res[:split], y_res[split:]

    model = build_model(K=20, F=BALLS)
    model.fit(
        X_train, {"main":y_main_train,"reserve":y_res_train},
        validation_data=(X_val, {"main":y_main_val,"reserve":y_res_val}),
        epochs=args.epochs, batch_size=16, verbose=1
    )

    last_in = X[-1: ]
    pred_main, pred_res = model.predict(last_in, verbose=0)
    pred_main = pred_main[0]

    print("\nTop 15 model picks by probability:")
    ranked = np.argsort(-pred_main)+1
    print(ranked[:15])

    tickets = enforce_rules(pred_main, tickets=args.tickets)
    print("\nFINAL {} {} tickets:".format(args.tickets, args.game.upper()))
    for i,t in enumerate(tickets,1):
        print(f"Ticket {i}: {t}")
