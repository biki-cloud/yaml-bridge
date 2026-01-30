#!/usr/bin/env python3
"""lessons_learned YAML → Markdown 変換（振り返り・教訓）"""

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

    lines.append(f"# {meta.get('title', '振り返り・教訓')}")
    lines.append("")
    lines.append(f"**タイプ:** 📝 振り返り・教訓 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    lessons = data.get('lessons', [])
    if lessons:
        lines.append("## 振り返り一覧")
        lines.append("")
        for L in lessons:
            lines.append(f"### {L.get('phase', '-')}")
            if L.get('held_at'):
                lines.append(f"**実施日:** {L['held_at']}")
            lines.append("")
            if L.get('what_worked'):
                lines.append("**うまくいったこと:**")
                for w in L['what_worked']:
                    lines.append(f"- {w}")
                lines.append("")
            if L.get('what_didnt'):
                lines.append("**うまくいかなかったこと:**")
                for w in L['what_didnt']:
                    lines.append(f"- {w}")
                lines.append("")
            if L.get('action_items'):
                lines.append("**次に活かすアクション:**")
                for a in L['action_items']:
                    lines.append(f"- {a}")
                lines.append("")
            if L.get('notes'):
                lines.append(L['notes'])
                lines.append("")
    else:
        lines.append("## 振り返り一覧")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
