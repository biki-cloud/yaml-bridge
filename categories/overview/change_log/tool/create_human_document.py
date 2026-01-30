#!/usr/bin/env python3
"""change_log YAML → Markdown 変換（変更履歴）"""

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

    lines.append(f"# {meta.get('title', '変更履歴')}")
    lines.append("")
    lines.append(f"**タイプ:** 📝 変更履歴 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    lines.append("**この doc_type の役割:** スコープ・計画・体制の変更履歴を記録する。いつ・何を・なぜ変更したか、承認有無を残す。本番リリースの日時・バージョン・変更内容は [リリースログ](../../release_log/human/document.md) を参照する。")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    changes = data.get('changes', [])
    if changes:
        lines.append("## 変更一覧")
        lines.append("")
        lines.append("| ID | 日付 | 概要 | スコープ変更 | スケジュール変更 | 承認者 |")
        lines.append("|----|------|------|--------------|------------------|--------|")
        for c in changes:
            scope = "✓" if c.get('scope_change') else "-"
            sched = "✓" if c.get('schedule_change') else "-"
            summary_short = (c.get('summary') or '-')[:40] + ('...' if len((c.get('summary') or '')) > 40 else '')
            lines.append(f"| {c.get('id', '-')} | {c.get('date', '-')} | {summary_short} | {scope} | {sched} | {c.get('approved_by') or '-'} |")
        lines.append("")
        for c in changes:
            lines.append(f"### {c.get('id', '-')}: {c.get('date', '')} - {c.get('summary', '')}")
            lines.append("")
            if c.get('detail'):
                lines.append(c['detail'])
                lines.append("")
            if c.get('scope_change') or c.get('schedule_change'):
                tags = []
                if c.get('scope_change'):
                    tags.append("スコープ変更")
                if c.get('schedule_change'):
                    tags.append("スケジュール変更")
                lines.append(f"**種別:** {', '.join(tags)}")
            if c.get('approved_by'):
                lines.append(f"**承認者:** {c['approved_by']}")
            lines.append("")
    else:
        lines.append("## 変更一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
