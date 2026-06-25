from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .differ import Differ, SentenceDiff
from .matcher import BlockMatch, MatchResult
from .parser import SemanticBlock


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DocDiff — Semantic Document Comparison</title>
<style>
:root {
  /* Light theme */
  --bg: #f8f9fa;
  --surface: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #6b7280;
  --border: #e5e7eb;
  --border-light: #f3f4f6;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04);

  /* Change type colors */
  --modified-bg: #fef3c7;
  --modified-text: #92400e;
  --modified-border: #fbbf24;
  --modified-accent: #d97706;
  --added-bg: #dcfce7;
  --added-text: #166534;
  --added-border: #4ade80;
  --added-accent: #16a34a;
  --removed-bg: #fee2e2;
  --removed-text: #991b1b;
  --removed-border: #f87171;
  --removed-accent: #dc2626;
  --moved-bg: #dbeafe;
  --moved-text: #1e40af;
  --moved-border: #60a5fa;
  --moved-accent: #2563eb;

  --num-old: #dc2626;
  --num-new: #16a34a;

  /* Sidebar */
  --sidebar-bg: #ffffff;
  --sidebar-width: 280px;
  --header-height: 64px;
}

[data-theme="dark"] {
  --bg: #0f172a;
  --surface: #1e293b;
  --text: #f1f5f9;
  --text-secondary: #94a3b8;
  --border: #334155;
  --border-light: #1e293b;
  --accent: #60a5fa;
  --accent-hover: #3b82f6;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -1px rgba(0,0,0,0.2);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.4), 0 4px 6px -2px rgba(0,0,0,0.3);
  --sidebar-bg: #1e293b;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  transition: background-color 0.3s, color 0.3s;
}

/* ===== Header ===== */
.header {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: var(--header-height);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  z-index: 100;
  box-shadow: var(--shadow);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
}

.header-left .subtitle {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 0.15rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ===== Theme Toggle ===== */
.theme-toggle {
  background: none;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: 1rem;
  color: var(--text-secondary);
  transition: all 0.2s;
}
.theme-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* ===== Filter Buttons ===== */
.filter-btn {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-secondary);
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.filter-btn:hover { border-color: var(--accent); color: var(--accent); }
.filter-btn.active.modified { background: var(--modified-bg); color: var(--modified-text); border-color: var(--modified-border); }
.filter-btn.active.added { background: var(--added-bg); color: var(--added-text); border-color: var(--added-border); }
.filter-btn.active.removed { background: var(--removed-bg); color: var(--removed-text); border-color: var(--removed-border); }
.filter-btn.active.moved { background: var(--moved-bg); color: var(--moved-text); border-color: var(--moved-border); }
.filter-btn.inactive { opacity: 0.35; }

/* ===== Sidebar ===== */
.sidebar {
  position: fixed;
  left: 0; top: var(--header-height); bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 1.25rem 1rem;
  z-index: 90;
  transition: background-color 0.3s;
}

.sidebar h3 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

.toc-item {
  display: block;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text);
  text-decoration: none;
  margin-bottom: 0.25rem;
  transition: background 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-left: 3px solid transparent;
}
.toc-item:hover { background: var(--border-light); }
.toc-item.modified { border-left-color: var(--modified-accent); }
.toc-item.added { border-left-color: var(--added-accent); }
.toc-item.removed { border-left-color: var(--removed-accent); }
.toc-item.moved { border-left-color: var(--moved-accent); }
.toc-item .badge-mini {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-weight: 700;
  text-transform: uppercase;
  margin-right: 0.4rem;
}
.toc-item.modified .badge-mini { background: var(--modified-bg); color: var(--modified-text); }
.toc-item.added .badge-mini { background: var(--added-bg); color: var(--added-text); }
.toc-item.removed .badge-mini { background: var(--removed-bg); color: var(--removed-text); }
.toc-item.moved .badge-mini { background: var(--moved-bg); color: var(--moved-text); }

/* ===== Main Content ===== */
.main-content {
  margin-left: var(--sidebar-width);
  margin-top: var(--header-height);
  padding: 1.5rem 2rem;
  max-width: 900px;
}

/* ===== Stats Bar ===== */
.stats-bar {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
  padding: 1rem 1.25rem;
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.stat-card {
  flex: 1;
  min-width: 120px;
  text-align: center;
  padding: 0.75rem;
  border-radius: 8px;
}
.stat-card .stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  line-height: 1;
}
.stat-card .stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.4rem;
  font-weight: 600;
}
.stat-card.modified { background: var(--modified-bg); }
.stat-card.modified .stat-value { color: var(--modified-accent); }
.stat-card.modified .stat-label { color: var(--modified-text); }
.stat-card.added { background: var(--added-bg); }
.stat-card.added .stat-value { color: var(--added-accent); }
.stat-card.added .stat-label { color: var(--added-text); }
.stat-card.removed { background: var(--removed-bg); }
.stat-card.removed .stat-value { color: var(--removed-accent); }
.stat-card.removed .stat-label { color: var(--removed-text); }
.stat-card.moved { background: var(--moved-bg); }
.stat-card.moved .stat-value { color: var(--moved-accent); }
.stat-card.moved .stat-label { color: var(--moved-text); }

/* ===== Change Block ===== */
.change-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 1.5rem;
  overflow: hidden;
  box-shadow: var(--shadow);
  transition: opacity 0.3s, transform 0.3s;
  scroll-margin-top: calc(var(--header-height) + 1rem);
}
.change-block.hidden { display: none; }
.change-block.fade { opacity: 0.35; }

.change-block.modified { border-left: 4px solid var(--modified-accent); }
.change-block.added { border-left: 4px solid var(--added-accent); }
.change-block.removed { border-left: 4px solid var(--removed-accent); }
.change-block.moved { border-left: 4px solid var(--moved-accent); }

.change-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--border-light);
  cursor: pointer;
  user-select: none;
}
.change-header:hover { background: var(--bg); }
.change-header h2 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  flex: 1;
  color: var(--text);
}
.change-header .toggle-icon {
  font-size: 0.8rem;
  color: var(--text-secondary);
  transition: transform 0.2s;
}
.change-header.collapsed .toggle-icon { transform: rotate(-90deg); }

.badge {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.25rem 0.65rem;
  border-radius: 6px;
  border: 1px solid;
  white-space: nowrap;
}
.badge.modified { background: var(--modified-bg); color: var(--modified-text); border-color: var(--modified-border); }
.badge.added { background: var(--added-bg); color: var(--added-text); border-color: var(--added-border); }
.badge.removed { background: var(--removed-bg); color: var(--removed-text); border-color: var(--removed-border); }
.badge.moved { background: var(--moved-bg); color: var(--moved-text); border-color: var(--moved-border); }

.score {
  font-size: 0.78rem;
  color: var(--text-secondary);
  font-family: "SF Mono", Monaco, "Cascadia Code", monospace;
  background: var(--bg);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.change-body {
  transition: max-height 0.3s ease-out, opacity 0.3s ease-out;
  max-height: 5000px;
  opacity: 1;
  overflow: hidden;
}
.change-body.collapsed {
  max-height: 0;
  opacity: 0;
}

/* ===== Side by Side ===== */
.side-by-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border);
}
.column {
  background: var(--surface);
  padding: 1.25rem 1.5rem;
}
.column-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}
.column-header .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.column-header .dot.old { background: var(--removed-accent); }
.column-header .dot.new { background: var(--added-accent); }
.column.old { border-left: 3px solid var(--removed-accent); }
.column.new { border-left: 3px solid var(--added-accent); }

.text-block {
  font-size: 0.92rem;
  line-height: 1.7;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
}

/* ===== Sentence Diff ===== */
.sentence-diff {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
}
.sentence-diff h4 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}
.sentence-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.sentence-list li {
  padding: 0.4rem 0;
  font-size: 0.9rem;
  line-height: 1.6;
  border-bottom: 1px dashed var(--border-light);
}
.sentence-list li:last-child { border-bottom: none; }

.del {
  background: var(--removed-bg);
  color: var(--removed-text);
  text-decoration: line-through;
  padding: 0.1rem 0.25rem;
  border-radius: 4px;
  font-weight: 500;
}
.ins {
  background: var(--added-bg);
  color: var(--added-text);
  font-weight: 700;
  padding: 0.1rem 0.25rem;
  border-radius: 4px;
}
.rep-del {
  background: var(--removed-bg);
  color: var(--removed-text);
  text-decoration: line-through;
  padding: 0.1rem 0.25rem;
  border-radius: 4px;
}
.rep-ins {
  background: var(--added-bg);
  color: var(--added-text);
  font-weight: 700;
  padding: 0.1rem 0.25rem;
  border-radius: 4px;
}

/* ===== Numeric Changes ===== */
.num-change {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  background: var(--border-light);
}
.num-change-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 600;
}
.num-pairs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.num-pair {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.75rem;
  background: var(--surface);
  border-radius: 8px;
  border: 1px solid var(--border);
  font-size: 0.9rem;
}
.num-old-val {
  color: var(--num-old);
  font-weight: 700;
  font-family: "SF Mono", Monaco, monospace;
  font-size: 0.95rem;
}
.num-arrow {
  color: var(--text-secondary);
  font-size: 0.8rem;
}
.num-new-val {
  color: var(--num-new);
  font-weight: 700;
  font-family: "SF Mono", Monaco, monospace;
  font-size: 0.95rem;
}

/* ===== Single Column (added/removed) ===== */
.single-column {
  padding: 1.25rem 1.5rem;
}
.single-column.old {
  border-left: 4px solid var(--removed-accent);
  background: var(--removed-bg);
}
.single-column.new {
  border-left: 4px solid var(--added-accent);
  background: var(--added-bg);
}

/* ===== Empty State ===== */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-secondary);
}
.empty-state h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--text);
}

/* ===== Footer ===== */
.footer {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
  font-size: 0.8rem;
  border-top: 1px solid var(--border);
  margin-top: 2rem;
}

/* ===== Responsive ===== */
@media (max-width: 900px) {
  .sidebar { display: none; }
  .main-content { margin-left: 0; }
  .header-right { display: none; }
  .side-by-side { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .main-content { padding: 1rem; }
  .stats-bar { gap: 0.5rem; }
  .stat-card { min-width: 80px; padding: 0.5rem; }
  .stat-card .stat-value { font-size: 1.25rem; }
}
</style>
</head>
<body data-theme="light">

<header class="header">
  <div class="header-left">
    <div>
      <h1>DocDiff</h1>
      <div class="subtitle">Semantic Document Comparison</div>
    </div>
  </div>
  <div class="header-right">
    <button class="filter-btn active all" onclick="filterAll()" id="btn-all">Все</button>
    <button class="filter-btn modified" onclick="filterType('modified')" id="btn-modified">Modified</button>
    <button class="filter-btn added" onclick="filterType('added')" id="btn-added">Added</button>
    <button class="filter-btn removed" onclick="filterType('removed')" id="btn-removed">Removed</button>
    <button class="filter-btn moved" onclick="filterType('moved')" id="btn-moved">Moved</button>
    <button class="theme-toggle" onclick="toggleTheme()" title="Переключить тему">🌓</button>
  </div>
</header>

<aside class="sidebar">
  <h3>Содержание</h3>
  <nav id="toc">
{{TOC}}
  </nav>
</aside>

<main class="main-content">
  <div class="stats-bar">
{{STATS}}
  </div>
{{BODY}}
  <footer class="footer">Сгенерировано docdiff</footer>
</main>

<script>
// ===== Theme Toggle =====
function toggleTheme() {
  const body = document.body;
  const current = body.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  body.setAttribute('data-theme', next);
  localStorage.setItem('docdiff-theme', next);
}
// Restore saved theme
const savedTheme = localStorage.getItem('docdiff-theme');
if (savedTheme) document.body.setAttribute('data-theme', savedTheme);

// ===== Collapsible Sections =====
document.querySelectorAll('.change-header').forEach(header => {
  header.addEventListener('click', () => {
    const body = header.nextElementSibling;
    if (!body) return;
    header.classList.toggle('collapsed');
    body.classList.toggle('collapsed');
  });
});

// ===== Filter =====
let activeFilter = 'all';
function filterAll() {
  activeFilter = 'all';
  document.querySelectorAll('.change-block').forEach(b => b.classList.remove('hidden'));
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active', 'inactive'));
  document.getElementById('btn-all').classList.add('active');
  updateTocVisibility();
}
function filterType(type) {
  activeFilter = type;
  document.querySelectorAll('.change-block').forEach(b => {
    if (b.classList.contains(type)) b.classList.remove('hidden');
    else b.classList.add('hidden');
  });
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('btn-' + type).classList.add('active');
  updateTocVisibility();
}
function updateTocVisibility() {
  document.querySelectorAll('.toc-item').forEach(item => {
    const targetId = item.getAttribute('href').slice(1);
    const target = document.getElementById(targetId);
    if (!target) return;
    item.style.display = (activeFilter === 'all' || target.classList.contains(activeFilter)) ? 'flex' : 'none';
  });
}

// ===== Scroll Spy for TOC =====
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      document.querySelectorAll('.toc-item').forEach(i => i.classList.remove('active'));
      const link = document.querySelector('.toc-item[href="#' + entry.target.id + '"]');
      if (link) link.classList.add('active');
    }
  });
}, { rootMargin: '-80px 0px -70% 0px' });

document.querySelectorAll('.change-block').forEach(block => observer.observe(block));
</script>

</body>
</html>
"""


class HtmlGenerator:
    def __init__(self, differ: Differ) -> None:
        self.differ = differ

    def _escape(self, text: str | None) -> str:
        if text is None:
            return ""
        return html.escape(text).replace("\n", "<br>")

    def _badge(self, change_type: str) -> str:
        return f'<span class="badge {change_type}">{change_type}</span>'

    def _render_sentence_diff(self, sd: SentenceDiff) -> str:
        if sd.type == "equal":
            return f"<li>{self._escape(sd.old_text)}</li>"
        elif sd.type == "delete":
            return f'<li><span class="del">{self._escape(sd.old_text)}</span></li>'
        elif sd.type == "insert":
            return f'<li><span class="ins">{self._escape(sd.new_text)}</span></li>'
        elif sd.type == "replace":
            parts = []
            for tag, old_frag, new_frag in sd.word_opcodes:
                if tag == "equal":
                    parts.append(self._escape(old_frag))
                elif tag == "delete":
                    parts.append(f'<span class="rep-del">{self._escape(old_frag)}</span>')
                elif tag == "insert":
                    parts.append(f'<span class="rep-ins">{self._escape(new_frag)}</span>')
                elif tag == "replace":
                    parts.append(f'<span class="rep-del">{self._escape(old_frag)}</span>')
                    parts.append(f'<span class="rep-ins">{self._escape(new_frag)}</span>')
            text = " ".join(parts)
            return f'<li>{text}</li>'
        return ""

    def _render_numeric_changes(self, numeric_changes: List[Dict[str, str]]) -> str:
        if not numeric_changes:
            return ""
        items = ""
        for nc in numeric_changes:
            items += (
                f'<span class="num-pair">'
                f'<span class="num-old-val">{self._escape(nc.get("old_value", ""))}</span>'
                f'<span class="num-arrow">→</span>'
                f'<span class="num-new-val">{self._escape(nc.get("new_value", ""))}</span>'
                f'</span>'
            )
        return (
            f'<div class="num-change">'
            f'<div class="num-change-label">Числовые изменения</div>'
            f'<div class="num-pairs">{items}</div>'
            f'</div>'
        )

    def _slug(self, text: str) -> str:
        """Create a URL-safe anchor slug."""
        s = re.sub(r'[^\w\s-]', '', text.lower())
        s = re.sub(r'[-\s]+', '-', s).strip('-')
        return s[:50] or "section"

    def _render_modified(self, match: BlockMatch, index: int) -> tuple[str, str]:
        old_text = match.block_a.full_text if match.block_a else ""
        new_text = match.block_b.full_text if match.block_b else ""
        context = match.block_a.title if match.block_a and match.block_a.title else (match.block_b.title if match.block_b else "Без раздела")
        anchor = f"block-{index}-{self._slug(context)}"

        sentence_diffs = self.differ.diff_sentences(old_text, new_text)
        sentences_html = "".join(self._render_sentence_diff(sd) for sd in sentence_diffs)

        numeric_changes = []
        for sd in sentence_diffs:
            for nc in sd.numeric_changes:
                numeric_changes.append({"old_value": nc.old_value, "new_value": nc.new_value})
        num_html = self._render_numeric_changes(numeric_changes)

        toc_entry = (
            f'<a href="#{anchor}" class="toc-item {match.type}">'
            f'<span class="badge-mini">{match.type[:3]}</span>'
            f'{self._escape(context[:45])}'
            f'</a>'
        )

        body = (
            f'<section class="change-block {match.type}" id="{anchor}">'
            f'<div class="change-header">'
            f'<h2>{self._escape(context)}</h2>'
            f'{self._badge(match.type)}'
            f'<span class="score">score: {match.score:.2f}</span>'
            f'<span class="toggle-icon">▼</span>'
            f'</div>'
            f'<div class="change-body">'
            f'<div class="side-by-side">'
            f'<div class="column old">'
            f'<div class="column-header"><span class="dot old"></span>Было</div>'
            f'<div class="text-block">{self._escape(old_text)}</div>'
            f'</div>'
            f'<div class="column new">'
            f'<div class="column-header"><span class="dot new"></span>Стало</div>'
            f'<div class="text-block">{self._escape(new_text)}</div>'
            f'</div>'
            f'</div>'
            f'{num_html}'
            f'<div class="sentence-diff">'
            f'<h4>Детализация по предложениям</h4>'
            f'<ul class="sentence-list">{sentences_html}</ul>'
            f'</div>'
            f'</div>'
            f'</section>'
        )
        return toc_entry, body

    def _render_added(self, match: BlockMatch, index: int) -> tuple[str, str]:
        new_text = match.block_b.full_text if match.block_b else ""
        context = match.block_b.title if match.block_b and match.block_b.title else "Без раздела"
        anchor = f"block-{index}-{self._slug(context)}"

        toc_entry = (
            f'<a href="#{anchor}" class="toc-item {match.type}">'
            f'<span class="badge-mini">ADD</span>'
            f'{self._escape(context[:45])}'
            f'</a>'
        )

        body = (
            f'<section class="change-block {match.type}" id="{anchor}">'
            f'<div class="change-header">'
            f'<h2>{self._escape(context)}</h2>'
            f'{self._badge(match.type)}'
            f'<span class="score">—</span>'
            f'<span class="toggle-icon">▼</span>'
            f'</div>'
            f'<div class="change-body">'
            f'<div class="single-column new">'
            f'<div class="text-block">{self._escape(new_text)}</div>'
            f'</div>'
            f'</div>'
            f'</section>'
        )
        return toc_entry, body

    def _render_removed(self, match: BlockMatch, index: int) -> tuple[str, str]:
        old_text = match.block_a.full_text if match.block_a else ""
        context = match.block_a.title if match.block_a and match.block_a.title else "Без раздела"
        anchor = f"block-{index}-{self._slug(context)}"

        toc_entry = (
            f'<a href="#{anchor}" class="toc-item {match.type}">'
            f'<span class="badge-mini">DEL</span>'
            f'{self._escape(context[:45])}'
            f'</a>'
        )

        body = (
            f'<section class="change-block {match.type}" id="{anchor}">'
            f'<div class="change-header">'
            f'<h2>{self._escape(context)}</h2>'
            f'{self._badge(match.type)}'
            f'<span class="score">—</span>'
            f'<span class="toggle-icon">▼</span>'
            f'</div>'
            f'<div class="change-body">'
            f'<div class="single-column old">'
            f'<div class="text-block">{self._escape(old_text)}</div>'
            f'</div>'
            f'</div>'
            f'</section>'
        )
        return toc_entry, body

    def generate(self, result: MatchResult) -> str:
        summary = {"modified": 0, "moved": 0, "added": 0, "removed": 0}
        toc_parts = []
        body_parts = []

        for i, match in enumerate(result.matches):
            summary[match.type] = summary.get(match.type, 0) + 1
            if match.type in ("modified", "moved"):
                toc, body = self._render_modified(match, i)
            elif match.type == "added":
                toc, body = self._render_added(match, i)
            elif match.type == "removed":
                toc, body = self._render_removed(match, i)
            else:
                continue
            toc_parts.append(toc)
            body_parts.append(body)

        # Stats cards
        stats_html = ""
        for typ in ["modified", "added", "removed", "moved"]:
            count = summary.get(typ, 0)
            if count > 0:
                stats_html += (
                    f'<div class="stat-card {typ}">'
                    f'<div class="stat-value">{count}</div>'
                    f'<div class="stat-label">{typ.capitalize()}</div>'
                    f'</div>'
                )
        if not stats_html:
            stats_html = '<div class="stat-card"><div class="stat-value">0</div><div class="stat-label">Изменений</div></div>'

        toc = "\n".join(toc_parts) if toc_parts else '<div style="color:var(--text-secondary);font-size:0.85rem;">Нет изменений</div>'
        body = "\n".join(body_parts) if body_parts else (
            f'<div class="empty-state">'
            f'<h3>Нет изменений</h3>'
            f'<p>Документы идентичны или порог сходства слишком высокий.</p>'
            f'</div>'
        )

        return _HTML_TEMPLATE.replace("{{STATS}}", stats_html).replace("{{BODY}}", body).replace("{{TOC}}", toc)
