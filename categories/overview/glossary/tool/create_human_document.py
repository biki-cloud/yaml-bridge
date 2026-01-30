#!/usr/bin/env python3
"""glossary YAML → Markdown 変換（用語集）"""

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

    lines.append(f"# {meta.get('title', '用語集')}")
    lines.append("")
    lines.append(f"**タイプ:** 📖 用語集 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    terms = data.get('terms', [])
    if terms:
        lines.append("## 用語一覧")
        lines.append("")
        lines.append("| ID | 用語 | 定義 |")
        lines.append("|----|------|------|")
        for t in terms:
            def_short = (t.get('definition') or '-')[:50]
            if len(t.get('definition') or '') > 50:
                def_short += "..."
            lines.append(f"| {t.get('id', '-')} | {t.get('term', '-')} | {def_short} |")
        lines.append("")
        for t in terms:
            lines.append(f"### {t.get('id', '-')}: {t.get('term', '')}")
            lines.append("")
            lines.append(t.get('definition', '-'))
            lines.append("")
            if t.get('alias'):
                lines.append(f"**別表記:** {', '.join(t['alias'])}")
                lines.append("")
            if t.get('related_terms'):
                lines.append(f"**関連用語:** {', '.join(t['related_terms'])}")
                lines.append("")
            if t.get('source'):
                lines.append(f"**出典:** {t['source']}")
                lines.append("")
    else:
        lines.append("## 用語一覧")
        lines.append("")
        lines.append(format_empty_section_hint("terms"))
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
