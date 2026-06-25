import pytest
from pathlib import Path

from docdiff.parser import parse_docx, SemanticBlock, ParagraphItem


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_old_contract():
    blocks = parse_docx(FIXTURES / "old_contract.docx")
    titles = [b.title for b in blocks]
    assert "Договор" in titles
    assert "Цена" in titles
    assert "Ответственность" in titles
    assert "Прочие условия" in titles

    price_block = next(b for b in blocks if b.title == "Цена")
    assert "100 000" in price_block.full_text


def test_parse_new_contract():
    blocks = parse_docx(FIXTURES / "new_contract.docx")
    titles = [b.title for b in blocks]
    assert "Договор поставки" in titles
    assert "Сроки поставки" in titles
    assert "Прочие условия" not in titles

    price_block = next(b for b in blocks if b.title == "Цена")
    assert "150 000" in price_block.full_text


def test_metadata_preserved():
    blocks = parse_docx(FIXTURES / "old_contract.docx")
    for block in blocks:
        for item in block.items:
            assert isinstance(item, ParagraphItem)
            assert item.style is not None or item.text == ""


# ========== Edge cases: pseudo-headings, tables, thesis ==========

def test_thesis_v1_pseudo_headings_detected():
    """Document without Heading styles should still detect bold large text as headings."""
    blocks = parse_docx(FIXTURES / "thesis_v1.docx")
    titles = [b.title for b in blocks if b.title]
    assert any("ВЛИЯНИЕ ИСКУССТВЕННОГО ИНТЕЛЛЕКТА" in t for t in titles), f"Titles: {titles}"
    assert any("Анализ мирового опыта" in t for t in titles), f"Titles: {titles}"
    assert any("Прогнозы на 2030 год" in t for t in titles), f"Titles: {titles}"
    assert any("Заключение" in t for t in titles), f"Titles: {titles}"


def test_thesis_v2_detects_changes():
    blocks = parse_docx(FIXTURES / "thesis_v2.docx")
    titles = [b.title for b in blocks if b.title]
    assert any("Рекомендации для студентов" in t for t in titles), f"Titles: {titles}"
    full_text = "\n".join(b.full_text for b in blocks)
    assert "92 млн" in full_text
    assert "105 млн" in full_text


def test_table_extraction():
    blocks = parse_docx(FIXTURES / "with_table.docx")
    table_block = next((b for b in blocks if b.title == "Таблицы"), None)
    assert table_block is not None, f"Blocks: {[b.title for b in blocks]}"
    assert "Показатель" in table_block.full_text
    assert "2023" in table_block.full_text
    assert "2024" in table_block.full_text
    assert "100" in table_block.full_text
    assert "150" in table_block.full_text


def test_thesis_semantic_blocks_structure():
    """Ensure the thesis has meaningful blocks, not just one giant block."""
    blocks = parse_docx(FIXTURES / "thesis_v1.docx")
    assert len(blocks) >= 4, f"Expected >=4 blocks, got {len(blocks)}: {[b.title for b in blocks]}"
