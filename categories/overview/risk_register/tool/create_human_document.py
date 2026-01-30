#!/usr/bin/env python3
"""risk_register YAML → Markdown 変換（リスク登録簿）"""

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

    lines.append(f"# {meta.get('title', 'リスク登録簿')}")
    lines.append("")
    lines.append(f"**タイプ:** 📊 リスク登録簿 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    risks = data.get('risks', [])
    if risks:
        impact_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        status_labels = {'open': '⬜ 未対応', 'mitigating': '🔄 対策中', 'mitigated': '✅ 対策済', 'closed': '✅ クローズ'}
        lines.append("## リスク一覧")
        lines.append("")
        lines.append("| ID | リスク | 影響度 | 対策 | オーナー | 状態 | 識別日 |")
        lines.append("|----|--------|--------|------|----------|------|--------|")
        for r in risks:
            icon = impact_icons.get(r.get('impact', ''), '')
            status = status_labels.get(r.get('status', 'open'), r.get('status', '-'))
            lines.append(f"| {r.get('id', '-')} | {r.get('risk', '-')} | {icon} {r.get('impact', '-')} | {r.get('mitigation') or '-'} | {r.get('owner') or '-'} | {status} | {r.get('identified_at') or '-'} |")
        lines.append("")

        # Mermaid pie: impact distribution
        counts = {'high': 0, 'medium': 0, 'low': 0}
        for r in risks:
            imp = r.get('impact')
            if imp in counts:
                counts[imp] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title リスク影響度分布")
            for level, count in counts.items():
                if count > 0:
                    labels = {'high': '高', 'medium': '中', 'low': '低'}
                    lines.append(f'    "{labels[level]}" : {count}')
            lines.append("```")
            lines.append("")

        for r in risks:
            if r.get('mitigation') or r.get('identified_at'):
                lines.append(f"### {r.get('id', '-')}: {r.get('risk', '')}")
                if r.get('mitigation'):
                    lines.append("")
                    lines.append(f"**対策:** {r['mitigation']}")
                if r.get('owner') or r.get('identified_at'):
                    lines.append(f"**オーナー:** {r.get('owner') or '-'} / **識別日:** {r.get('identified_at') or '-'}")
                lines.append("")
    else:
        lines.append("## リスク一覧")
        lines.append("")
        lines.append(format_empty_section_hint("risks"))
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
