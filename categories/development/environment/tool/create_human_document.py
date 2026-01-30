#!/usr/bin/env python3
"""environment YAML → Markdown 変換（環境・インフラ）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_empty_section_hint,
    format_navigation_footer,
    format_references_section,
    format_status,
    get_doc_type_role_description,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', '環境・インフラ')}")
    lines.append("")
    lines.append(f"**タイプ:** 🖥 環境・インフラ | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    type_labels = {'local': 'ローカル', 'dev': '開発', 'staging': 'ステージング', 'production': '本番', 'other': 'その他'}
    envs = data.get('environments', [])
    if envs:
        lines.append("## 環境一覧")
        lines.append("")
        lines.append("| ID | 名前 | 種別 | URL | デプロイ先 |")
        lines.append("|----|------|------|-----|------------|")
        for e in envs:
            typ = type_labels.get(e.get('type'), e.get('type') or '-')
            lines.append(f"| {e.get('id', '-')} | {e.get('name', '-')} | {typ} | {e.get('url') or '-'} | {e.get('deploy_target') or '-'} |")
        lines.append("")
        for e in envs:
            if e.get('cicd') or e.get('secrets_policy') or e.get('notes'):
                lines.append(f"### {e.get('id', '-')}: {e.get('name', '')}")
                lines.append("")
                if e.get('cicd'):
                    lines.append("**CI/CD:** " + e['cicd'])
                    lines.append("")
                if e.get('secrets_policy'):
                    lines.append("**シークレット方針:** " + e['secrets_policy'])
                    lines.append("")
                if e.get('notes'):
                    lines.append(e['notes'])
                    lines.append("")
    else:
        lines.append("## 環境一覧")
        lines.append("")
        lines.append(format_empty_section_hint("environments"))
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
