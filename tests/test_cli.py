import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from docdiff.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_markdown(capsys):
    argv = [str(FIXTURES / "old_contract.docx"), str(FIXTURES / "new_contract.docx"), "--format", "markdown"]
    with patch.object(sys, "argv", ["docdiff"] + argv):
        # We need to mock embedder to avoid heavy model load in tests
        with patch("docdiff.cli.Embedder") as MockEmbedder:
            import numpy as np

            class FakeEmbedder:
                def __init__(self, *a, **k):
                    pass
                def encode(self, texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    embeddings = []
                    for text in texts:
                        vec = np.zeros(128, dtype=np.float32)
                        for i, ch in enumerate(text):
                            vec[i % 128] += ord(ch)
                        norm = np.linalg.norm(vec)
                        if norm > 0:
                            vec = vec / norm
                        embeddings.append(vec)
                    return np.array(embeddings)
                def batch_similarity(self, a, b):
                    a = np.asarray(a, dtype=np.float32)
                    b = np.asarray(b, dtype=np.float32)
                    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
                    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
                    return np.dot(a_norm, b_norm.T)

            MockEmbedder.return_value = FakeEmbedder()
            rc = main()
    assert rc == 0
    captured = capsys.readouterr()
    assert "Semantic Document Diff" in captured.out or "Parsing documents" in captured.err


def test_cli_html(capsys):
    argv = [str(FIXTURES / "old_contract.docx"), str(FIXTURES / "new_contract.docx"), "--format", "html"]
    with patch.object(sys, "argv", ["docdiff"] + argv):
        with patch("docdiff.cli.Embedder") as MockEmbedder:
            import numpy as np

            class FakeEmbedder:
                def __init__(self, *a, **k):
                    pass
                def encode(self, texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    embeddings = []
                    for text in texts:
                        vec = np.zeros(128, dtype=np.float32)
                        for i, ch in enumerate(text):
                            vec[i % 128] += ord(ch)
                        norm = np.linalg.norm(vec)
                        if norm > 0:
                            vec = vec / norm
                        embeddings.append(vec)
                    return np.array(embeddings)
                def batch_similarity(self, a, b):
                    a = np.asarray(a, dtype=np.float32)
                    b = np.asarray(b, dtype=np.float32)
                    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
                    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
                    return np.dot(a_norm, b_norm.T)

            MockEmbedder.return_value = FakeEmbedder()
            rc = main()
    assert rc == 0
    captured = capsys.readouterr()
    # HTML output goes to file by default, not stdout
    assert "Report saved to" in captured.err or "Parsing documents" in captured.err


def test_cli_json(capsys):
    argv = [str(FIXTURES / "old_contract.docx"), str(FIXTURES / "new_contract.docx"), "--format", "json"]
    with patch.object(sys, "argv", ["docdiff"] + argv):
        with patch("docdiff.cli.Embedder") as MockEmbedder:
            import numpy as np

            class FakeEmbedder:
                def __init__(self, *a, **k):
                    pass
                def encode(self, texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    embeddings = []
                    for text in texts:
                        vec = np.zeros(128, dtype=np.float32)
                        for i, ch in enumerate(text):
                            vec[i % 128] += ord(ch)
                        norm = np.linalg.norm(vec)
                        if norm > 0:
                            vec = vec / norm
                        embeddings.append(vec)
                    return np.array(embeddings)
                def batch_similarity(self, a, b):
                    a = np.asarray(a, dtype=np.float32)
                    b = np.asarray(b, dtype=np.float32)
                    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-10)
                    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
                    return np.dot(a_norm, b_norm.T)

            MockEmbedder.return_value = FakeEmbedder()
            rc = main()
    assert rc == 0
    captured = capsys.readouterr()
    assert '"changes"' in captured.out or '"summary"' in captured.out


