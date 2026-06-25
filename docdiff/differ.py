from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class NumericChange:
    old_value: str
    new_value: str


@dataclass
class SentenceDiff:
    type: str  # "equal", "insert", "delete", "replace"
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    word_opcodes: List[Tuple[str, str, str]] = field(default_factory=list)
    numeric_changes: List[NumericChange] = field(default_factory=list)


class SentenceSplitter:
    """Simple sentence splitter using regex."""

    _SENTENCE_RE = re.compile(r'(?<=[.!?])\s+')

    @classmethod
    def split(cls, text: str) -> List[str]:
        if not text:
            return []
        sentences = [s.strip() for s in cls._SENTENCE_RE.split(text) if s.strip()]
        return sentences


class Differ:
    NUM_PATTERN = re.compile(r'\d+(?:[.,]\d+)?(?:\s*%)?')

    def _extract_numbers(self, text: str) -> List[str]:
        return self.NUM_PATTERN.findall(text)

    def _find_numeric_changes(self, old_text: str, new_text: str) -> List[NumericChange]:
        old_nums = self._extract_numbers(old_text)
        new_nums = self._extract_numbers(new_text)
        changes = []
        # Pair naively by position; if lengths differ, iterate over min length
        for o, n in zip(old_nums, new_nums):
            if o != n:
                changes.append(NumericChange(old_value=o, new_value=n))
        return changes

    def _word_level_diff(self, old_text: str, new_text: str) -> List[Tuple[str, str, str]]:
        """Return word-level opcodes: (tag, old_fragment, new_fragment)."""
        old_words = old_text.split()
        new_words = new_text.split()
        sm = difflib.SequenceMatcher(None, old_words, new_words)
        opcodes = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            old_frag = " ".join(old_words[i1:i2])
            new_frag = " ".join(new_words[j1:j2])
            opcodes.append((tag, old_frag, new_frag))
        return opcodes

    def diff_sentences(self, old_text: str, new_text: str) -> List[SentenceDiff]:
        old_sents = SentenceSplitter.split(old_text)
        new_sents = SentenceSplitter.split(new_text)

        sm = difflib.SequenceMatcher(None, old_sents, new_sents)
        results: List[SentenceDiff] = []

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for s in old_sents[i1:i2]:
                    results.append(SentenceDiff(type="equal", old_text=s, new_text=s))
            elif tag == "delete":
                for s in old_sents[i1:i2]:
                    results.append(SentenceDiff(type="delete", old_text=s, new_text=None))
            elif tag == "insert":
                for s in new_sents[j1:j2]:
                    results.append(SentenceDiff(type="insert", old_text=None, new_text=s))
            elif tag == "replace":
                # Pair up as many as possible; if lengths differ, remainder is insert/delete
                old_slice = old_sents[i1:i2]
                new_slice = new_sents[j1:j2]
                max_len = max(len(old_slice), len(new_slice))
                for k in range(max_len):
                    o = old_slice[k] if k < len(old_slice) else None
                    n = new_slice[k] if k < len(new_slice) else None
                    if o and n:
                        word_diff = self._word_level_diff(o, n)
                        num_changes = self._find_numeric_changes(o, n)
                        results.append(SentenceDiff(
                            type="replace",
                            old_text=o,
                            new_text=n,
                            word_opcodes=word_diff,
                            numeric_changes=num_changes,
                        ))
                    elif o:
                        results.append(SentenceDiff(type="delete", old_text=o, new_text=None))
                    elif n:
                        results.append(SentenceDiff(type="insert", old_text=None, new_text=n))
        return results
