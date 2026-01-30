#!/usr/bin/env python3
"""tasks YAML → Markdown 変換（カテゴリの詳細タスク一覧）"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_empty_section_hint,
    format_navigation_footer,
    format_references_section,
    format_status,
    get_doc_type_role_description,
    load_yaml,
    run_create_human_document,
)


def _wbs_code_sort_key(wbs_code: str) -> tuple:
    if not wbs_code:
        return (0,)
    parts = [int(x) if x.isdigit() else 0 for x in re.split(r'[.\s]+', str(wbs_code)) if x]
    return tuple(parts)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', '詳細タスク')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 詳細タスク | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    role = get_doc_type_role_description(meta.get('category', ''), meta.get('doc_type', ''))
    if role:
        lines.append(f"**この doc_type の役割:** {role}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    tasks = data.get('tasks', [])
    if tasks:
        lines.append("## タスク一覧")
        lines.append("")
        status_icons = {'todo': '⬜', 'wip': '🔄', 'done': '✅'}
        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines.append("| ID | WBS | タスク | 優先度 | ステータス | 見積(h) | 依存 |")
        lines.append("|----|-----|--------|--------|----------|---------|------|")
        for t in sorted(tasks, key=lambda x: _wbs_code_sort_key(x.get('wbs_code') or '')):
            st = status_icons.get(t.get('status', ''), '') + ' ' + (t.get('status') or '-')
            pr = priority_icons.get(t.get('priority', ''), '') + ' ' + (t.get('priority') or '-')
            deps = ", ".join(t.get('dependencies') or []) or "-"
            lines.append(f"| {t.get('id', '-')} | {t.get('wbs_code') or '-'} | {t.get('title', '-')} | {pr} | {st} | {t.get('estimated_hours', '-')} | {deps} |")
        lines.append("")
        for t in tasks:
            if t.get('description') or t.get('dependencies'):
                lines.append(f"### {t.get('id', '-')}: {t.get('title', '-')}")
                lines.append("")
                if t.get('description'):
                    lines.append(t['description'])
                    lines.append("")
                if t.get('dependencies'):
                    lines.append(f"**依存:** {', '.join(t['dependencies'])}")
                    lines.append("")
    else:
        lines.append("## タスク一覧")
        lines.append("")
        lines.append(format_empty_section_hint("tasks"))
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    nav = format_navigation_footer(output_path)
    if nav:
        lines.append(nav.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
