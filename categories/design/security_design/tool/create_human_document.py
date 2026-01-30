#!/usr/bin/env python3
"""security_design YAML → Markdown 変換（セキュリティ設計・脅威モデル）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_overview_section,
    format_references_section,
    format_status,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', 'セキュリティ設計・脅威モデル')}")
    lines.append("")
    lines.append(f"**タイプ:** 🔒 セキュリティ設計 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    overview = data.get('overview', {})
    overview_section = format_overview_section(overview, output_path=output_path)
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")

    threats = data.get('threats', [])
    if threats:
        impact_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        status_labels = {'open': '⬜ 未対応', 'mitigating': '🔄 対策中', 'mitigated': '✅ 対策済', 'accepted': '✅ 受容'}
        lines.append("## 脅威と対策一覧")
        lines.append("")
        lines.append("| ID | 脅威 | 影響度 | 対策状況 |")
        lines.append("|----|------|--------|----------|")
        for t in threats:
            icon = impact_icons.get(t.get('impact', ''), '')
            status = status_labels.get(t.get('status', 'open'), t.get('status', '-'))
            threat_short = (t.get('threat') or '-')[:40] + ('...' if len((t.get('threat') or '')) > 40 else '')
            lines.append(f"| {t.get('id', '-')} | {threat_short} | {icon} {t.get('impact', '-')} | {status} |")
        lines.append("")

        for t in threats:
            lines.append(f"### {t.get('id', '-')}: {t.get('threat', '')}")
            lines.append("")
            if t.get('impact'):
                lines.append(f"**影響度:** {t['impact']}")
                lines.append("")
            if t.get('countermeasure'):
                lines.append(f"**対策:** {t['countermeasure']}")
                lines.append("")
            if t.get('status'):
                lines.append(f"**対策状況:** {status_labels.get(t['status'], t['status'])}")
                lines.append("")
            if t.get('related_docs'):
                lines.append("**関連資料:**")
                for rd in t['related_docs']:
                    lines.append(f"- [{rd.get('title', '-')}]({rd.get('url', '')})")
                lines.append("")
    else:
        lines.append("## 脅威と対策一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
