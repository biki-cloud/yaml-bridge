#!/usr/bin/env python3
"""incident_postmortem YAML → Markdown 変換（障害・振り返り）"""

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

    lines.append(f"# {meta.get('title', '障害・振り返り')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 障害・振り返り | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    severity_labels = {'critical': '🔴 重大', 'high': '🟠 高', 'medium': '🟡 中', 'low': '🟢 低'}
    incidents = data.get('incidents', [])
    if incidents:
        lines.append("## 障害・インシデント一覧")
        lines.append("")
        lines.append("| ID | タイトル | 発生日時 | 解消日時 | 深刻度 |")
        lines.append("|----|----------|----------|----------|--------|")
        for i in incidents:
            sev = severity_labels.get(i.get('severity'), i.get('severity') or '-')
            lines.append(f"| {i.get('id', '-')} | {i.get('title', '-')} | {i.get('occurred_at') or '-'} | {i.get('resolved_at') or '-'} | {sev} |")
        lines.append("")
        for i in incidents:
            lines.append(f"### {i.get('id', '-')}: {i.get('title', '')}")
            lines.append("")
            lines.append("**概要:** " + (i.get('summary') or '-'))
            if i.get('occurred_at') or i.get('resolved_at'):
                lines.append("")
                lines.append(f"**期間:** {i.get('occurred_at') or '-'} ～ {i.get('resolved_at') or '-'}")
            if i.get('root_cause'):
                lines.append("")
                lines.append("**原因:**")
                lines.append(i['root_cause'])
            if i.get('action_taken'):
                lines.append("")
                lines.append("**対応内容:**")
                lines.append(i['action_taken'])
            if i.get('prevention'):
                lines.append("")
                lines.append("**再発防止策:**")
                lines.append(i['prevention'])
            if i.get('runbook_ref'):
                lines.append("")
                lines.append("**参照ランブック:** " + i['runbook_ref'])
            if i.get('notes'):
                lines.append("")
                lines.append(i['notes'])
            lines.append("")
    else:
        lines.append("## 障害・インシデント一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
