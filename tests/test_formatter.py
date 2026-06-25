import json
import pytest

from docdiff.differ import Differ
from docdiff.formatter import Formatter
from docdiff.matcher import BlockMatch, MatchResult
from docdiff.parser import SemanticBlock, ParagraphItem


def make_block(title, text, level=1):
    return SemanticBlock(title=title, level=level, items=[ParagraphItem(text=text)])


def test_markdown_output():
    differ = Differ()
    formatter = Formatter(differ)
    match = BlockMatch(
        type="modified",
        score=0.95,
        block_a=make_block("Цена", "Стоимость 100 рублей."),
        block_b=make_block("Цена", "Стоимость 150 рублей."),
        a_index=0,
        b_index=0,
    )
    result = MatchResult(matches=[match])
    md = formatter.format_markdown(result)
    assert "Semantic Document Diff" in md
    assert "Цена" in md
    assert "modified" in md
    assert "100" in md
    assert "150" in md


def test_json_output():
    differ = Differ()
    formatter = Formatter(differ)
    match = BlockMatch(
        type="added",
        score=0.0,
        block_a=None,
        block_b=make_block("Сроки", "30 дней."),
        a_index=-1,
        b_index=1,
    )
    result = MatchResult(matches=[match])
    data = formatter.format_json(result)
    assert data["summary"]["added"] == 1
    assert any(ch["type"] == "added" for ch in data["changes"])


def test_numeric_changes_in_markdown():
    differ = Differ()
    formatter = Formatter(differ)
    match = BlockMatch(
        type="modified",
        score=0.9,
        block_a=make_block("Цена", "Стоимость 100 000 рублей."),
        block_b=make_block("Цена", "Стоимость 150 000 рублей."),
        a_index=0,
        b_index=0,
    )
    result = MatchResult(matches=[match])
    md = formatter.format_markdown(result)
    assert "100 000" in md
    assert "150 000" in md
