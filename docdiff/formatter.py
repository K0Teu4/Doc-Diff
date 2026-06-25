from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .differ import Differ, SentenceDiff
from .matcher import BlockMatch, MatchResult
from .parser import SemanticBlock


@dataclass
class FormattedChange:
    type: str
    score: float
    context: Optional[str]
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    sentence_diffs: List[Dict[str, Any]] = field(default_factory=list)
    numeric_changes: List[Dict[str, str]] = field(default_factory=list)


class Formatter:
    def __init__(self, differ: Differ) -> None:
        self.differ = differ

    def _context(self, block: Optional[SemanticBlock]) -> Optional[str]:
        return block.title if block and block.title else None

    def _build_sentence_diffs(self, old_text: str, new_text: str) -> List[Dict[str, Any]]:
        diffs = self.differ.diff_sentences(old_text, new_text)
        result = []
        for d in diffs:
            entry = {
                "type": d.type,
                "old_text": d.old_text,
                "new_text": d.new_text,
                "word_opcodes": d.word_opcodes,
                "numeric_changes": [asdict(nc) for nc in d.numeric_changes],
            }
            result.append(entry)
        return result

    def _collect_numeric_changes(self, sentence_diffs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        changes = []
        for sd in sentence_diffs:
            for nc in sd.get("numeric_changes", []):
                changes.append(nc)
        return changes

    def build_changes(self, result: MatchResult) -> List[FormattedChange]:
        changes: List[FormattedChange] = []
        for match in result.matches:
            context = self._context(match.block_a or match.block_b)
            change = FormattedChange(
                type=match.type,
                score=match.score,
                context=context,
            )
            if match.type in ("modified", "moved"):
                old_text = match.block_a.full_text if match.block_a else ""
                new_text = match.block_b.full_text if match.block_b else ""
                change.old_text = old_text
                change.new_text = new_text
                change.sentence_diffs = self._build_sentence_diffs(old_text, new_text)
                change.numeric_changes = self._collect_numeric_changes(change.sentence_diffs)
            elif match.type == "added":
                change.new_text = match.block_b.full_text if match.block_b else ""
            elif match.type == "removed":
                change.old_text = match.block_a.full_text if match.block_a else ""
            changes.append(change)
        return changes

    def format_markdown(self, result: MatchResult) -> str:
        changes = self.build_changes(result)
        lines: List[str] = ["# Semantic Document Diff\n"]
        if not changes:
            lines.append("*Нет изменений.*")
            return "\n".join(lines)

        for ch in changes:
            title = ch.context or "Без раздела"
            lines.append(f"## {title}")
            lines.append(f"**Тип:** {ch.type} | **Уверенность:** {ch.score:.2f}")
            lines.append("")

            if ch.type in ("modified", "moved"):
                if ch.numeric_changes:
                    lines.append("**Числовые изменения:**")
                    for nc in ch.numeric_changes:
                        lines.append(f"- `{nc['old_value']}` → `{nc['new_value']}`")
                    lines.append("")

                lines.append("**Было:**")
                lines.append(f"```\n{ch.old_text or ''}\n```")
                lines.append("**Стало:**")
                lines.append(f"```\n{ch.new_text or ''}\n```")

                if ch.sentence_diffs:
                    lines.append("**Детализация по предложениям:**")
                    for sd in ch.sentence_diffs:
                        if sd["type"] == "equal":
                            lines.append(f"  {sd['old_text']}")
                        elif sd["type"] == "delete":
                            lines.append(f"  ~~{sd['old_text']}~~")
                        elif sd["type"] == "insert":
                            lines.append(f"  **{sd['new_text']}**")
                        elif sd["type"] == "replace":
                            lines.append(f"  ~~{sd['old_text']}~~ → **{sd['new_text']}**")
                            for nc in sd.get("numeric_changes", []):
                                lines.append(f"    Число: `{nc['old_value']}` → `{nc['new_value']}`")
                    lines.append("")

            elif ch.type == "added":
                lines.append(f"**Добавлено:**")
                lines.append(f"```\n{ch.new_text or ''}\n```")
                lines.append("")
            elif ch.type == "removed":
                lines.append(f"**Удалено:**")
                lines.append(f"```\n{ch.old_text or ''}\n```")
                lines.append("")

        return "\n".join(lines)

    def format_json(self, result: MatchResult) -> dict:
        changes = self.build_changes(result)
        return {
            "changes": [asdict(ch) for ch in changes],
            "summary": {
                "modified": sum(1 for c in changes if c.type == "modified"),
                "moved": sum(1 for c in changes if c.type == "moved"),
                "added": sum(1 for c in changes if c.type == "added"),
                "removed": sum(1 for c in changes if c.type == "removed"),
            },
        }

    def to_json_string(self, result: MatchResult) -> str:
        return json.dumps(self.format_json(result), ensure_ascii=False, indent=2)
