#!/usr/bin/env python3
"""implementation_detail YAML → Markdown 変換（Mermaid図含む）"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'common'))
from md_base import load_yaml


def format_status(status: str) -> str:
    return {'todo': '⬜ TODO', 'wip': '🔄 WIP', 'done': '✅ Done'}.get(status, status)


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '実装詳細')}")
    lines.append("")
    lines.append(f"**タイプ:** 📝 実装詳細 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Overview
    overview = data.get('overview', {})
    if overview.get('summary'):
        lines.append("## 概要")
        lines.append("")
        lines.append(overview['summary'])
        lines.append("")
    if overview.get('related_plan'):
        lines.append(f"**関連計画:** {overview['related_plan']}")
        lines.append("")
    
    # Changes + Mermaid
    changes = data.get('changes', [])
    if changes:
        lines.append("## 変更内容")
        lines.append("")
        
        # Mermaid変更タイプ分布
        counts = {'add': 0, 'modify': 0, 'delete': 0, 'rename': 0}
        for c in changes:
            ct = c.get('change_type', 'modify')
            if ct in counts:
                counts[ct] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 変更タイプ分布")
            labels = {'add': '追加', 'modify': '変更', 'delete': '削除', 'rename': 'リネーム'}
            for t, count in counts.items():
                if count > 0:
                    lines.append(f'    "{labels[t]}" : {count}')
            lines.append("```")
            lines.append("")
        
        icons = {'add': '➕', 'modify': '✏️', 'delete': '❌', 'rename': '📝'}
        for c in changes:
            icon = icons.get(c.get('change_type', 'modify'), '•')
            lines.append(f"### {icon} `{c.get('file', '-')}`")
            lines.append("")
            if c.get('description'):
                lines.append(c['description'])
                lines.append("")
            if c.get('before'):
                lines.append("**Before:**")
                lines.append("```")
                lines.append(c['before'])
                lines.append("```")
                lines.append("")
            if c.get('after'):
                lines.append("**After:**")
                lines.append("```")
                lines.append(c['after'])
                lines.append("```")
                lines.append("")
    
    # Notes
    if data.get('notes'):
        lines.append("## メモ")
        lines.append("")
        for note in data['notes']:
            lines.append(f"- {note}")
        lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    
    data = load_yaml(args.input)
    md = generate_markdown(data)
    
    if args.output:
        Path(args.output).write_text(md, encoding='utf-8')
        print(f"✅ {args.output}")
    else:
        print(md)


if __name__ == '__main__':
    main()
