#!/usr/bin/env python3
"""api_spec YAML → Markdown 変換（API仕様）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_empty_section_hint,
    format_navigation_footer,
    format_overview_section,
    format_references_section,
    format_status,
    get_doc_type_role_description,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', 'API仕様')}")
    lines.append("")
    lines.append(f"**タイプ:** 🔌 API仕様 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    overview = data.get('overview', {})
    overview_section = format_overview_section(overview, output_path=output_path)
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")
    if overview.get('base_url'):
        lines.append("**ベースURL:** " + overview['base_url'])
        lines.append("")
    if overview.get('scope') and (overview['scope'].get('in') or overview['scope'].get('out')):
        lines.append("## スコープ")
        lines.append("")
        if overview['scope'].get('in'):
            lines.append("### スコープ内")
            for item in overview['scope']['in']:
                lines.append(f"- {item}")
            lines.append("")
        if overview['scope'].get('out'):
            lines.append("### スコープ外")
            for item in overview['scope']['out']:
                lines.append(f"- {item}")
            lines.append("")

    endpoints = data.get('endpoints', [])
    if endpoints:
        lines.append("## エンドポイント一覧")
        lines.append("")
        lines.append("| メソッド | パス | 説明 | 要件参照 |")
        lines.append("|---------|------|------|----------|")
        for e in endpoints:
            desc = (e.get('description') or '-')[:40] + ('...' if len((e.get('description') or '')) > 40 else '')
            refs = ', '.join(e.get('requirements_ref') or []) or '-'
            lines.append(f"| {e.get('method', '-')} | {e.get('path', '-')} | {desc} | {refs} |")
        lines.append("")
        for e in endpoints:
            lines.append(f"### {e.get('method', '-')} {e.get('path', '-')}")
            lines.append("")
            lines.append(e.get('description', ''))
            if e.get('request_body'):
                lines.append("")
                lines.append("**リクエスト:** " + e['request_body'])
            if e.get('response'):
                lines.append("**レスポンス:** " + e['response'])
            if e.get('requirements_ref'):
                lines.append("**要件参照:** " + ', '.join(e['requirements_ref']))
            lines.append("")
    else:
        lines.append("## エンドポイント一覧")
        lines.append("")
        lines.append(format_empty_section_hint("endpoints"))
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
