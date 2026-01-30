#!/usr/bin/env python3
"""runbook YAML → Markdown 変換（ランブック・運用手順）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_references_section,
    format_status,
    format_overview_section,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', '運用ランブック')}")
    lines.append("")
    lines.append(f"**タイプ:** 📘 ランブック・運用手順 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    overview = data.get('overview', {})
    overview_section = format_overview_section(overview)
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")
    if overview.get('environment'):
        lines.append(f"**対象環境:** {overview['environment']}")
        lines.append("")
    if overview.get('target_system'):
        lines.append(f"**対象システム:** {overview['target_system']}")
        lines.append("")

    procedures = data.get('procedures', [])
    if procedures:
        type_labels = {
            "startup": "起動",
            "deploy": "デプロイ",
            "rollback": "ロールバック",
            "incident": "障害対応",
            "maintenance": "保守",
            "other": "その他",
        }
        lines.append("## 手順一覧")
        lines.append("")
        lines.append("| ID | 種別 | タイトル | 想定時間 |")
        lines.append("|----|------|----------|----------|")
        for p in procedures:
            ptype = type_labels.get(p.get('procedure_type'), p.get('procedure_type') or "-")
            est = f"{p.get('estimated_minutes')}分" if p.get('estimated_minutes') is not None else "-"
            lines.append(f"| {p.get('id', '-')} | {ptype} | {p.get('title', '-')} | {est} |")
        lines.append("")
        for proc in procedures:
            ptype = type_labels.get(proc.get('procedure_type'), proc.get('procedure_type') or "")
            lines.append(f"## {proc.get('id', '-')}: {proc.get('title', '-')}")
            if ptype:
                lines.append(f"**種別:** {ptype}")
                lines.append("")
            if proc.get('precondition'):
                lines.append(f"**事前条件:** {proc['precondition']}")
                lines.append("")
            lines.append("### 手順")
            lines.append("")
            for i, step in enumerate(proc.get('steps', []), 1):
                lines.append(f"**{i}. {step.get('action', '-')}**")
                lines.append("")
                if step.get('expected'):
                    lines.append(f"   期待結果: {step['expected']}")
                if step.get('note'):
                    lines.append(f"   備考: {step['note']}")
                lines.append("")
            if proc.get('postcondition'):
                lines.append(f"**事後条件:** {proc['postcondition']}")
                lines.append("")
    else:
        lines.append("## 手順一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
