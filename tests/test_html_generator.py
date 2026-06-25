from pathlib import Path

import pytest

from docdiff.differ import Differ
from docdiff.html_generator import HtmlGenerator
from docdiff.matcher import BlockMatch, MatchResult
from docdiff.parser import SemanticBlock, ParagraphItem


def make_block(title, text, level=1):
    return SemanticBlock(title=title, level=level, items=[ParagraphItem(text=text)])


def test_html_modified():
    d = Differ()
    gen = HtmlGenerator(d)
    match = BlockMatch(
        type="modified", score=0.95,
        block_a=make_block("Цена", "Стоимость 100 рублей."),
        block_b=make_block("Цена", "Стоимость 150 рублей."),
        a_index=0, b_index=0
    )
    html = gen.generate(MatchResult(matches=[match]))
    assert "<!DOCTYPE html>" in html
    assert "DocDiff" in html
    assert "Цена" in html
    assert "modified" in html
    assert "100" in html
    assert "150" in html
    assert "Было" in html
    assert "Стало" in html
    assert "block-" in html  # anchor links
    assert "toc-item" in html  # sidebar navigation


def test_html_added_removed():
    d = Differ()
    gen = HtmlGenerator(d)
    matches = [
        BlockMatch(
            type="added", score=0.0,
            block_a=None,
            block_b=make_block("Сроки", "30 дней."),
            a_index=-1, b_index=0
        ),
        BlockMatch(
            type="removed", score=0.0,
            block_a=make_block("Прочее", "Удалённый текст."),
            block_b=None,
            a_index=0, b_index=-1
        ),
    ]
    html = gen.generate(MatchResult(matches=matches))
    assert "added" in html
    assert "removed" in html
    assert "30 дней" in html
    assert "Удалённый текст" in html


def test_html_stats():
    d = Differ()
    gen = HtmlGenerator(d)
    matches = [
        BlockMatch(type="modified", score=0.9, block_a=make_block("A", "a"), block_b=make_block("A", "b"), a_index=0, b_index=0),
        BlockMatch(type="added", score=0.0, block_a=None, block_b=make_block("B", "b"), a_index=-1, b_index=1),
        BlockMatch(type="removed", score=0.0, block_a=make_block("C", "c"), block_b=None, a_index=1, b_index=-1),
    ]
    html = gen.generate(MatchResult(matches=matches))
    assert "Modified" in html
    assert "Added" in html
    assert "Removed" in html
    assert "stat-card" in html
    assert "stat-value" in html


def test_html_no_changes():
    d = Differ()
    gen = HtmlGenerator(d)
    html = gen.generate(MatchResult(matches=[]))
    assert "Нет изменений" in html or "No changes" in html or "Нет изменений" in html
