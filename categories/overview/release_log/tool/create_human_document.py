#!/usr/bin/env python3
"""release_log YAML → Markdown 変換（リリースログ）"""

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

    lines.append(f"# {meta.get('title', 'リリースログ')}")
    lines.append("")
    lines.append(f"**タイプ:** 🚀 リリースログ | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    lines.append("**この doc_type の役割:** 本番リリースの日時・バージョン・変更内容を記録する。プロジェクトのスコープ・計画・体制の変更履歴は [プロジェクト変更履歴](../../change_log/human/document.md) を参照する。")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    releases = data.get('releases', [])
    if releases:
        lines.append("## リリース一覧")
        lines.append("")
        lines.append("| ID | 日付 | 環境 | バージョン | 概要 | リリース担当 |")
        lines.append("|----|------|------|------------|------|--------------|")
        for r in releases:
            summary_short = (r.get('summary') or '-')[:35] + ('...' if len((r.get('summary') or '')) > 35 else '')
            lines.append(f"| {r.get('id', '-')} | {r.get('date', '-')} | {r.get('environment') or '-'} | {r.get('version') or '-'} | {summary_short} | {r.get('released_by') or '-'} |")
        lines.append("")
        for r in releases:
            lines.append(f"### {r.get('id', '-')}: {r.get('date', '')} - {r.get('summary', '')}")
            lines.append("")
            if r.get('environment'):
                lines.append(f"**環境:** {r['environment']}")
            if r.get('version'):
                lines.append(f"**バージョン:** {r['version']}")
            if r.get('detail'):
                lines.append("")
                lines.append(r['detail'])
            if r.get('released_by'):
                lines.append("")
                lines.append(f"**リリース担当:** {r['released_by']}")
            if r.get('rollback_notes'):
                lines.append("")
                lines.append(f"**ロールバック時の注意:** {r['rollback_notes']}")
            if r.get('related_pr'):
                lines.append("")
                lines.append(f"**関連 PR:** {r['related_pr']}")
            lines.append("")
    else:
        lines.append("## リリース一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
