#!/usr/bin/env python3
"""architecture YAML → Markdown 変換（アーキテクチャ・コンポーネント構成）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_overview_section,
    format_references_section,
    format_status,
    run_create_human_document,
    load_yaml,
)


def _mermaid_sanitize_id(raw: str) -> str:
    if not raw:
        return 'n'
    s = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(raw))
    return s or 'n'


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', 'アーキテクチャ')}")
    lines.append("")
    lines.append(f"**タイプ:** 🏗 アーキテクチャ | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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
    if overview.get('scope'):
        scope = overview['scope']
        if scope.get('in') or scope.get('out'):
            lines.append("## スコープ")
            lines.append("")
            if scope.get('in'):
                lines.append("### スコープ内")
                for item in scope['in']:
                    lines.append(f"- {item}")
                lines.append("")
            if scope.get('out'):
                lines.append("### スコープ外")
                for item in scope['out']:
                    lines.append(f"- {item}")
                lines.append("")

    components = data.get('components', [])
    if components:
        lines.append("## コンポーネント一覧")
        lines.append("")
        lines.append("| ID | 名前 | 責務 |")
        lines.append("|----|------|------|")
        for c in components:
            resp = (c.get('responsibility') or '-')[:50] + ('...' if len((c.get('responsibility') or '')) > 50 else '')
            lines.append(f"| {c.get('id', '-')} | {c.get('name', '-')} | {resp} |")
        lines.append("")

        # Mermaid flowchart: components and dependencies
        if any(c.get('depends_on') for c in components):
            lines.append("```mermaid")
            lines.append("flowchart LR")
            for c in components:
                nid = _mermaid_sanitize_id(c.get('id', ''))
                name = (c.get('name') or c.get('id', '')).replace('"', '\\"')[:30]
                lines.append(f'    {nid}["{name}"]')
            for c in components:
                nid = _mermaid_sanitize_id(c.get('id', ''))
                for dep in c.get('depends_on') or []:
                    dep_id = _mermaid_sanitize_id(dep)
                    lines.append(f"    {dep_id} --> {nid}")
            lines.append("```")
            lines.append("")

        for c in components:
            lines.append(f"### {c.get('id', '-')}: {c.get('name', '')}")
            lines.append("")
            if c.get('description'):
                lines.append(c['description'])
                lines.append("")
            if c.get('responsibility'):
                lines.append(f"**責務:** {c['responsibility']}")
            if c.get('depends_on'):
                lines.append(f"**依存:** {', '.join(c['depends_on'])}")
            lines.append("")
    else:
        lines.append("## コンポーネント一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
