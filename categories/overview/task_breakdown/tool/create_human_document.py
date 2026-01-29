#!/usr/bin/env python3
"""task_breakdown YAML → Markdown 変換（Mermaid図含む）
overview / design / development / investigation / verification の各 ai_document.yaml の
タスク状態を集約表示する。"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from config import AI_DOCUMENT_YAML
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document

TASK_STATE_CATEGORIES = ['overview', 'design', 'development', 'investigation', 'verification']


def get_categories_dir() -> Path:
    """categories ディレクトリを返す（tool/ から doc_type を抜けて 2 段上）"""
    return Path(__file__).resolve().parent.parent.parent.parent


def collect_task_states() -> list[dict]:
    """各カテゴリの ai_document.yaml からタスク状態を収集"""
    categories_dir = get_categories_dir()
    entries = []
    for category in TASK_STATE_CATEGORIES:
        cat_dir = categories_dir / category
        if not cat_dir.is_dir():
            continue
        for doc_dir in sorted(cat_dir.iterdir()):
            if not doc_dir.is_dir():
                continue
            yaml_path = doc_dir / AI_DOCUMENT_YAML
            if not yaml_path.exists():
                continue
            try:
                data = load_yaml(str(yaml_path))
            except Exception:
                continue
            meta = data.get('meta', {})
            entry = {
                'category': category,
                'doc_type': meta.get('doc_type', doc_dir.name),
                'title': meta.get('title', yaml_path.stem),
                'status': meta.get('status', ''),
            }
            tasks = data.get('tasks', [])
            if tasks:
                entry['tasks'] = [
                    {'id': t.get('id', ''), 'title': t.get('title', ''), 'status': t.get('status', '')}
                    for t in tasks
                ]
            entries.append(entry)
    return entries


def format_task_states_section(entries: list[dict]) -> str:
    """収集したタスク状態を Markdown セクションとして整形"""
    if not entries:
        return ''
    lines = []
    lines.append('## カテゴリ別タスク状態')
    lines.append('')
    lines.append('overview / design / development / investigation / verification の各 `{}` のドキュメント状態と、'.format(AI_DOCUMENT_YAML))
    lines.append('task_breakdown のタスク一覧を表示しています。')
    lines.append('')
    for e in entries:
        cat_doc = f"{e['category']} / {e['doc_type']}"
        status_str = format_status(e['status']) if e['status'] else '-'
        lines.append(f"### {cat_doc}")
        lines.append('')
        lines.append(f"- **タイトル:** {e['title']}")
        lines.append(f"- **ドキュメント状態:** {status_str}")
        if e.get('tasks'):
            lines.append('')
            lines.append('| ID | タイトル | 状態 |')
            lines.append('|----|----------|------|')
            for t in e['tasks']:
                ts = format_status(t['status']) if t['status'] else '-'
                lines.append(f"| {t['id']} | {t['title']} | {ts} |")
        lines.append('')
    return '\n'.join(lines)


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
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    overview_section = format_overview_section(data.get('overview', {}), include_related_docs=False)
    if overview_section:
        lines.append(overview_section.rstrip())
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
    
    # カテゴリ別タスク状態（各 AI_DOCUMENT_YAML から取得）
    task_entries = collect_task_states()
    task_section = format_task_states_section(task_entries)
    if task_section:
        lines.append(task_section)
    
    ref_section = format_references_section(data)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
