#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Comparison Script
Compare baseline vs enhanced model performance
"""

import numpy as np
import time
from data_pipeline import LottoData, build_sequence_dataset

print("=" * 70)
print("MODEL COMPARISON: Baseline vs Enhanced")
print("=" * 70)

# Load data
print("\n1. Loading data...")
data = LottoData("nl_lotto_xl_history.csv", game="xl")
print(f"   ✓ Loaded {len(data)} draws")

# Build dataset
print("\n2. Building sequences...")
X, y_main, y_reserve, dates = build_sequence_dataset(data.get_df(), lookback=20)
print(f"   ✓ Created {len(X)} sequences")

# Split data
split_idx = int(len(X) * 0.8)
X_train, X_val = X[:split_idx], X[split_idx:]
y_main_train, y_main_val = y_main[:split_idx], y_main[split_idx:]
y_res_train, y_res_val = y_reserve[:split_idx], y_reserve[split_idx:]

print(f"   ✓ Train: {len(X_train)}, Val: {len(X_val)}")

# Test baseline model
print("\n" + "=" * 70)
print("BASELINE MODEL")
print("=" * 70)

try:
    from ml_model import build_model, train_model
    
    print("\n3. Building baseline model...")
    model_baseline = build_model(
        lookback=20,
        balls=45,
        d_model=128,
        n_heads=4,
        dropout=0.25
    )
    params_baseline = model_baseline.count_params()
    print(f"   ✓ Parameters: {params_baseline:,}")
    
    print("\n4. Training baseline model...")
    start = time.time()
    history_baseline = train_model(
        model_baseline,
        X_train, y_main_train, y_res_train,
        X_val, y_main_val, y_res_val,
        epochs=50,
        batch_size=64,
        verbose=0
    )
    time_baseline = time.time() - start
    
    # Get final metrics
    final_loss_baseline = history_baseline.history['val_loss'][-1]
    final_acc_baseline = history_baseline.history['val_reserve_accuracy'][-1]
    
    print(f"   ✓ Training time: {time_baseline:.1f}s")
    print(f"   ✓ Final val_loss: {final_loss_baseline:.4f}")
    print(f"   ✓ Reserve accuracy: {final_acc_baseline:.2%}")
    
    # Test prediction
    print("\n5. Testing baseline predictions...")
    X_test = X_val[:1]
    probs_main_baseline, probs_res_baseline = model_baseline.predict(X_test, verbose=0)
    
    # Get top predictions
    top_10_baseline = np.argsort(probs_main_baseline[0])[-10:][::-1] + 1
    print(f"   Top 10 numbers: {sorted(top_10_baseline.tolist())}")
    
    # Calculate prediction diversity (entropy)
    entropy_baseline = -np.sum(probs_main_baseline[0] * np.log(probs_main_baseline[0] + 1e-10))
    print(f"   Prediction entropy: {entropy_baseline:.3f}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    model_baseline = None

# Test enhanced model
print("\n" + "=" * 70)
print("ENHANCED MODEL")
print("=" * 70)

try:
    from ml_model_enhanced import build_enhanced_model, train_enhanced_model
    
    print("\n3. Building enhanced model...")
    model_enhanced = build_enhanced_model(
        lookback=20,
        balls=45,
        d_model=192,
        n_heads=6,
        n_layers=4,
        dropout=0.3
    )
    params_enhanced = model_enhanced.count_params()
    print(f"   ✓ Parameters: {params_enhanced:,}")
    
    print("\n4. Training enhanced model...")
    start = time.time()
    history_enhanced = train_enhanced_model(
        model_enhanced,
        X, y_main, y_reserve,
        epochs=50,  # Use 50 for fair comparison
        batch_size=8,
        val_size=0.2,
        verbose=0
    )
    time_enhanced = time.time() - start
    
    # Get final metrics
    final_loss_enhanced = history_enhanced.history['val_loss'][-1]
    final_acc_enhanced = history_enhanced.history['val_reserve_accuracy'][-1]
    
    print(f"   ✓ Training time: {time_enhanced:.1f}s")
    print(f"   ✓ Final val_loss: {final_loss_enhanced:.4f}")
    print(f"   ✓ Reserve accuracy: {final_acc_enhanced:.2%}")
    
    # Test prediction
    print("\n5. Testing enhanced predictions...")
    X_test = X_val[:1]
    probs_main_enhanced, probs_res_enhanced = model_enhanced.predict(X_test, verbose=0)
    
    # Get top predictions
    top_10_enhanced = np.argsort(probs_main_enhanced[0])[-10:][::-1] + 1
    print(f"   Top 10 numbers: {sorted(top_10_enhanced.tolist())}")
    
    # Calculate prediction diversity (entropy)
    entropy_enhanced = -np.sum(probs_main_enhanced[0] * np.log(probs_main_enhanced[0] + 1e-10))
    print(f"   Prediction entropy: {entropy_enhanced:.3f}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    model_enhanced = None

# Comparison summary
print("\n" + "=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)

if model_baseline and model_enhanced:
    print("\n{:<25} {:>15} {:>15} {:>15}".format("Metric", "Baseline", "Enhanced", "Improvement"))
    print("-" * 70)
    
    # Parameters
    param_diff = ((params_enhanced - params_baseline) / params_baseline) * 100
    print("{:<25} {:>15,} {:>15,} {:>14.0f}%".format(
        "Parameters", params_baseline, params_enhanced, param_diff
    ))
    
    # Training time
    time_diff = ((time_enhanced - time_baseline) / time_baseline) * 100
    print("{:<25} {:>14.1f}s {:>14.1f}s {:>14.0f}%".format(
        "Training time", time_baseline, time_enhanced, time_diff
    ))
    
    # Validation loss
    loss_diff = ((final_loss_baseline - final_loss_enhanced) / final_loss_baseline) * 100
    print("{:<25} {:>15.4f} {:>15.4f} {:>14.0f}%".format(
        "Validation loss", final_loss_baseline, final_loss_enhanced, loss_diff
    ))
    
    # Reserve accuracy
    acc_diff = ((final_acc_enhanced - final_acc_baseline) / final_acc_baseline) * 100
    print("{:<25} {:>14.2%} {:>14.2%} {:>14.0f}%".format(
        "Reserve accuracy", final_acc_baseline, final_acc_enhanced, acc_diff
    ))
    
    # Prediction diversity
    div_diff = ((entropy_enhanced - entropy_baseline) / entropy_baseline) * 100
    print("{:<25} {:>15.3f} {:>15.3f} {:>14.0f}%".format(
        "Prediction entropy", entropy_baseline, entropy_enhanced, div_diff
    ))
    
    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    
    if final_loss_enhanced < final_loss_baseline:
        print("\n✓ Enhanced model shows BETTER performance:")
        print(f"  - {loss_diff:.1f}% lower validation loss")
        print(f"  - {acc_diff:.1f}% higher reserve accuracy")
        print(f"  - {div_diff:.1f}% more diverse predictions")
        print(f"\n  Trade-off: {time_diff:.1f}% longer training time")
    else:
        print("\n⚠ Results may vary - consider:")
        print("  - Training for more epochs (100 vs 50)")
        print("  - Multiple runs with different seeds")
        print("  - Larger dataset for deeper model")
    
    print("\n" + "=" * 70)

else:
    print("\n✗ Could not complete comparison")
    if not model_baseline:
        print("  - Baseline model failed")
    if not model_enhanced:
        print("  - Enhanced model failed")

print("\nDone!")
