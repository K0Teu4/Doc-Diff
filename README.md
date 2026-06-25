# Semantic Document Diff (docdiff)

CLI-инструмент для семантического сравнения документов Microsoft Word (.docx). Вместо построчного сравнения, `docdiff` работает на уровне абзацев и предложений, используя векторные эмбеддинги для нахождения соответствий между разделами.

## Возможности

- **Семантическое сравнение** — находит похожие разделы даже при изменении формулировок
- **Детальный diff** — внутри изменённых блоков показывает diff на уровне предложений
- **Детекция числовых изменений** — автоматически выделяет изменения в цифрах и процентах
- **Детекция перемещений** — находит разделы, которые переместились в документе
- **Markdown и JSON** — два формата вывода
- **Полностью локально** — работает без внешних API, используется `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## Установка

```bash
git clone <repo>
cd docdiff
pip install -r requirements.txt
```

## Использование

### Markdown (по умолчанию)

```bash
docdiff old_contract.docx new_contract.docx
```

### JSON

```bash
docdiff old_contract.docx new_contract.docx --format json
```

### Настройка порога сходства

```bash
docdiff old_contract.docx new_contract.docx --threshold 0.8
```

### Указание устройства (CPU/CUDA)

```bash
docdiff old_contract.docx new_contract.docx --device cuda
```

## Пример вывода (Markdown)

```markdown
# Semantic Document Diff

## Цена
**Тип:** modified | **Уверенность:** 0.95

**Числовые изменения:**
- `100` → `150`

**Было:**
```
Стоимость товара составляет 100 000 рублей.
```
**Стало:**
```
Стоимость товара составляет 150 000 рублей.
```

**Детализация по предложениям:**
  Стоимость товара составляет ~~100 000~~ → **150 000** рублей.
```

## Архитектура

```
docdiff/
├── docdiff/
│   ├── __init__.py
│   ├── parser.py       # DOCX → структура (SemanticBlock)
│   ├── embedder.py     # sentence-transformers (MiniLM)
│   ├── matcher.py      # косинусное сравнение + greedy matching
│   ├── differ.py       # детальный diff на уровне предложений
│   ├── formatter.py    # markdown/json вывод
│   └── cli.py          # argparse
├── tests/
│   ├── fixtures/
│   │   ├── old_contract.docx
│   │   └── new_contract.docx
│   ├── test_parser.py
│   ├── test_differ.py
│   ├── test_matcher.py
│   ├── test_formatter.py
│   └── test_cli.py
├── requirements.txt
└── README.md
```

## Запуск тестов

```bash
pytest tests/ -v
```

## Зависимости

- Python 3.10+
- `python-docx`
- `sentence-transformers`
- `scikit-learn`
- `numpy`
- `torch`
- `pytest` (для разработки)

## Критерии готовности

- [x] pytest проходит на тестовых фикстурах
- [x] Работает на реальном договоре (50+ страниц) — зависит от производительности CPU
- [x] README с примером использования
