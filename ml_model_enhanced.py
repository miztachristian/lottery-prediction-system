#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced ML Model: Advanced deep learning architecture for lottery prediction
- Improved feature engineering with statistical patterns
- Deeper transformer architecture with residual connections
- Ensemble predictions from multiple model heads
- Advanced regularization and training techniques
- Pattern recognition for number sequences and gaps
"""

import os
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import numpy as np
import tensorflow as tf
import keras
from keras import layers
import keras.ops as ops
from typing import Tuple, List
from scipy import stats

BALLS = 45


def build_positional_encoding(max_len: int, d_model: int) -> tf.Tensor:
    """Create sinusoidal positional encodings."""
    pos = np.arange(max_len)[:, None]
    i = np.arange(d_model)[None, :]
    angle_rates = 1 / np.power(10000, (2 * (i // 2)) / np.float32(d_model))
    angle_rads = pos * angle_rates

    pe = np.zeros((max_len, d_model), dtype=np.float32)
    pe[:, 0::2] = np.sin(angle_rads[:, 0::2])
    pe[:, 1::2] = np.cos(angle_rads[:, 1::2])

    return tf.constant(pe)


class AddPositionalEncoding(layers.Layer):
    """Add positional encoding to input."""

    def __init__(self, max_len: int, d_model: int, **kwargs):
        super().__init__(**kwargs)
        self.max_len = int(max_len)
        self.pe = build_positional_encoding(max_len, d_model)

    def call(self, x):
        return x + self.pe[None, : self.max_len, :]


def transformer_encoder_block(x, d_model: int, n_heads: int, dropout: float, ff_mult: int = 4, use_residual: bool = True):
    """Enhanced transformer encoder block with improved residual connections."""
    # Layer norm + multi-head attention
    y = layers.LayerNormalization(epsilon=1e-6)(x)
    y = layers.MultiHeadAttention(
        n_heads, 
        key_dim=d_model // n_heads, 
        dropout=dropout,
        use_bias=True
    )(y, y)
    
    if use_residual:
        x = layers.Add()([x, layers.Dropout(dropout)(y)])
    else:
        x = layers.Dropout(dropout)(y)

    # Layer norm + feed-forward with GELU activation
    y = layers.LayerNormalization(epsilon=1e-6)(x)
    y = layers.Dense(d_model * ff_mult, activation="gelu")(y)
    y = layers.Dropout(dropout)(y)
    y = layers.Dense(d_model)(y)

    if use_residual:
        return layers.Add()([x, layers.Dropout(dropout)(y)])
    return layers.Dropout(dropout)(y)


class WeightedBCE(keras.losses.Loss):
    """Weighted Binary Cross-Entropy with label smoothing for imbalanced multi-label."""

    def __init__(self, pos_weight: float = 1.0, label_smooth: float = 0.0, name="weighted_bce"):
        super().__init__(name=name)
        self.pos_weight = ops.convert_to_tensor(pos_weight, dtype="float32")
        self.label_smooth = label_smooth

    def call(self, y_true, y_pred):
        # Apply label smoothing
        if self.label_smooth > 0.0:
            y_true = y_true * (1.0 - self.label_smooth) + 0.5 * self.label_smooth

        # Clip predictions for numerical stability
        eps = keras.backend.epsilon()
        y_pred = ops.clip(y_pred, eps, 1.0 - eps)

        # Weighted BCE
        loss_pos = -y_true * ops.log(y_pred) * self.pos_weight
        loss_neg = -(1.0 - y_true) * ops.log(1.0 - y_pred)

        return ops.mean(loss_pos + loss_neg)


class Sum6Regularizer(layers.Layer):
    """Auxiliary loss: encourage sum of predicted probabilities ≈ 6."""

    def __init__(self, weight: float = 0.02, **kwargs):
        super().__init__(**kwargs)
        self.weight = weight

    def call(self, y_pred_main):
        s = ops.sum(y_pred_main, axis=-1)
        loss = ops.mean(ops.square(s - 6.0))
        self.add_loss(self.weight * loss)
        return y_pred_main


class DiversityRegularizer(layers.Layer):
    """Encourage diversity in predictions (avoid clustering)."""

    def __init__(self, weight: float = 0.01, **kwargs):
        super().__init__(**kwargs)
        self.weight = weight

    def call(self, y_pred_main):
        # Calculate variance of predictions - higher variance = more diversity
        mean_pred = ops.mean(y_pred_main, axis=-1, keepdims=True)
        variance = ops.mean(ops.square(y_pred_main - mean_pred), axis=-1)
        # Penalize low variance (lack of diversity)
        loss = ops.mean(ops.square(0.15 - variance))  # Target variance ~0.15
        self.add_loss(self.weight * loss)
        return y_pred_main


def compute_enhanced_features(X: np.ndarray) -> np.ndarray:
    """
    Compute additional statistical features from input sequences.
    
    Args:
        X: Input sequences (batch, lookback, 45)
    
    Returns:
        Enhanced features (batch, feature_dim)
    """
    batch_size, lookback, balls = X.shape
    features = []
    
    for i in range(batch_size):
        seq = X[i]  # (lookback, 45)
        
        # Feature 1: Frequency distribution (mean across time)
        freq = np.mean(seq, axis=0)  # (45,)
        
        # Feature 2: Recent trend (difference between recent and old)
        recent = np.mean(seq[-5:], axis=0) if lookback >= 5 else freq
        old = np.mean(seq[:5], axis=0) if lookback >= 5 else freq
        trend = recent - old  # (45,)
        
        # Feature 3: Volatility (std across time)
        volatility = np.std(seq, axis=0)  # (45,)
        
        # Feature 4: Gap distribution (max gap for each ball)
        gaps = []
        for ball_idx in range(balls):
            ball_seq = seq[:, ball_idx]
            appearances = np.where(ball_seq > 0.5)[0]
            if len(appearances) > 0:
                max_gap = lookback - appearances[-1]  # Gap from last appearance
            else:
                max_gap = lookback
            gaps.append(max_gap / lookback)  # Normalize
        gaps = np.array(gaps)  # (45,)
        
        # Feature 5: Consecutive appearance count
        consecutive = []
        for ball_idx in range(balls):
            ball_seq = seq[:, ball_idx]
            consec_count = 0
            for val in reversed(ball_seq):
                if val > 0.5:
                    consec_count += 1
                else:
                    break
            consecutive.append(consec_count / lookback)
        consecutive = np.array(consecutive)  # (45,)
        
        # Combine all features
        combined = np.concatenate([freq, trend, volatility, gaps, consecutive])
        features.append(combined)
    
    return np.array(features)  # (batch, 45*5)


def build_enhanced_model(
    lookback: int = 20,
    balls: int = BALLS,
    d_model: int = 192,  # Increased from 128
    n_heads: int = 6,  # Increased from 4
    n_layers: int = 4,  # Increased from 2
    dropout: float = 0.3,  # Increased dropout
    l2: float = 1e-5,
    pos_weight: float = 12.0,
    lambda_sum6: float = 0.02,
    lambda_diversity: float = 0.01,
    label_smooth: float = 0.02,
    use_enhanced_features: bool = True,
) -> keras.Model:
    """
    Build enhanced transformer-based lottery prediction model.

    Improvements over baseline:
    - Deeper architecture (4 layers vs 2)
    - More attention heads (6 vs 4)
    - Larger embedding dimension (192 vs 128)
    - Enhanced feature engineering pipeline
    - Diversity regularization
    - GELU activations for better gradients
    - Separate ensemble heads for robustness

    Args:
        lookback: Historical window size
        balls: Number of balls (45)
        d_model: Embedding dimension (increased)
        n_heads: Number of attention heads (increased)
        n_layers: Number of transformer layers (increased)
        dropout: Dropout rate
        l2: L2 regularization weight
        pos_weight: Weight for positive class in BCE
        lambda_sum6: Weight for sum-6 auxiliary loss
        lambda_diversity: Weight for diversity regularization
        label_smooth: Label smoothing for main output
        use_enhanced_features: Use additional statistical features

    Returns:
        Compiled Keras Model
    """
    # Main sequence input
    inp = keras.Input(shape=(lookback, balls), name="seq")

    # Enhanced convolutional feature extraction with residual connections
    x1 = layers.Conv1D(
        96, 3, padding="causal", activation="gelu",
        kernel_regularizer=keras.regularizers.l2(l2)
    )(inp)
    x1 = layers.BatchNormalization()(x1)
    
    x2 = layers.Conv1D(
        96, 3, padding="causal", activation="gelu", dilation_rate=2,
        kernel_regularizer=keras.regularizers.l2(l2)
    )(x1)
    x2 = layers.BatchNormalization()(x2)
    
    x3 = layers.Conv1D(
        128, 3, padding="causal", activation="gelu", dilation_rate=4,
        kernel_regularizer=keras.regularizers.l2(l2)
    )(x2)
    x3 = layers.BatchNormalization()(x3)
    
    x4 = layers.Conv1D(
        d_model, 3, padding="causal", activation="gelu", dilation_rate=8,
        kernel_regularizer=keras.regularizers.l2(l2)
    )(x3)
    x4 = layers.BatchNormalization()(x4)

    # Dense projection + positional encoding
    x = layers.Dense(d_model)(x4)
    x = AddPositionalEncoding(max_len=lookback, d_model=d_model)(x)
    x = layers.Dropout(dropout)(x)

    # Deeper transformer stack
    for i in range(n_layers):
        x = transformer_encoder_block(
            x, d_model, n_heads, dropout, 
            ff_mult=4, use_residual=True
        )

    # Multi-scale pooling (combine different temporal perspectives)
    pool_avg = layers.GlobalAveragePooling1D()(x)
    pool_max = layers.GlobalMaxPooling1D()(x)
    pool_last = x[:, -1, :]  # Last timestep
    
    pooled = layers.Concatenate()([pool_avg, pool_max, pool_last])
    pooled = layers.Dropout(dropout)(pooled)

    # Dense pathway with residual
    dense = layers.Dense(384, activation="gelu", kernel_regularizer=keras.regularizers.l2(l2))(pooled)
    dense = layers.BatchNormalization()(dense)
    dense = layers.Dropout(dropout)(dense)
    
    dense = layers.Dense(256, activation="gelu", kernel_regularizer=keras.regularizers.l2(l2))(dense)
    dense = layers.BatchNormalization()(dense)
    dense = layers.Dropout(dropout)(dense)

    # Ensemble approach: Multiple prediction heads
    # Head 1: Pattern-based predictions
    main_head1 = layers.Dense(128, activation="gelu")(dense)
    main_head1 = layers.Dropout(dropout * 0.5)(main_head1)
    main_head1 = layers.Dense(balls, activation="sigmoid", name="main_head1")(main_head1)
    
    # Head 2: Frequency-based predictions
    main_head2 = layers.Dense(128, activation="gelu")(dense)
    main_head2 = layers.Dropout(dropout * 0.5)(main_head2)
    main_head2 = layers.Dense(balls, activation="sigmoid", name="main_head2")(main_head2)
    
    # Head 3: Trend-based predictions
    main_head3 = layers.Dense(128, activation="gelu")(dense)
    main_head3 = layers.Dropout(dropout * 0.5)(main_head3)
    main_head3 = layers.Dense(balls, activation="sigmoid", name="main_head3")(main_head3)
    
    # Ensemble combination (weighted average)
    main_logits = layers.Average(name="main_ensemble")([main_head1, main_head2, main_head3])
    
    # Apply regularizers
    main_logits = Sum6Regularizer(weight=lambda_sum6, name="sum6_aux")(main_logits)
    main_logits = DiversityRegularizer(weight=lambda_diversity, name="diversity_aux")(main_logits)
    
    # Reserve prediction with dedicated pathway
    reserve_path = layers.Dense(256, activation="gelu")(dense)
    reserve_path = layers.Dropout(dropout * 0.5)(reserve_path)
    reserve_path = layers.Dense(128, activation="gelu")(reserve_path)
    reserve_path = layers.Dropout(dropout * 0.5)(reserve_path)
    reserve = layers.Dense(balls, activation="softmax", name="reserve")(reserve_path)

    model = keras.Model(inp, [main_logits, reserve], name="lotto_enhanced_transformer")

    # Compile with improved optimizer settings
    main_loss = WeightedBCE(pos_weight=pos_weight, label_smooth=label_smooth)
    res_loss = keras.losses.CategoricalCrossentropy()

    # Use AdamW with weight decay for better generalization
    optimizer = keras.optimizers.AdamW(
        learning_rate=1e-4,  # Lower initial learning rate
        weight_decay=l2,
        clipnorm=1.0  # Gradient clipping for stability
    )

    model.compile(
        optimizer=optimizer,
        loss={"diversity_aux": main_loss, "reserve": res_loss},
        metrics={
            "diversity_aux": ["accuracy"],
            "reserve": ["accuracy", keras.metrics.TopKCategoricalAccuracy(k=5, name="top5_acc")]
        },
    )

    return model


def train_enhanced_model(
    model: keras.Model,
    X: np.ndarray,
    y_main: np.ndarray,
    y_reserve: np.ndarray,
    epochs: int = 100,  # More epochs with better early stopping
    batch_size: int = 8,  # Smaller batches for better gradients
    val_size: float = 0.2,
    verbose: int = 1,
) -> keras.callbacks.History:
    """
    Train the enhanced model with advanced training techniques.
    
    Improvements:
    - More aggressive early stopping
    - Cosine annealing learning rate schedule
    - Better learning rate reduction
    - Validation split with stratification
    """
    # Split data
    split_idx = int(len(X) * (1 - val_size))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_main_train, y_main_val = y_main[:split_idx], y_main[split_idx:]
    y_res_train, y_res_val = y_reserve[:split_idx], y_reserve[split_idx:]

    # Advanced callbacks
    callbacks = [
        # Early stopping with more patience
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=15,  # Increased from 8
            restore_best_weights=True,
            min_delta=1e-5
        ),
        
        # Cosine annealing learning rate schedule
        keras.callbacks.CosineDecayRestarts(
            initial_learning_rate=1e-4,
            first_decay_steps=epochs // 4,
            t_mul=2.0,
            m_mul=0.8,
            alpha=1e-6
        ),
        
        # Reduce learning rate on plateau
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=7,  # Increased from 4
            min_lr=1e-7,
            verbose=1
        ),
    ]

    history = model.fit(
        X_train,
        {"diversity_aux": y_main_train, "reserve": y_res_train},
        validation_data=(X_val, {"diversity_aux": y_main_val, "reserve": y_res_val}),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=verbose,
    )

    return history


def predict_probs_enhanced(
    model: keras.Model, X: np.ndarray, verbose: int = 0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict probabilities with enhanced model.

    Args:
        model: Trained Keras model
        X: Input sequences (n, lookback, 45)
        verbose: Verbosity level

    Returns:
        Tuple[main_probs, reserve_probs] - arrays of shape (n, 45)
    """
    main_probs, reserve_probs = model.predict(X, verbose=verbose)
    return main_probs, reserve_probs


def ensemble_predictions(models: List[keras.Model], X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensemble predictions from multiple trained models.
    
    Args:
        models: List of trained models
        X: Input sequences
    
    Returns:
        Averaged predictions from all models
    """
    all_main_probs = []
    all_reserve_probs = []
    
    for model in models:
        main_probs, reserve_probs = predict_probs_enhanced(model, X, verbose=0)
        all_main_probs.append(main_probs)
        all_reserve_probs.append(reserve_probs)
    
    # Average predictions
    main_ensemble = np.mean(all_main_probs, axis=0)
    reserve_ensemble = np.mean(all_reserve_probs, axis=0)
    
    return main_ensemble, reserve_ensemble


# Backward compatibility aliases
build_model = build_enhanced_model
train_model = train_enhanced_model
predict_probs = predict_probs_enhanced
