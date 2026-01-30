#!/usr/bin/env python3
"""decisions YAML → Markdown 変換（決定ログ・ADR）"""

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
    load_yaml,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', '決定ログ')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 決定ログ（ADR） | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    decisions = data.get('decisions', [])
    if decisions:
        lines.append("## 決定一覧")
        lines.append("")
        lines.append("決まったことの記録。open_items の検討事項が決まったらここに結論を追記する。")
        lines.append("")
        lines.append("| ID | 概要 | 結論 | 決定日 | 決定者 | 紐づく検討事項 |")
        lines.append("|----|------|------|--------|--------|----------------|")
        for d in decisions:
            summary_short = (d.get('summary') or '-')[:40] + ('...' if len((d.get('summary') or '')) > 40 else '')
            conclusion_short = (d.get('conclusion') or '-')[:40] + ('...' if len((d.get('conclusion') or '')) > 40 else '')
            lines.append(f"| {d.get('id', '-')} | {summary_short} | {conclusion_short} | {d.get('decided_at') or '-'} | {d.get('decided_by') or '-'} | {d.get('related_open_decision_id') or '-'} |")
        lines.append("")
        for d in decisions:
            lines.append(f"### {d.get('id', '-')}: {d.get('summary', '')}")
            lines.append("")
            lines.append(f"**結論:** {d.get('conclusion', '-')}")
            if d.get('context'):
                lines.append("")
                lines.append("**背景・理由:**")
                lines.append(d['context'])
            if d.get('decided_at') or d.get('decided_by'):
                lines.append("")
                lines.append(f"**決定:** {d.get('decided_at') or '-'} / {d.get('decided_by') or '-'}")
            if d.get('related_open_decision_id'):
                lines.append(f"**紐づく検討事項 ID:** {d['related_open_decision_id']}")
            lines.append("")
    else:
        lines.append("## 決定一覧")
        lines.append("")
        lines.append(format_empty_section_hint("decisions"))
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
