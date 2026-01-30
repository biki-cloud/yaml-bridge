#!/usr/bin/env python3
"""stakeholder_raci YAML → Markdown 変換（ステークホルダー・RACI）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_empty_section_hint,
    format_navigation_footer,
    format_references_section,
    format_status,
    get_doc_type_role_description,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', 'ステークホルダー・RACI')}")
    lines.append("")
    lines.append(f"**タイプ:** 👥 ステークホルダー・RACI | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    items = data.get('raci_items', [])
    if items:
        lines.append("## RACI一覧")
        lines.append("")
        lines.append("| 範囲・活動 | R 実行 | A 説明責任 | C 相談 | I 報告 | 備考 |")
        lines.append("|-----------|--------|------------|--------|--------|------|")
        for r in items:
            resp = r.get('responsible') or '-'
            acc = r.get('accountable') or '-'
            cons = ', '.join(r.get('consulted') or []) or '-'
            inf = ', '.join(r.get('informed') or []) or '-'
            notes = (r.get('notes') or '-')[:30] + ('...' if len((r.get('notes') or '')) > 30 else '')
            lines.append(f"| {r.get('scope', '-')} | {resp} | {acc} | {cons} | {inf} | {notes} |")
        lines.append("")
        for r in items:
            if r.get('notes'):
                lines.append(f"### {r.get('scope', '-')}")
                lines.append("")
                lines.append(r['notes'])
                lines.append("")
    else:
        lines.append("## RACI一覧")
        lines.append("")
        lines.append(format_empty_section_hint("raci_items"))
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
