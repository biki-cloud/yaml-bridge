#!/usr/bin/env python3
"""WBS YAML → Markdown 変換（Mermaid図・進捗計算・マイルストーン含む）
overview / design / development / investigation / verification の各 ai_document.yaml の
タスク状態を集約表示する。WBS は wbs_elements から進捗・マイルストーン・ゴール状況を算出する。"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from config import AI_DOCUMENT_YAML
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document

TASK_STATE_CATEGORIES = ['overview', 'design', 'development', 'investigation', 'verification']


def get_categories_dir() -> Path:
    """categories ディレクトリを返す（tool/ から doc_type を抜けて 2 段上）"""
    return Path(__file__).resolve().parent.parent.parent.parent


def _wbs_code_sort_key(wbs_code: str) -> tuple:
    """wbs_code をソート用タプルに変換（1, 1.1, 1.1.1 の順）"""
    if not wbs_code:
        return (0,)
    parts = [int(x) if x.isdigit() else 0 for x in re.split(r'[.\s]+', str(wbs_code)) if x]
    return tuple(parts)


def _progress_from_elements(elements: list[dict]) -> tuple[float, float, int, int, float, float]:
    """type が task または milestone の要素から進捗を算出。
    返却: (task_pct, hours_pct, done_count, total_count, done_hours, total_hours)"""
    work = [e for e in elements if e.get('type') in ('task', 'milestone')]
    if not work:
        return 0.0, 0.0, 0, 0, 0.0, 0.0
    total_count = len(work)
    done_count = sum(1 for e in work if e.get('status') == 'done')
    total_hours = sum(float(e.get('estimated_hours') or 0) for e in work)
    done_hours = sum(float(e.get('estimated_hours') or 0) for e in work if e.get('status') == 'done')
    task_pct = (done_count / total_count * 100) if total_count else 0.0
    hours_pct = (done_hours / total_hours * 100) if total_hours else 0.0
    return task_pct, hours_pct, done_count, total_count, done_hours, total_hours


def collect_task_states() -> list[dict]:
    """各カテゴリの ai_document.yaml からタスク状態を収集（tasks または wbs_elements）"""
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
            wbs_elements = data.get('wbs_elements', [])
            if tasks:
                entry['tasks'] = [
                    {'id': t.get('id', ''), 'title': t.get('title', ''), 'status': t.get('status', '')}
                    for t in tasks
                ]
            elif wbs_elements:
                entry['tasks'] = [
                    {'id': e.get('id', ''), 'title': e.get('title', ''), 'status': e.get('status', '')}
                    for e in wbs_elements if e.get('type') in ('task', 'milestone')
                ]
            entries.append(entry)
    return entries


def collect_category_tasks() -> list[dict]:
    """各カテゴリの doc_type: tasks から詳細タスクを収集（WBS で集約表示用）"""
    categories_dir = get_categories_dir()
    entries = []
    for category in TASK_STATE_CATEGORIES:
        if category == 'overview':
            continue
        tasks_dir = categories_dir / category / 'tasks'
        yaml_path = tasks_dir / 'ai' / 'document.yaml'
        if not yaml_path.exists():
            continue
        try:
            data = load_yaml(str(yaml_path))
        except Exception:
            continue
        meta = data.get('meta', {})
        tasks = data.get('tasks', [])
        entries.append({
            'category': category,
            'title': meta.get('title', ''),
            'status': meta.get('status', ''),
            'tasks': [
                {'id': t.get('id', ''), 'title': t.get('title', ''), 'wbs_code': t.get('wbs_code', ''), 'status': t.get('status', ''), 'estimated_hours': t.get('estimated_hours')}
                for t in tasks
            ]
        })
    return entries


def format_category_tasks_section(entries: list[dict]) -> str:
    """カテゴリ別詳細タスク（doc_type: tasks）を Markdown セクションとして整形"""
    if not entries:
        return ''
    lines = []
    lines.append('## カテゴリ別詳細タスク')
    lines.append('')
    lines.append('各カテゴリの `tasks` doc_type から読み込んだ詳細タスク一覧（WBS の wbs_code で紐付け）。')
    lines.append('')
    for e in entries:
        cat = e['category']
        status_str = format_status(e['status']) if e['status'] else '-'
        lines.append(f"### {cat} / tasks")
        lines.append('')
        lines.append(f"- **タイトル:** {e['title']}")
        lines.append(f"- **ドキュメント状態:** {status_str}")
        if e.get('tasks'):
            lines.append('')
            lines.append('| ID | WBS | タスク | ステータス | 見積(h) |')
            lines.append('|----|-----|--------|----------|---------|')
            for t in sorted(e['tasks'], key=lambda x: _wbs_code_sort_key(x.get('wbs_code') or '')):
                ts = format_status_display(t.get('status', ''))
                lines.append(f"| {t.get('id', '-')} | {t.get('wbs_code') or '-'} | {t.get('title', '-')} | {ts} | {t.get('estimated_hours', '-')} |")
        lines.append('')
    return '\n'.join(lines)


def format_task_states_section(entries: list[dict]) -> str:
    """収集したタスク状態を Markdown セクションとして整形"""
    if not entries:
        return ''
    lines = []
    lines.append('## カテゴリ別タスク状態')
    lines.append('')
    lines.append('overview / design / development / investigation / verification の各 `{}` のドキュメント状態と、'.format(AI_DOCUMENT_YAML))
    lines.append('WBS のタスク一覧を表示しています。')
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


def format_status_display(status: str) -> str:
    return {'todo': '⬜ TODO', 'wip': '🔄 WIP', 'done': '✅ Done'}.get(status, status)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})
    overview = data.get('overview', {})
    elements = data.get('wbs_elements', [])

    lines.append(f"# {meta.get('title', 'WBS（作業分解構成）')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 WBS（作業分解構成） | **ステータス:** {format_status_display(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    overview_section = format_overview_section(overview, include_related_docs=False, output_path=output_path)
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")

    # --- ゴールまでの状況・進捗サマリ ---
    task_pct, hours_pct, done_count, total_count, done_hours, total_hours = _progress_from_elements(elements)
    lines.append("## ゴールまでの状況")
    lines.append("")
    if overview.get('goal'):
        lines.append(overview['goal'].strip())
        lines.append("")
    lines.append(f"- **全体進捗（タスク数）:** {done_count}/{total_count} タスク = **{task_pct:.0f}%**")
    if total_hours > 0:
        lines.append(f"- **全体進捗（工数）:** {done_hours:.0f}/{total_hours:.0f}h = **{hours_pct:.0f}%**")
    remaining = [e for e in elements if e.get('type') in ('task', 'milestone') and e.get('status') != 'done']
    if remaining:
        lines.append("")
        lines.append("**残タスク:** " + ", ".join(e.get('id') or e.get('title', '') for e in remaining[:15]))
        if len(remaining) > 15:
            lines.append(f" …他 {len(remaining) - 15} 件")
    lines.append("")
    # プログレスバー（テキスト）
    bar_len = 20
    filled = int(bar_len * task_pct / 100) if task_pct <= 100 else bar_len
    lines.append(f"進捗: `{'█' * filled}{'░' * (bar_len - filled)}` {task_pct:.0f}%")
    lines.append("")

    # --- マイルストーン一覧 ---
    milestones = [e for e in elements if e.get('type') == 'milestone']
    if milestones:
        lines.append("## マイルストーン一覧")
        lines.append("")
        lines.append("| ID | タイトル | 目標日 | 状態 |")
        lines.append("|----|----------|--------|------|")
        for m in sorted(milestones, key=lambda x: _wbs_code_sort_key(x.get('wbs_code', ''))):
            lines.append(f"| {m.get('id', '-')} | {m.get('title', '-')} | {m.get('target_date', '-')} | {format_status_display(m.get('status', '-'))} |")
        lines.append("")

    # --- WBS ツリー ---
    if elements:
        lines.append("## WBS ツリー")
        lines.append("")
        sorted_elements = sorted(elements, key=lambda x: _wbs_code_sort_key(x.get('wbs_code', '')))
        for e in sorted_elements:
            code = e.get('wbs_code', '')
            depth = len(code.split('.')) if code else 0
            indent = "  " * depth
            type_label = {"summary": "📁", "task": "📄", "milestone": "🏁"}.get(e.get('type', ''), "•")
            status_s = format_status_display(e.get('status', ''))
            lines.append(f"{indent}- {type_label} **{code}** {e.get('title', '-')} — {status_s}")
        lines.append("")
        # Mermaid WBS ツリー（簡易 flowchart）
        lines.append("```mermaid")
        lines.append("flowchart TB")
        id_map = {}
        for e in sorted_elements:
            nid = (e.get('id') or e.get('wbs_code', '')).replace('-', '_').replace('.', '_')
            nid = ''.join(c if c.isalnum() or c == '_' else '_' for c in nid) or 'n'
            id_map[e.get('id') or e.get('wbs_code')] = nid
            title_short = (e.get('title') or '')[:20] + ('...' if len(e.get('title', '') or '') > 20 else '')
            label = title_short.replace('"', '\\"')
            lines.append(f'    {nid}["{e.get("wbs_code", "")} {label}"]')
        for e in sorted_elements:
            wbs = e.get('wbs_code', '')
            parts = wbs.split('.')
            if len(parts) > 1:
                parent_code = '.'.join(parts[:-1])
                pid = id_map.get(parent_code)
                nid = id_map.get(e.get('id') or wbs)
                if pid and nid and pid != nid:
                    lines.append(f"    {pid} --> {nid}")
        lines.append("```")
        lines.append("")

    # --- タスク／WBS 要素一覧（進捗分布・表） ---
    work_elements = [e for e in elements if e.get('type') in ('task', 'milestone')]
    if work_elements:
        lines.append("## タスク一覧")
        lines.append("")
        status_counts = {'todo': 0, 'wip': 0, 'done': 0}
        category_counts = {'investigation': 0, 'design': 0, 'development': 0, 'verification': 0}
        for e in work_elements:
            s = e.get('status', 'todo')
            if s in status_counts:
                status_counts[s] += 1
            c = e.get('category', 'development')
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
        with_deps = [e for e in work_elements if e.get('dependencies')]
        if with_deps:
            lines.append("```mermaid")
            lines.append("flowchart LR")
            task_ids = {e.get('id'): e for e in work_elements if e.get('id')}
            for e in work_elements[:15]:
                tid = e.get('id', '')
                title_short = (e.get('title', '') or '')[:12]
                safe_id = tid.replace('-', '_')
                lines.append(f'    {safe_id}["{tid}: {title_short}"]')
                for dep in e.get('dependencies', []):
                    if dep in task_ids:
                        lines.append(f"    {dep.replace('-', '_')} --> {safe_id}")
            lines.append("```")
            lines.append("")
        status_icons = {'todo': '⬜', 'wip': '🔄', 'done': '✅'}
        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        category_labels = {
            'investigation': '調査', 'design': '設計', 'development': '開発', 'verification': '動作確認'
        }
        lines.append("| ID | WBS | タイプ | タスク | カテゴリ | 優先度 | ステータス | 見積(h) |")
        lines.append("|----|-----|--------|--------|----------|--------|----------|---------|")
        for e in sorted(work_elements, key=lambda x: _wbs_code_sort_key(x.get('wbs_code', ''))):
            st = status_icons.get(e.get('status', ''), '') + ' ' + e.get('status', '-')
            pr = priority_icons.get(e.get('priority', ''), '') + ' ' + (e.get('priority') or '-')
            cat = category_labels.get(e.get('category', ''), e.get('category') or '-')
            hours = e.get('estimated_hours', '-')
            typ = e.get('type', '-')
            lines.append(f"| {e.get('id', '-')} | {e.get('wbs_code', '-')} | {typ} | {e.get('title', '-')} | {cat} | {pr} | {st} | {hours} |")
        lines.append("")
        for e in work_elements:
            if e.get('description') or e.get('dependencies'):
                lines.append(f"### {e.get('id', '-')}: {e.get('title', '-')}")
                lines.append("")
                if e.get('description'):
                    lines.append(e['description'])
                    lines.append("")
                if e.get('dependencies'):
                    lines.append(f"**依存:** {', '.join(e['dependencies'])}")
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

    # Blockers（WBS 要素に紐付くブロッカー）
    if data.get('blockers'):
        lines.append("## ブロッカー")
        lines.append("")
        lines.append("| ID | 説明 | 紐付く要素 | 解消 |")
        lines.append("|----|------|------------|------|")
        for b in data['blockers']:
            resolved = "✅ 解消" if b.get('resolved') else "⬜ 未解消"
            lines.append(f"| {b.get('id', '-')} | {b.get('description', '-')} | {b.get('related_element_id', '-')} | {resolved} |")
        lines.append("")

    task_entries = collect_task_states()
    task_section = format_task_states_section(task_entries)
    if task_section:
        lines.append(task_section)

    category_task_entries = collect_category_tasks()
    category_tasks_section = format_category_tasks_section(category_task_entries)
    if category_tasks_section:
        lines.append(category_tasks_section)

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
