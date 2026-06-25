from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .embedder import Embedder
from .parser import SemanticBlock


@dataclass
class BlockMatch:
    type: str  # "modified", "moved", "added", "removed"
    score: float
    block_a: Optional[SemanticBlock] = None
    block_b: Optional[SemanticBlock] = None
    a_index: int = -1
    b_index: int = -1


@dataclass
class MatchResult:
    matches: List[BlockMatch] = field(default_factory=list)


class Matcher:
    def __init__(self, embedder: Embedder, threshold: float = 0.75) -> None:
        self.embedder = embedder
        self.threshold = threshold

    def _normalize_title(self, title: Optional[str]) -> str:
        return (title or "").strip().lower()

    def _classify_match(self, a_idx: int, b_idx: int, block_a: SemanticBlock, block_b: SemanticBlock, score: float) -> str:
        title_a = self._normalize_title(block_a.title)
        title_b = self._normalize_title(block_b.title)
        # If titles match and position is roughly same → modified
        # If titles differ or position shifted significantly → moved
        if title_a and title_b and title_a == title_b:
            return "modified"
        if abs(a_idx - b_idx) > 2:
            return "moved"
        if title_a != title_b:
            return "moved"
        return "modified"

    def match(self, blocks_a: List[SemanticBlock], blocks_b: List[SemanticBlock]) -> MatchResult:
        if not blocks_a and not blocks_b:
            return MatchResult()

        texts_a = [b.full_text for b in blocks_a]
        texts_b = [b.full_text for b in blocks_b]

        if texts_a and texts_b:
            emb_a = self.embedder.encode(texts_a)
            emb_b = self.embedder.encode(texts_b)
            sim_matrix = self.embedder.batch_similarity(emb_a, emb_b)
        else:
            sim_matrix = np.zeros((len(blocks_a), len(blocks_b)), dtype=np.float32)

        # Greedy one-to-one matching
        pairs: List[Tuple[int, int, float]] = []
        for i in range(len(blocks_a)):
            for j in range(len(blocks_b)):
                pairs.append((i, j, float(sim_matrix[i, j])))
        pairs.sort(key=lambda x: x[2], reverse=True)

        matched_a = set()
        matched_b = set()
        matches: List[BlockMatch] = []

        for i, j, score in pairs:
            if i in matched_a or j in matched_b:
                continue
            if score >= self.threshold:
                match_type = self._classify_match(i, j, blocks_a[i], blocks_b[j], score)
                matches.append(BlockMatch(
                    type=match_type,
                    score=round(score, 4),
                    block_a=blocks_a[i],
                    block_b=blocks_b[j],
                    a_index=i,
                    b_index=j,
                ))
                matched_a.add(i)
                matched_b.add(j)

        # Removed blocks from A
        for i, block in enumerate(blocks_a):
            if i not in matched_a:
                matches.append(BlockMatch(
                    type="removed",
                    score=0.0,
                    block_a=block,
                    block_b=None,
                    a_index=i,
                    b_index=-1,
                ))

        # Added blocks from B
        for j, block in enumerate(blocks_b):
            if j not in matched_b:
                matches.append(BlockMatch(
                    type="added",
                    score=0.0,
                    block_a=None,
                    block_b=block,
                    a_index=-1,
                    b_index=j,
                ))

        # Sort by original A index, then B index for readability
        matches.sort(key=lambda m: (m.a_index if m.a_index != -1 else 9999, m.b_index if m.b_index != -1 else 9999))
        return MatchResult(matches=matches)
