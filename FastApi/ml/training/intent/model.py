"""Joint intent + slot model: one BiLSTM encoder, two heads that output raw logits."""

from __future__ import annotations

import keras
from keras import layers


def build_joint_model(
    vocab_size: int,
    num_intents: int,
    num_slots: int,
    max_len: int = 32,
    dim: int = 128,
    dropout: float = 0.2,
) -> keras.Model:
    """Heads stay linear (logits) so temperature scaling can calibrate them later.

    Padding (id 0) is masked: the pooled intent vector ignores padded positions.
    """
    tokens = keras.Input(shape=(max_len,), dtype="int32", name="tokens")
    x = layers.Embedding(vocab_size, dim, mask_zero=True)(tokens)
    x = layers.Bidirectional(layers.LSTM(dim, return_sequences=True, dropout=dropout))(x)
    pooled = layers.GlobalAveragePooling1D()(x)
    intent = layers.Dense(num_intents, name="intent", dtype="float32")(pooled)
    slots = layers.Dense(num_slots, name="slots", dtype="float32")(x)
    return keras.Model(tokens, {"intent": intent, "slots": slots}, name="joint_intent_slots")
