from docdiff.differ import Differ, SentenceSplitter


def test_split_sentences():
    text = "Первое предложение. Второе предложение! Третье?"
    sents = SentenceSplitter.split(text)
    assert len(sents) == 3
    assert sents[0] == "Первое предложение."
    assert sents[1] == "Второе предложение!"
    assert sents[2] == "Третье?"


def test_diff_equal():
    d = Differ()
    result = d.diff_sentences("Hello world.", "Hello world.")
    assert len(result) == 1
    assert result[0].type == "equal"


def test_diff_insert():
    d = Differ()
    result = d.diff_sentences("Hello.", "Hello. New sentence.")
    types = [r.type for r in result]
    assert "equal" in types
    assert "insert" in types


def test_diff_numeric_changes():
    d = Differ()
    result = d.diff_sentences(
        "Стоимость составляет 100 000 рублей.",
        "Стоимость составляет 150 000 рублей."
    )
    replace = [r for r in result if r.type == "replace"]
    assert len(replace) >= 1
    nums = replace[0].numeric_changes
    assert any("100" in nc.old_value and "150" in nc.new_value for nc in nums)


def test_diff_percentage():
    d = Differ()
    result = d.diff_sentences(
        "Размер скидки 10%.",
        "Размер скидки 15%."
    )
    replace = [r for r in result if r.type == "replace"]
    assert len(replace) >= 1
    nums = replace[0].numeric_changes
    assert any(nc.old_value == "10%" and nc.new_value == "15%" for nc in nums)
