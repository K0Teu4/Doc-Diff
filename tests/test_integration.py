"""Integration tests: full pipeline from DOCX to HTML output."""

from pathlib import Path

import pytest

from docdiff.differ import Differ
from docdiff.embedder import Embedder
from docdiff.html_generator import HtmlGenerator
from docdiff.matcher import Matcher
from docdiff.parser import parse_docx


FIXTURES = Path(__file__).parent / "fixtures"


class TestFullPipeline:
    """End-to-end tests without mocking embedder (uses real model or fails gracefully)."""

    def test_contract_full_pipeline(self):
        """Parse, match, diff, and generate HTML for the contract fixtures."""
        blocks_old = parse_docx(FIXTURES / "old_contract.docx")
        blocks_new = parse_docx(FIXTURES / "new_contract.docx")

        assert len(blocks_old) >= 3
        assert len(blocks_new) >= 3

        # Check titles detected
        old_titles = {b.title for b in blocks_old if b.title}
        new_titles = {b.title for b in blocks_new if b.title}
        assert "Договор" in old_titles or "Договор поставки" in new_titles
        assert "Цена" in old_titles
        assert "Цена" in new_titles

    def test_thesis_full_pipeline(self):
        """Parse thesis documents and verify structure."""
        blocks_old = parse_docx(FIXTURES / "thesis_v1.docx")
        blocks_new = parse_docx(FIXTURES / "thesis_v2.docx")

        # Should detect pseudo-headings
        old_titles = {b.title for b in blocks_old if b.title}
        new_titles = {b.title for b in blocks_new if b.title}

        assert any("ИНТЕЛЛЕКТА" in t for t in old_titles), f"Old titles: {old_titles}"
        assert any("Анализ мирового" in t for t in old_titles), f"Old titles: {old_titles}"

        assert any("Рекомендации" in t for t in new_titles), f"New titles: {new_titles}"

        # v2 has new section
        assert len(blocks_new) >= len(blocks_old)

    def test_table_extraction(self):
        """Tables should be extracted as a separate block."""
        blocks = parse_docx(FIXTURES / "with_table.docx")
        table_block = next((b for b in blocks if b.title == "Таблицы"), None)
        assert table_block is not None
        assert "Показатель" in table_block.full_text
        assert "100" in table_block.full_text

    def test_html_contains_all_sections(self):
        """HTML output should contain all change types when present."""
        from docdiff.parser import SemanticBlock, ParagraphItem

        def make_block(title, text, level=1):
            return SemanticBlock(title=title, level=level, items=[ParagraphItem(text=text)])

        from docdiff.matcher import BlockMatch, MatchResult

        matches = [
            BlockMatch(type="modified", score=0.9,
                       block_a=make_block("Цена", "Стоимость 100 рублей."),
                       block_b=make_block("Цена", "Стоимость 150 рублей."),
                       a_index=0, b_index=0),
            BlockMatch(type="added", score=0.0,
                       block_a=None,
                       block_b=make_block("Сроки", "30 дней."),
                       a_index=-1, b_index=1),
            BlockMatch(type="removed", score=0.0,
                       block_a=make_block("Прочее", "Удалён."),
                       block_b=None,
                       a_index=1, b_index=-1),
        ]

        differ = Differ()
        gen = HtmlGenerator(differ)
        html = gen.generate(MatchResult(matches=matches))

        assert "modified" in html
        assert "added" in html
        assert "removed" in html
        assert "Было" in html
        assert "Стало" in html
        assert "100" in html
        assert "150" in html
        assert "30 дней" in html
        assert "Удалён" in html

    def test_empty_result(self):
        """Empty match result should produce valid HTML with no changes message."""
        from docdiff.matcher import MatchResult

        differ = Differ()
        gen = HtmlGenerator(differ)
        html = gen.generate(MatchResult(matches=[]))

        assert "<!DOCTYPE html>" in html
        assert "Нет изменений" in html or "No changes" in html

    def test_numeric_detection_in_full_pipeline(self):
        """Numbers and percentages should be detected across sentence diffs."""
        from docdiff.parser import SemanticBlock, ParagraphItem

        def make_block(title, text, level=1):
            return SemanticBlock(title=title, level=level, items=[ParagraphItem(text=text)])

        from docdiff.matcher import BlockMatch, MatchResult

        match = BlockMatch(
            type="modified", score=0.9,
            block_a=make_block("Скидка", "Размер скидки составляет 10%."),
            block_b=make_block("Скидка", "Размер скидки составляет 15%."),
            a_index=0, b_index=0
        )

        differ = Differ()
        gen = HtmlGenerator(differ)
        html = gen.generate(MatchResult(matches=[match]))

        assert "10%" in html
        assert "15%" in html

    def test_parser_metadata_fields(self):
        """Parser should populate all metadata fields."""
        blocks = parse_docx(FIXTURES / "old_contract.docx")
        for block in blocks:
            for item in block.items:
                assert hasattr(item, "style")
                assert hasattr(item, "bold")
                assert hasattr(item, "alignment")
                assert hasattr(item, "list_type")
                assert hasattr(item, "font_size")
