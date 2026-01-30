#!/usr/bin/env python3
"""investigation_summary YAML → Markdown 変換（調査サマリ・結論・設計へのインプット）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    load_yaml,
    format_status,
    format_references_section,
    format_ai_context_section,
    format_overview_section,
    _ref_url_for_markdown,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})
    title = meta.get('title', '調査サマリ')

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 調査サマリ | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    overview_section = format_overview_section(data.get('overview', {}), output_path=output_path)
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")

    lines.append("**この doc_type の役割:** 調査フェーズの結論・推奨・「やる／やらない」を一箇所で示す。複数の code_understanding / domain_knowledge / related_code_research を総括し、設計・実装へのインプットを明示する。")
    lines.append("")
    lines.append("## 概要・総括")
    lines.append("")
    summary = data.get('summary', '')
    lines.append(summary if summary else "（調査の概要・総括を記述してください）")
    lines.append("")

    conclusions = data.get('conclusions', [])
    if conclusions:
        lines.append("## 結論")
        lines.append("")
        for c in conclusions:
            lines.append(f"- {c}")
        lines.append("")

    recommendations = data.get('recommendations', [])
    if recommendations:
        lines.append("## 推奨事項")
        lines.append("")
        icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        for r in recommendations:
            pri = icons.get(r.get('priority', ''), '')
            lines.append(f"- {pri} {r.get('item', '-')}")
        lines.append("")

    inputs_to_design = data.get('inputs_to_design', [])
    if inputs_to_design:
        lines.append("## 設計フェーズへのインプット")
        lines.append("")
        for i in inputs_to_design:
            lines.append(f"- {i}")
        lines.append("")

    related = data.get('related_investigation_docs', [])
    if related:
        lines.append("## 参照した調査ドキュメント")
        lines.append("")
        for doc in related:
            url = doc.get('path_or_url', '')
            if output_path and url and not url.startswith(('http', 'file')):
                link = _ref_url_for_markdown(url, output_path)
            else:
                link = url
            title = doc.get('title', '-')
            doc_type = doc.get('doc_type', '')
            suffix = f"（{doc_type}）" if doc_type else ""
            lines.append(f"- [{title}]({link}){suffix}")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
