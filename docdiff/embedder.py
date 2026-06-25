from __future__ import annotations

import math
from typing import List, Union

import numpy as np


class Embedder:
    """Lazy-loading sentence-transformers embedder."""

    DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device or "cpu"
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        model = self._load()
        if isinstance(texts, str):
            texts = [texts]
        return model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two 1-D vectors."""
        a = np.asarray(a, dtype=np.float32)
        b = np.asarray(b, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def batch_similarity(self, embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> np.ndarray:
        """Compute pairwise cosine similarity matrix."""
        a = np.asarray(embeddings_a, dtype=np.float32)
        b = np.asarray(embeddings_b, dtype=np.float32)
        # Normalize
        a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
        b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
        return np.dot(a_norm, b_norm.T)
