"""Serving-time tokenizer. MUST match ml/training/common/markup.py (a parity test enforces it)."""

import re

_TOKEN = re.compile(r"\.?[\w@+#]+(?:[.\-/][\w@+#]+)*")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())
