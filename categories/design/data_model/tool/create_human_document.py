#!/usr/bin/env python3
"""data_model YAML → Markdown 変換（データモデル）"""

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


def _mermaid_sanitize_id(raw: str) -> str:
    if not raw:
        return 'n'
    s = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(raw))
    return s or 'n'


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', 'データモデル')}")
    lines.append("")
    lines.append(f"**タイプ:** 📊 データモデル | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    overview = data.get('overview', {}) or {}
    if not (overview.get('background') or overview.get('goal')):
        overview = {
            **overview,
            'background': overview.get('background') or '本システムで扱うエンティティとその関係を定義する。',
            'goal': overview.get('goal') or '要件・アーキテクチャと整合したデータ構造を明文化する。',
        }
    overview_section = format_overview_section(overview, output_path=output_path)
    if overview_section:
        lines.append(overview_section.rstrip())
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

    entities = data.get('entities', [])
    if entities:
        lines.append("## エンティティ一覧")
        lines.append("")
        lines.append("| ID | 名前 | 説明 |")
        lines.append("|----|------|------|")
        for e in entities:
            desc = (e.get('description') or '-')[:50] + ('...' if len((e.get('description') or '')) > 50 else '')
            lines.append(f"| {e.get('id', '-')} | {e.get('name', '-')} | {desc} |")
        lines.append("")

        for e in entities:
            lines.append(f"### {e.get('id', '-')}: {e.get('name', '')}")
            lines.append("")
            if e.get('description'):
                lines.append(e['description'])
                lines.append("")
            attrs = e.get('attributes') or []
            if attrs:
                lines.append("| 属性 | 型 | PK | NULL |")
                lines.append("|------|-----|----|------|")
                for a in attrs:
                    pk = '✓' if a.get('primary_key') else '-'
                    nul = '✓' if a.get('nullable') else '-'
                    lines.append(f"| {a.get('name', '-')} | {a.get('type', '-')} | {pk} | {nul} |")
                lines.append("")
            rels = e.get('relations') or []
            if rels:
                lines.append("**関連:**")
                for r in rels:
                    lines.append(f"- {r.get('relation_type', '-')} → {r.get('target_entity_id', '-')} " + (r.get('description') or ''))
                lines.append("")
    else:
        lines.append("## エンティティ一覧")
        lines.append("")
        lines.append(format_empty_section_hint("entities"))
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
