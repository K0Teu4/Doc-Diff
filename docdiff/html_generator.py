from __future__ import annotations

import html
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
<title>Semantic Document Diff</title>
<style>
  :root {
    --bg: #f4f6f8;
    --card-bg: #ffffff;
    --text: #1a1a2e;
    --muted: #6b7280;
    --border: #e5e7eb;
    --removed-bg: #fff0f0;
    --removed-text: #991b1b;
    --removed-border: #fecaca;
    --added-bg: #f0fdf4;
    --added-text: #166534;
    --added-border: #bbf7d0;
    --modified-bg: #fffbeb;
    --modified-text: #92400e;
    --modified-border: #fde68a;
    --moved-bg: #eff6ff;
    --moved-text: #1e40af;
    --moved-border: #bfdbfe;
    --num-old: #ef4444;
    --num-new: #22c55e;
  }
  * { box-sizing: border-box; }
  body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
    line-height: 1.6;
  }
  header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff;
    padding: 2rem 1rem;
    text-align: center;
  }
  header h1 { margin: 0 0 0.5rem; font-size: 1.75rem; }
  .stats {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 1rem;
  }
  .stat {
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.875rem;
    background: rgba(255,255,255,0.12);
    color: #fff;
  }
  .stat.modified { background: var(--modified-bg); color: var(--modified-text); }
  .stat.added { background: var(--added-bg); color: var(--added-text); }
  .stat.removed { background: var(--removed-bg); color: var(--removed-text); }
  .stat.moved { background: var(--moved-bg); color: var(--moved-text); }
  main { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
  .change-block {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 1.5rem;
    overflow: hidden;
  }
  .change-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);
    background: #fafafa;
  }
  .change-header h2 { margin: 0; font-size: 1.1rem; flex: 1; }
  .badge {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    border: 1px solid;
  }
  .badge.modified { background: var(--modified-bg); color: var(--modified-text); border-color: var(--modified-border); }
  .badge.added { background: var(--added-bg); color: var(--added-text); border-color: var(--added-border); }
  .badge.removed { background: var(--removed-bg); color: var(--removed-text); border-color: var(--removed-border); }
  .badge.moved { background: var(--moved-bg); color: var(--moved-text); border-color: var(--moved-border); }
  .score { font-size: 0.8rem; color: var(--muted); font-family: monospace; }
  .side-by-side { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--border); }
  .column { background: var(--card-bg); padding: 1rem 1.25rem; }
  .column h3 { margin: 0 0 0.5rem; font-size: 0.85rem; text-transform: uppercase; color: var(--muted); letter-spacing: 0.05em; }
  .column.old { border-left: 4px solid var(--removed-border); }
  .column.new { border-left: 4px solid var(--added-border); }
  .text-block { font-family: Georgia, "Times New Roman", serif; font-size: 0.95rem; white-space: pre-wrap; }
  .sentence-list { list-style: none; padding: 0; margin: 0; }
  .sentence-list li { padding: 0.3rem 0; }
  .del { background: var(--removed-bg); color: var(--removed-text); text-decoration: line-through; padding: 0 0.15rem; border-radius: 3px; }
  .ins { background: var(--added-bg); color: var(--added-text); font-weight: 600; padding: 0 0.15rem; border-radius: 3px; }
  .rep-del { background: var(--removed-bg); color: var(--removed-text); text-decoration: line-through; padding: 0 0.15rem; border-radius: 3px; }
  .rep-ins { background: var(--added-bg); color: var(--added-text); font-weight: 600; padding: 0 0.15rem; border-radius: 3px; }
  .num-change { margin-top: 0.75rem; padding: 0.75rem 1rem; background: #fafafa; border-radius: 8px; font-size: 0.85rem; }
  .num-change .label { color: var(--muted); margin-bottom: 0.25rem; }
  .num-pair { display: inline-flex; align-items: center; gap: 0.5rem; margin-right: 1rem; }
  .num-old-val { color: var(--num-old); font-weight: 700; font-family: monospace; }
  .num-arrow { color: var(--muted); }
  .num-new-val { color: var(--num-new); font-weight: 700; font-family: monospace; }
  .single-column { padding: 1rem 1.25rem; }
  .single-column.old { border-left: 4px solid var(--removed-border); background: var(--removed-bg); }
  .single-column.new { border-left: 4px solid var(--added-border); background: var(--added-bg); }
  footer { text-align: center; padding: 2rem 1rem; color: var(--muted); font-size: 0.8rem; }
  @media (max-width: 768px) {
    .side-by-side { grid-template-columns: 1fr; }
    .stats { gap: 0.5rem; }
  }
</style>
</head>
<body>
<header>
  <h1>Semantic Document Diff</h1>
  <div class="stats">{{STATS}}</div>
</header>
<main>
{{BODY}}
</main>
<footer>Сгенерировано docdiff</footer>
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
            # Build inline word diff
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
            f'<div class="label">Числовые изменения:</div>'
            f'<div>{items}</div>'
            f'</div>'
        )

    def _render_modified(self, match: BlockMatch) -> str:
        old_text = match.block_a.full_text if match.block_a else ""
        new_text = match.block_b.full_text if match.block_b else ""
        context = match.block_a.title if match.block_a and match.block_a.title else (match.block_b.title if match.block_b else "Без раздела")

        sentence_diffs = self.differ.diff_sentences(old_text, new_text)
        sentences_html = "".join(self._render_sentence_diff(sd) for sd in sentence_diffs)

        # Collect numeric changes from sentence diffs
        numeric_changes = []
        for sd in sentence_diffs:
            for nc in sd.numeric_changes:
                numeric_changes.append({"old_value": nc.old_value, "new_value": nc.new_value})

        num_html = self._render_numeric_changes(numeric_changes)

        return (
            f'<section class="change-block {match.type}">'
            f'<div class="change-header">'
            f'<h2>{self._escape(context)}</h2>'
            f'{self._badge(match.type)}'
            f'<span class="score">score: {match.score:.2f}</span>'
            f'</div>'
            f'<div class="side-by-side">'
            f'<div class="column old">'
            f'<h3>Было</h3>'
            f'<div class="text-block">{self._escape(old_text)}</div>'
            f'</div>'
            f'<div class="column new">'
            f'<h3>Стало</h3>'
            f'<div class="text-block">{self._escape(new_text)}</div>'
            f'</div>'
            f'</div>'
            f'{num_html}'
            f'<div style="padding: 0 1.25rem 1rem;">'
            f'<h3 style="font-size:0.85rem;color:var(--muted);margin:0.75rem 0 0.5rem;">Детализация по предложениям</h3>'
            f'<ul class="sentence-list">{sentences_html}</ul>'
            f'</div>'
            f'</section>'
        )

    def _render_added(self, match: BlockMatch) -> str:
        new_text = match.block_b.full_text if match.block_b else ""
        context = match.block_b.title if match.block_b and match.block_b.title else "Без раздела"
        return (
            f'<section class="change-block {match.type}">'
            f'<div class="change-header">'
            f'<h2>{self._escape(context)}</h2>'
            f'{self._badge(match.type)}'
            f'<span class="score">score: —</span>'
            f'</div>'
            f'<div class="single-column new">'
            f'<div class="text-block">{self._escape(new_text)}</div>'
            f'</div>'
            f'</section>'
        )

    def _render_removed(self, match: BlockMatch) -> str:
        old_text = match.block_a.full_text if match.block_a else ""
        context = match.block_a.title if match.block_a and match.block_a.title else "Без раздела"
        return (
            f'<section class="change-block {match.type}">'
            f'<div class="change-header">'
            f'<h2>{self._escape(context)}</h2>'
            f'{self._badge(match.type)}'
            f'<span class="score">score: —</span>'
            f'</div>'
            f'<div class="single-column old">'
            f'<div class="text-block">{self._escape(old_text)}</div>'
            f'</div>'
            f'</section>'
        )

    def generate(self, result: MatchResult) -> str:
        summary = {"modified": 0, "moved": 0, "added": 0, "removed": 0}
        body_parts = []

        for match in result.matches:
            summary[match.type] = summary.get(match.type, 0) + 1
            if match.type in ("modified", "moved"):
                body_parts.append(self._render_modified(match))
            elif match.type == "added":
                body_parts.append(self._render_added(match))
            elif match.type == "removed":
                body_parts.append(self._render_removed(match))

        stats = ""
        for typ, count in summary.items():
            if count > 0:
                stats += f'<span class="stat {typ}">{typ.capitalize()}: {count}</span>'
        if not stats:
            stats = '<span class="stat">Нет изменений</span>'

        body = "\n".join(body_parts) if body_parts else "<p style='text-align:center;color:var(--muted);'>Нет изменений.</p>"

        return _HTML_TEMPLATE.replace("{{STATS}}", stats).replace("{{BODY}}", body)
