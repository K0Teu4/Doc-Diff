# Semantic Document Diff (docdiff)

Инструмент для семантического сравнения документов Microsoft Word (.docx). Вместо построчного сравнения, `docdiff` работает на уровне абзацев и предложений, используя векторные эмбеддинги для нахождения соответствий между разделами.

**Доступно как:** CLI, веб-приложение, и графическое приложение (desktop).

## Возможности

- **Семантическое сравнение** — находит похожие разделы даже при изменении формулировок
- **Детальный diff** — внутри изменённых блоков показывает diff на уровне предложений
- **Детекция числовых изменений** — автоматически выделяет изменения в цифрах и процентах
- **Детекция перемещений** — находит разделы, которые переместились в документе
- **HTML-отчёт** — красивый side-by-side diff в браузере с подсветкой изменений
- **Markdown и JSON** — два формата вывода в терминал
- **Полностью локально** — работает без внешних API, используется `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## Установка

```bash
git clone <repo>
cd docdiff
pip install -r requirements.txt
pip install -e .          # editable install для entry points
```

## Использование

### 🖥️ Графическое приложение (рекомендуется)

Простой интерфейс в браузере — drag-and-drop, прогресс-бар, настройки:

```bash
# Если установлено через pip
docdiff-gui

# Или напрямую из папки проекта (без установки)
python -m docdiff.desktop.launcher
```

Откроется окно браузера с интерфейсом. Перетащите два файла `.docx`, нажмите **Сравнить** — результат откроется в новой вкладке.

### 🌐 Веб-сервер

Запустить как локальный веб-сервер (FastAPI):

```bash
# Если установлено через pip
docdiff-web

# Или напрямую из папки проекта
python -m docdiff.webapp.app
```

Откройте `http://localhost:8765` в браузере.

### 📟 CLI

Для автоматизации и скриптов:

```bash
# Markdown (по умолчанию)
docdiff old_contract.docx new_contract.docx

# Или напрямую из папки проекта
python -m docdiff.cli old_contract.docx new_contract.docx

# JSON
docdiff old_contract.docx new_contract.docx --format json

# HTML-отчёт
docdiff old_contract.docx new_contract.docx --format html -o report.html

# Настройка порога
docdiff old_contract.docx new_contract.docx --threshold 0.8

# Указание устройства (CPU/CUDA)
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

## Пример вывода (HTML)

HTML-отчёт открывается в браузере и содержит:
- Сводку изменений (Modified / Added / Removed / Moved)
- Side-by-side сравнение для изменённых блоков
- Подсветку удалённого (зачёркивание) и добавленного (жирный зелёный) текста
- Выделение числовых изменений цветом

```bash
docdiff old_contract.docx new_contract.docx --format html -o report.html
# затем откройте report.html в браузере
```

## Архитектура

```
docdiff/
├── docdiff/
│   ├── __init__.py
│   ├── parser.py          # DOCX → структура (SemanticBlock)
│   ├── embedder.py        # sentence-transformers (MiniLM)
│   ├── matcher.py         # косинусное сравнение + greedy matching
│   ├── differ.py          # детальный diff на уровне предложений
│   ├── formatter.py       # markdown/json вывод
│   ├── html_generator.py  # HTML-отчёт
│   ├── cli.py             # argparse + точка входа
│   ├── webapp/
│   │   ├── app.py         # FastAPI + drag-and-drop UI
│   │   ├── static/
│   │   └── templates/
│   │       └── index.html
│   └── desktop/
│       └── launcher.py    # Запускает веб-сервер + браузер
├── tests/
│   ├── fixtures/
│   │   ├── old_contract.docx
│   │   ├── new_contract.docx
│   │   ├── thesis_v1.docx
│   │   ├── thesis_v2.docx
│   │   └── with_table.docx
│   ├── test_parser.py
│   ├── test_differ.py
│   ├── test_matcher.py
│   ├── test_formatter.py
│   ├── test_html_generator.py
│   ├── test_cli.py
│   └── test_webapp.py
├── requirements.txt
├── pyproject.toml
├── ROADMAP.md
└── README.md
```

## Запуск тестов

```bash
pytest tests/ -v
```

## Зависимости

- Python 3.10+
- `python-docx`, `sentence-transformers`, `scikit-learn`, `numpy`, `torch`
- `fastapi`, `uvicorn`, `jinja2`, `python-multipart` (для GUI и webapp)
- `pytest` (для разработки)

## Критерии готовности

- [x] pytest проходит на тестовых фикстурах (28 тестов)
- [x] CLI, веб-приложение и GUI работают
- [x] HTML-отчёт с интерактивным UI (тёмная тема, фильтры, TOC)
- [x] README с примерами использования
