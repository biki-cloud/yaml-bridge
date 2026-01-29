#!/usr/bin/env python3
"""implementation_result YAML → Markdown 変換（Mermaid図含む）"""

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
    
    lines.append(f"# {meta.get('title', '修正結果')}")
    lines.append("")
    lines.append(f"**タイプ:** ✅ 修正結果 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Overview
    overview = data.get('overview', {})
    if overview.get('related_plan'):
        lines.append(f"**関連計画:** {overview['related_plan']}")
    if overview.get('related_pr'):
        lines.append(f"**関連PR:** {overview['related_pr']}")
    if overview:
        lines.append("")
    
    # Result + Mermaid
    result = data.get('result', {})
    if result:
        lines.append("## 修正結果")
        lines.append("")
        
        # Mermaid変更量
        if result.get('lines_added') or result.get('lines_deleted'):
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 変更行数")
            if result.get('lines_added'):
                lines.append(f'    "追加" : {result["lines_added"]}')
            if result.get('lines_deleted'):
                lines.append(f'    "削除" : {result["lines_deleted"]}')
            lines.append("```")
            lines.append("")
        
        if result.get('summary'):
            lines.append(result['summary'])
            lines.append("")
        
        stats = []
        if result.get('files_changed'):
            stats.append(f"**変更ファイル:** {result['files_changed']}")
        if result.get('lines_added'):
            stats.append(f"**追加行:** +{result['lines_added']}")
        if result.get('lines_deleted'):
            stats.append(f"**削除行:** -{result['lines_deleted']}")
        if stats:
            lines.append(" | ".join(stats))
            lines.append("")
        
        if result.get('commits'):
            lines.append("### コミット履歴")
            lines.append("")
            for c in result['commits']:
                lines.append(f"- `{c.get('hash', '-')[:7]}` {c.get('message', '-')}")
            lines.append("")
    
    # Issues found
    if data.get('issues_found'):
        lines.append("## 発見した問題")
        lines.append("")
        for issue in data['issues_found']:
            lines.append(f"### {issue.get('description', '-')}")
            lines.append("")
            if issue.get('resolution'):
                lines.append(f"**解決方法:** {issue['resolution']}")
                lines.append("")
    
    # Lessons learned
    if data.get('lessons_learned'):
        lines.append("## 学び")
        lines.append("")
        for lesson in data['lessons_learned']:
            lines.append(f"- {lesson}")
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
