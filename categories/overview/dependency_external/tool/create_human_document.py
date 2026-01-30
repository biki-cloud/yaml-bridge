#!/usr/bin/env python3
"""dependency_external YAML → Markdown 変換（外部依存）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_references_section,
    format_status,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', '外部依存')}")
    lines.append("")
    lines.append(f"**タイプ:** 🔗 外部依存 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    type_labels = {'vendor': 'ベンダー', 'project': '他プロジェクト', 'team': '他チーム', 'other': 'その他'}
    deps = data.get('dependencies', [])
    if deps:
        lines.append("## 外部依存一覧")
        lines.append("")
        lines.append("| ID | 名前 | 種別 | 窓口 | SLA・契約 | リスク参照 |")
        lines.append("|----|------|------|------|-----------|------------|")
        for d in deps:
            typ = type_labels.get(d.get('type'), d.get('type') or '-')
            sla_short = (d.get('sla') or '-')[:30] + ('...' if len((d.get('sla') or '')) > 30 else '')
            lines.append(f"| {d.get('id', '-')} | {d.get('name', '-')} | {typ} | {d.get('owner') or '-'} | {sla_short} | {d.get('risk_register_id') or '-'} |")
        lines.append("")
        for d in deps:
            if d.get('notes'):
                lines.append(f"### {d.get('id', '-')}: {d.get('name', '')}")
                lines.append("")
                lines.append(d['notes'])
                lines.append("")
    else:
        lines.append("## 外部依存一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
