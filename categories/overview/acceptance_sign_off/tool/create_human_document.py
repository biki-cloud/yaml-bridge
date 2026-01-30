#!/usr/bin/env python3
"""acceptance_sign_off YAML → Markdown 変換（受入・サインオフ）"""

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

    lines.append(f"# {meta.get('title', '受入・サインオフ')}")
    lines.append("")
    lines.append(f"**タイプ:** ✅ 受入・サインオフ | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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

    sign_offs = data.get('sign_offs', [])
    if sign_offs:
        lines.append("## 受入・サインオフ一覧")
        lines.append("")
        lines.append("| ID | 対象種別 | タイトル | 承認者 | 承認日 | 条件充足 |")
        lines.append("|----|----------|----------|--------|--------|----------|")
        for s in sign_offs:
            scope = s.get('scope', '-')
            cond = "✓" if s.get('conditions_met') is True else ("✗" if s.get('conditions_met') is False else "-")
            lines.append(f"| {s.get('id', '-')} | {scope} | {(s.get('title') or '-')[:30]} | {s.get('approved_by') or '-'} | {s.get('approved_at') or '-'} | {cond} |")
        lines.append("")
        for s in sign_offs:
            lines.append(f"### {s.get('id', '-')}: {s.get('title', '')}")
            lines.append("")
            if s.get('acceptance_criteria'):
                lines.append("**受入基準:**")
                for c in s['acceptance_criteria']:
                    lines.append(f"- {c}")
                lines.append("")
            if s.get('approved_by') or s.get('approved_at'):
                lines.append(f"**承認:** {s.get('approved_by') or '-'} / {s.get('approved_at') or '-'}")
                lines.append("")
            if s.get('conditions_met') is not None:
                lines.append(f"**条件充足:** {'はい' if s['conditions_met'] else 'いいえ'}")
                lines.append("")
            if s.get('notes'):
                lines.append(f"**備考:** {s['notes']}")
                lines.append("")
            if s.get('related_docs'):
                lines.append("**関連資料:**")
                for rd in s['related_docs']:
                    lines.append(f"- [{rd.get('title', '-')}]({rd.get('url', '')})")
                lines.append("")
    else:
        lines.append("## 受入・サインオフ一覧")
        lines.append("")
        lines.append(format_empty_section_hint("sign_offs"))
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
