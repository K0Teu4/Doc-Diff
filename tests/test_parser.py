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
