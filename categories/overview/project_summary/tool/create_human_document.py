#!/usr/bin/env python3
"""project_summary YAML → Markdown 変換（Mermaid図含む）
全カテゴリ（overview / design / development / investigation / verification）の
human_document.md へのリンク一覧を表示する。"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from config import AI_DOCUMENT_YAML, HUMAN_DOCUMENT_MD
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document

CATEGORIES = ['overview', 'design', 'development', 'investigation', 'verification']


def get_categories_dir() -> Path:
    """categories ディレクトリを返す（tool/ から doc_type を抜けて 2 段上）"""
    return Path(__file__).resolve().parent.parent.parent.parent


def get_all_doc_links() -> list[tuple[str, str, str]]:
    """全カテゴリの (category, doc_type, title) 一覧を返す（project_summary 自身を除く）"""
    categories_dir = get_categories_dir()
    entries = []
    for category in CATEGORIES:
        cat_dir = categories_dir / category
        if not cat_dir.is_dir():
            continue
        for doc_dir in sorted(cat_dir.iterdir()):
            if not doc_dir.is_dir():
                continue
            if category == 'overview' and doc_dir.name == 'project_summary':
                continue
            yaml_path = doc_dir / AI_DOCUMENT_YAML
            if not yaml_path.exists():
                continue
            try:
                data = load_yaml(str(yaml_path))
            except Exception:
                continue
            meta = data.get('meta', {})
            title = meta.get('title') or meta.get('doc_type', doc_dir.name)
            entries.append((category, doc_dir.name, title))
    return entries


def format_doc_links_section(entries: list[tuple[str, str, str]]) -> str:
    """全カテゴリのドキュメントへのリンク一覧を Markdown で返す（カテゴリ別）"""
    if not entries:
        return ''
    # カテゴリごとにグループ化
    by_category: dict[str, list[tuple[str, str]]] = {}
    for category, doc_type, title in entries:
        by_category.setdefault(category, []).append((doc_type, title))
    lines = []
    lines.append('## カテゴリ別ドキュメント一覧')
    lines.append('')
    for category in CATEGORIES:
        if category not in by_category:
            continue
        lines.append(f'### {category}')
        lines.append('')
        for doc_type, title in by_category[category]:
            # project_summary は categories/overview/project_summary/human/ にあるので、
            # 他カテゴリへは 3 段上がって categories/ から下る
            if category == 'overview':
                href = f'../{doc_type}/{HUMAN_DOCUMENT_MD}'
            else:
                href = f'../../../{category}/{doc_type}/{HUMAN_DOCUMENT_MD}'
            lines.append(f"- [{title}]({href})")
        lines.append('')
    return '\n'.join(lines)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})
    
    # ヘッダー
    lines.append(f"# {meta.get('title', 'プロジェクト概要')}")
    lines.append("")
    lines.append(f"**ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    overview_section = format_overview_section(
        data.get('summary', {}), goal_heading='ゴール', include_related_docs=False, output_path=output_path
    )
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")
    summary = data.get('summary', {})
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

    # Blockers（案件またはWBSタスクに紐付くブロッカー）
    if data.get('blockers'):
        lines.append("## ブロッカー")
        lines.append("")
        lines.append("| ID | 説明 | 紐付け先 | 解消 |")
        lines.append("|----|------|----------|------|")
        for b in data['blockers']:
            resolved = "✅ 解消" if b.get('resolved') else "⬜ 未解消"
            lines.append(f"| {b.get('id', '-')} | {b.get('description', '-')} | {b.get('linked_to', '-')} | {resolved} |")
        lines.append("")

    # 新規必要ファイル
    if data.get('required_docs'):
        lines.append("## 新規必要ファイル")
        lines.append("")
        lines.append("| タイトル | パス/URL | 理由 | 状態 |")
        lines.append("|----------|----------|------|------|")
        for rd in data['required_docs']:
            lines.append(f"| {rd.get('title', '-')} | {rd.get('path_or_url', '-')} | {rd.get('reason') or '-'} | {rd.get('status') or '-'} |")
        lines.append("")
    
    # 全カテゴリの HUMAN_DOCUMENT_MD へのリンク一覧
    doc_links = get_all_doc_links()
    links_section = format_doc_links_section(doc_links)
    if links_section:
        lines.append(links_section)
    
    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
