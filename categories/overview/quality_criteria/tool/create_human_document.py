#!/usr/bin/env python3
"""quality_criteria YAML → Markdown 変換（品質・受入基準）"""

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

    lines.append(f"# {meta.get('title', '品質・受入基準')}")
    lines.append("")
    lines.append(f"**タイプ:** ✅ 品質・受入基準 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    criteria = data.get('criteria', [])
    if criteria:
        priority_labels = {'must': '必須', 'should': '推奨', 'optional': '任意'}
        lines.append("## 基準一覧")
        lines.append("")
        lines.append("| ID | タイトル | 優先度 | 適用範囲 |")
        lines.append("|----|----------|--------|----------|")
        for c in criteria:
            pri = priority_labels.get(c.get('priority'), c.get('priority') or '-')
            lines.append(f"| {c.get('id', '-')} | {(c.get('title') or '-')[:40]} | {pri} | {c.get('scope') or '-'} |")
        lines.append("")
        for c in criteria:
            lines.append(f"### {c.get('id', '-')}: {c.get('title', '')}")
            lines.append("")
            if c.get('description'):
                lines.append(c['description'])
                lines.append("")
            if c.get('priority'):
                lines.append(f"**優先度:** {priority_labels.get(c['priority'], c['priority'])}")
                lines.append("")
            if c.get('related_docs'):
                lines.append("**関連資料:**")
                for rd in c['related_docs']:
                    lines.append(f"- [{rd.get('title', '-')}]({rd.get('url', '')})")
                lines.append("")
    else:
        lines.append("## 基準一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
