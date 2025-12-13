#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Model: Transformer-based deep network for lottery prediction.
- Inputs: one-hot sequence of historical draws
- Outputs: probabilities for 6 main numbers + 1 reserve
"""

import os
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import numpy as np
import tensorflow as tf
import keras
from keras import layers
import keras.ops as ops

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


def transformer_encoder_block(x, d_model: int, n_heads: int, dropout: float, ff_mult: int = 4):
    """Single transformer encoder block: attention + feed-forward."""
    # Layer norm + multi-head attention
    y = layers.LayerNormalization()(x)
    y = layers.MultiHeadAttention(n_heads, key_dim=d_model // n_heads, dropout=dropout)(y, y)
    x = layers.Add()([x, layers.Dropout(dropout)(y)])

    # Layer norm + feed-forward
    y = layers.LayerNormalization()(x)
    y = layers.Dense(d_model * ff_mult, activation="relu")(y)
    y = layers.Dropout(dropout)(y)
    y = layers.Dense(d_model)(y)

    return layers.Add()([x, layers.Dropout(dropout)(y)])


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
        s = ops.sum(y_pred_main, axis=-1)  # Sum across balls
        loss = ops.mean(ops.square(s - 6.0))
        self.add_loss(self.weight * loss)
        return y_pred_main


def build_model(
    lookback: int = 20,
    balls: int = BALLS,
    d_model: int = 128,
    n_heads: int = 4,
    dropout: float = 0.25,
    l2: float = 1e-5,
    pos_weight: float = 12.0,
    lambda_sum6: float = 0.02,
    label_smooth: float = 0.02,
) -> keras.Model:
    """
    Build transformer-based lottery prediction model.

    Args:
        lookback: Historical window size
        balls: Number of balls (45)
        d_model: Embedding dimension
        n_heads: Number of attention heads
        dropout: Dropout rate
        l2: L2 regularization weight
        pos_weight: Weight for positive class in BCE (accounting for class imbalance)
        lambda_sum6: Weight for sum-6 auxiliary loss
        label_smooth: Label smoothing for main output

    Returns:
        Compiled Keras Model
    """
    inp = keras.Input(shape=(lookback, balls), name="seq")

    # Conv + positional encoding
    x = layers.Conv1D(
        96, 3, padding="causal", activation="relu", dilation_rate=1,
        kernel_regularizer=keras.regularizers.l2(l2)
    )(inp)
    x = layers.Conv1D(
        96, 3, padding="causal", activation="relu", dilation_rate=2,
        kernel_regularizer=keras.regularizers.l2(l2)
    )(x)
    x = layers.Conv1D(
        128, 3, padding="causal", activation="relu", dilation_rate=4,
        kernel_regularizer=keras.regularizers.l2(l2)
    )(x)

    # Dense projection + positional encoding
    x = layers.Dense(d_model)(x)
    x = AddPositionalEncoding(max_len=lookback, d_model=d_model)(x)

    # Transformer blocks
    for _ in range(2):
        x = transformer_encoder_block(x, d_model, n_heads, dropout, ff_mult=4)

    # Global pooling + dense
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(256, activation="relu", kernel_regularizer=keras.regularizers.l2(l2))(x)
    x = layers.Dropout(dropout)(x)

    # Output heads
    main_logits = layers.Dense(balls, activation="sigmoid", name="main_logits")(x)
    main_logits = Sum6Regularizer(weight=lambda_sum6, name="sum6_aux")(main_logits)
    reserve = layers.Dense(balls, activation="softmax", name="reserve")(x)

    model = keras.Model(inp, [main_logits, reserve], name="lotto_transformer")

    # Compile
    main_loss = WeightedBCE(pos_weight=pos_weight, label_smooth=label_smooth)
    res_loss = keras.losses.CategoricalCrossentropy()

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=2e-4),
        loss={"sum6_aux": main_loss, "reserve": res_loss},
        metrics={"reserve": ["accuracy"]},
    )

    return model


def train_model(
    model: keras.Model,
    X_train: np.ndarray,
    y_main_train: np.ndarray,
    y_res_train: np.ndarray,
    X_val: np.ndarray,
    y_main_val: np.ndarray,
    y_res_val: np.ndarray,
    epochs: int = 40,
    batch_size: int = 64,
    verbose: int = 1,
) -> keras.callbacks.History:
    """Train the model."""
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4),
    ]

    history = model.fit(
        X_train,
        {"sum6_aux": y_main_train, "reserve": y_res_train},
        validation_data=(X_val, {"sum6_aux": y_main_val, "reserve": y_res_val}),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=verbose,
    )

    return history


def predict_probs(
    model: keras.Model, X: np.ndarray, verbose: int = 0
) -> tuple:
    """
    Predict probabilities for main and reserve numbers.

    Args:
        model: Trained Keras model
        X: Input sequences (n, lookback, 45)
        verbose: Verbosity level

    Returns:
        Tuple[main_probs, reserve_probs] - arrays of shape (n, 45)
    """
    main_probs, reserve_probs = model.predict(X, verbose=verbose)
    return main_probs, reserve_probs
