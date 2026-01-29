#!/usr/bin/env python3
"""task_breakdown YAML → Markdown 変換（Mermaid図含む）"""

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
    
    lines.append(f"# {meta.get('title', 'タスク分解')}")
    lines.append("")
    lines.append(f"**タイプ:** 📝 タスク分解 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Overview
    overview = data.get('overview', {})
    if overview.get('background'):
        lines.append("## 背景")
        lines.append("")
        lines.append(overview['background'])
        lines.append("")
    
    if overview.get('goal'):
        lines.append("## 目的")
        lines.append("")
        lines.append(overview['goal'])
        lines.append("")
    
    # Tasks + Mermaid
    tasks = data.get('tasks', [])
    if tasks:
        lines.append("## タスク一覧")
        lines.append("")
        
        # Mermaid進捗分布
        status_counts = {'todo': 0, 'wip': 0, 'done': 0}
        category_counts = {'investigation': 0, 'design': 0, 'development': 0, 'verification': 0}
        for t in tasks:
            s = t.get('status', 'todo')
            if s in status_counts:
                status_counts[s] += 1
            c = t.get('category', 'development')
            if c in category_counts:
                category_counts[c] += 1
        
        if sum(status_counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title タスク進捗")
            labels = {'todo': 'TODO', 'wip': 'WIP', 'done': 'Done'}
            for s, count in status_counts.items():
                if count > 0:
                    lines.append(f'    "{labels[s]}" : {count}')
            lines.append("```")
            lines.append("")
        
        if sum(category_counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title タスクカテゴリ分布")
            labels = {'investigation': '調査', 'design': '設計', 'development': '開発', 'verification': '動作確認'}
            for c, count in category_counts.items():
                if count > 0:
                    lines.append(f'    "{labels[c]}" : {count}')
            lines.append("```")
            lines.append("")
        
        # 依存関係図
        tasks_with_deps = [t for t in tasks if t.get('dependencies')]
        if tasks_with_deps:
            lines.append("```mermaid")
            lines.append("flowchart LR")
            task_ids = {t.get('id'): t for t in tasks if t.get('id')}
            for task in tasks[:10]:
                tid = task.get('id', '')
                title_short = task.get('title', '')[:12]
                lines.append(f'    {tid}["{tid}: {title_short}"]')
                for dep in task.get('dependencies', []):
                    if dep in task_ids:
                        lines.append(f"    {dep} --> {tid}")
            lines.append("```")
            lines.append("")
        
        status_icons = {'todo': '⬜', 'wip': '🔄', 'done': '✅'}
        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        category_labels = {
            'investigation': '調査',
            'design': '設計',
            'development': '開発',
            'verification': '動作確認'
        }
        
        lines.append("| ID | タスク | カテゴリ | 優先度 | ステータス | 見積(h) |")
        lines.append("|----|--------|----------|--------|----------|---------|")
        for task in tasks:
            status = status_icons.get(task.get('status', ''), '') + ' ' + task.get('status', '-')
            priority = priority_icons.get(task.get('priority', ''), '') + ' ' + task.get('priority', '-')
            category = category_labels.get(task.get('category', ''), task.get('category', '-'))
            hours = task.get('estimated_hours', '-')
            lines.append(f"| {task.get('id', '-')} | {task.get('title', '-')} | {category} | {priority} | {status} | {hours} |")
        lines.append("")
        
        # Task details
        for task in tasks:
            if task.get('description') or task.get('dependencies'):
                lines.append(f"### {task.get('id', '-')}: {task.get('title', '-')}")
                lines.append("")
                if task.get('description'):
                    lines.append(task['description'])
                    lines.append("")
                if task.get('dependencies'):
                    lines.append(f"**依存:** {', '.join(task['dependencies'])}")
                    lines.append("")
    
    # Constraints
    if data.get('constraints'):
        lines.append("## 制約条件")
        lines.append("")
        icons = {'technical': '🔧', 'business': '💼', 'resource': '👥', 'time': '⏰'}
        for c in data['constraints']:
            icon = icons.get(c.get('type', ''), '•')
            lines.append(f"- {icon} **{c.get('type', '-')}**: {c.get('description', '-')}")
        lines.append("")
    
    # Risks
    if data.get('risks'):
        lines.append("## リスク")
        lines.append("")
        impact_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines.append("| リスク | 影響度 | 対策 |")
        lines.append("|--------|--------|------|")
        for r in data['risks']:
            icon = impact_icons.get(r.get('impact', ''), '')
            lines.append(f"| {r.get('risk', '-')} | {icon} {r.get('impact', '-')} | {r.get('mitigation', '-')} |")
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
