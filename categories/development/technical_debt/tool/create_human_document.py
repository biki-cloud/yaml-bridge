#!/usr/bin/env python3
"""technical_debt YAML → Markdown 変換（技術的負債）"""

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

    lines.append(f"# {meta.get('title', '技術的負債')}")
    lines.append("")
    lines.append(f"**タイプ:** 📦 技術的負債 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    overview = data.get('overview')
    if overview:
        overview_section = format_overview_section(overview, output_path=output_path)
        if overview_section:
            lines.append(overview_section.rstrip())
            lines.append("")

    items = data.get('items', [])
    if items:
        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        status_labels = {'open': '⬜ 未着手', 'planned': '📋 計画済', 'in_progress': '🔄 対応中', 'resolved': '✅ 解消済'}
        lines.append("## 負債一覧")
        lines.append("")
        lines.append("| ID | 内容 | 優先度 | 状態 | WBS/タスク | 解消予定 |")
        lines.append("|----|------|--------|------|------------|----------|")
        for i in items:
            desc_short = (i.get('description') or '-')[:30] + ('...' if len((i.get('description') or '')) > 30 else '')
            icon = priority_icons.get(i.get('priority', ''), '')
            status = status_labels.get(i.get('status', 'open'), i.get('status', '-'))
            ref = i.get('wbs_code') or i.get('task_id') or '-'
            lines.append(f"| {i.get('id', '-')} | {desc_short} | {icon} {i.get('priority') or '-'} | {status} | {ref} | {i.get('planned_resolution') or '-'} |")
        lines.append("")
        for i in items:
            lines.append(f"### {i.get('id', '-')}")
            lines.append("")
            lines.append(i.get('description', '-'))
            if i.get('impact'):
                lines.append("")
                lines.append(f"**影響:** {i['impact']}")
            if i.get('priority'):
                lines.append(f"**優先度:** {i['priority']}")
            if i.get('wbs_code') or i.get('task_id'):
                lines.append(f"**紐付け:** WBS={i.get('wbs_code') or '-'} / タスク={i.get('task_id') or '-'}")
            if i.get('planned_resolution'):
                lines.append(f"**解消予定:** {i['planned_resolution']}")
            if i.get('status'):
                lines.append(f"**状態:** {i['status']}")
            lines.append("")
    else:
        lines.append("## 負債一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
