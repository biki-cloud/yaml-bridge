#!/usr/bin/env python3
"""project_summary YAML → Markdown 変換（Mermaid図含む）
overview ビルド時に design / development / investigation / verification の
各 ai_handled.yaml のタスク状態を取得して表示する。"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'common'))
from md_base import load_yaml

# タスク状態を集約するカテゴリ（task_breakdown は design 内の doc_type のひとつ）
TASK_STATE_CATEGORIES = ['design', 'development', 'investigation', 'verification']


def get_categories_dir() -> Path:
    """categories ディレクトリを返す（overview/project_summary から 2 段上）"""
    return Path(__file__).resolve().parent.parent.parent


def collect_task_states() -> list[dict]:
    """design, development, investigation, verification の各 ai_handled.yaml からタスク状態を収集"""
    categories_dir = get_categories_dir()
    entries = []
    for category in TASK_STATE_CATEGORIES:
        cat_dir = categories_dir / category
        if not cat_dir.is_dir():
            continue
        for doc_dir in sorted(cat_dir.iterdir()):
            if not doc_dir.is_dir():
                continue
            yaml_path = doc_dir / 'ai_handled.yaml'
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
    lines.append('design / development / investigation / verification の各 `ai_handled.yaml` のドキュメント状態と、')
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
    
    # ヘッダー
    lines.append(f"# {meta.get('title', 'プロジェクト概要')}")
    lines.append("")
    lines.append(f"**ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Summary
    summary = data.get('summary', {})
    lines.append("## 背景")
    lines.append("")
    lines.append(summary.get('background', '-'))
    lines.append("")
    
    lines.append("## ゴール")
    lines.append("")
    lines.append(summary.get('goal', '-'))
    lines.append("")
    
    if summary.get('scope'):
        scope = summary['scope']
        lines.append("## スコープ")
        lines.append("")
        if scope.get('in'):
            lines.append("### スコープ内")
            for item in scope['in']:
                lines.append(f"- {item}")
            lines.append("")
        if scope.get('out'):
            lines.append("### スコープ外")
            for item in scope['out']:
                lines.append(f"- {item}")
            lines.append("")
    
    if summary.get('success_criteria'):
        lines.append("## 成功基準")
        lines.append("")
        for i, c in enumerate(summary['success_criteria'], 1):
            lines.append(f"{i}. {c}")
        lines.append("")
    
    # Stakeholders
    if data.get('stakeholders'):
        lines.append("## ステークホルダー")
        lines.append("")
        lines.append("| 名前 | 役割 | 連絡先 |")
        lines.append("|------|------|--------|")
        for sh in data['stakeholders']:
            lines.append(f"| {sh.get('name', '-')} | {sh.get('role', '-')} | {sh.get('contact', '-')} |")
        lines.append("")
    
    # Timeline + Mermaid
    if data.get('timeline'):
        tl = data['timeline']
        lines.append("## タイムライン")
        lines.append("")
        if tl.get('start_date') or tl.get('end_date'):
            lines.append(f"**期間:** {tl.get('start_date', '-')} ~ {tl.get('end_date', '-')}")
            lines.append("")
        
        if tl.get('milestones'):
            # Mermaid Gantt
            lines.append("```mermaid")
            lines.append("gantt")
            lines.append("    title プロジェクトタイムライン")
            lines.append("    dateFormat YYYY-MM-DD")
            lines.append("    section マイルストーン")
            for ms in tl['milestones']:
                name = ms.get('name', 'MS')
                date = ms.get('date', '2024-01-01')
                lines.append(f"    {name} : milestone, {date}, 1d")
            lines.append("```")
            lines.append("")
            
            lines.append("| マイルストーン | 日付 | 説明 |")
            lines.append("|---------------|------|------|")
            for ms in tl['milestones']:
                lines.append(f"| {ms.get('name', '-')} | {ms.get('date', '-')} | {ms.get('description', '-')} |")
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
    
    # Risks + Mermaid
    if data.get('risks'):
        lines.append("## リスク")
        lines.append("")
        
        # Mermaid pie chart
        counts = {'high': 0, 'medium': 0, 'low': 0}
        for r in data['risks']:
            impact = r.get('impact', 'medium')
            if impact in counts:
                counts[impact] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title リスク影響度分布")
            for level, count in counts.items():
                if count > 0:
                    labels = {'high': '高', 'medium': '中', 'low': '低'}
                    lines.append(f'    "{labels[level]}" : {count}')
            lines.append("```")
            lines.append("")
        
        impact_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines.append("| リスク | 影響度 | 対策 |")
        lines.append("|--------|--------|------|")
        for r in data['risks']:
            icon = impact_icons.get(r.get('impact', ''), '')
            lines.append(f"| {r.get('risk', '-')} | {icon} {r.get('impact', '-')} | {r.get('mitigation', '-')} |")
        lines.append("")
    
    # References
    if data.get('references'):
        lines.append("## 参考資料")
        lines.append("")
        for ref in data['references']:
            if ref.get('url'):
                lines.append(f"- [{ref.get('title', '-')}]({ref['url']})")
            else:
                lines.append(f"- {ref.get('title', '-')}")
        lines.append("")
    
    # カテゴリ別タスク状態（design, development, investigation, verification の ai_handled.yaml から取得）
    task_entries = collect_task_states()
    task_section = format_task_states_section(task_entries)
    if task_section:
        lines.append(task_section)
    
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
