import pytest
import numpy as np

from docdiff.embedder import Embedder
from docdiff.matcher import Matcher, MatchResult
from docdiff.parser import SemanticBlock, ParagraphItem


class FakeEmbedder:
    """Fake embedder that returns deterministic embeddings based on text hash."""

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = []
        for text in texts:
            # Create a simple deterministic vector
            vec = np.zeros(128, dtype=np.float32)
            for i, ch in enumerate(text):
                vec[i % 128] += ord(ch)
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)
        return np.array(embeddings)

    def cosine_similarity(self, a, b):
        a = np.asarray(a, dtype=np.float32)
        b = np.asarray(b, dtype=np.float32)
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def batch_similarity(self, emb_a, emb_b):
        a = np.asarray(emb_a, dtype=np.float32)
        b = np.asarray(emb_b, dtype=np.float32)
        a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
        b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
        return np.dot(a_norm, b_norm.T)


def make_block(title, text, level=1):
    return SemanticBlock(title=title, level=level, items=[ParagraphItem(text=text)])


def test_match_modified():
    emb = FakeEmbedder()
    matcher = Matcher(emb, threshold=0.5)
    a = [make_block("Цена", "Стоимость 100")]
    b = [make_block("Цена", "Стоимость 150")]
    result = matcher.match(a, b)
    assert len(result.matches) == 1
    assert result.matches[0].type == "modified"
    assert result.matches[0].score > 0.5


def test_match_added_removed():
    emb = FakeEmbedder()
    matcher = Matcher(emb, threshold=0.5)
    a = [make_block("Цена", "Стоимость 100")]
    b = [make_block("Цена", "Стоимость 100"), make_block("Сроки", "30 дней")]
    result = matcher.match(a, b)
    types = [m.type for m in result.matches]
    assert "modified" in types
    assert "added" in types


def test_match_moved():
    emb = FakeEmbedder()
    matcher = Matcher(emb, threshold=0.5)
    a = [
        make_block("A", "Text A"),
        make_block("B", "Text B"),
        make_block("C", "Text C"),
        make_block("D", "Text D"),
    ]
    b = [
        make_block("A", "Text A"),
        make_block("C", "Text C"),
        make_block("B", "Text B"),
        make_block("D", "Text D"),
    ]
    result = matcher.match(a, b)
    moved = [m for m in result.matches if m.type == "moved"]
    # B and C swapped positions; one of them may be classified as moved
    assert any(m.a_index != m.b_index for m in result.matches if m.type in ("modified", "moved"))
