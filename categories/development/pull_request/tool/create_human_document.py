#!/usr/bin/env python3
"""pull_request YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', 'PR情報')}")
    lines.append("")
    lines.append(f"**タイプ:** 🔀 PR情報 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    # Pull Request info + Mermaid
    pr = data.get('pull_request', {})
    if pr:
        lines.append("## Pull Request")
        lines.append("")
        if pr.get('url'):
            lines.append(f"**URL:** {pr['url']}")
        lines.append(f"**タイトル:** {pr.get('title', '-')}")
        if pr.get('branch'):
            lines.append(f"**ブランチ:** `{pr['branch']}` → `{pr.get('base_branch', 'main')}`")
        lines.append("")
        
        if pr.get('description'):
            lines.append("### 説明")
            lines.append("")
            lines.append(pr['description'])
            lines.append("")
        
        if pr.get('reviewers'):
            lines.append(f"**レビュアー:** {', '.join(pr['reviewers'])}")
        if pr.get('labels'):
            lines.append(f"**ラベル:** {', '.join(pr['labels'])}")
        if pr.get('reviewers') or pr.get('labels'):
            lines.append("")
        
        checklist = pr.get('checklist', [])
        if checklist:
            # Mermaidチェックリスト進捗
            done = sum(1 for item in checklist if item.get('done'))
            not_done = len(checklist) - done
            if done > 0 or not_done > 0:
                lines.append("```mermaid")
                lines.append("pie showData")
                lines.append("    title チェックリスト進捗")
                if done > 0:
                    lines.append(f'    "完了" : {done}')
                if not_done > 0:
                    lines.append(f'    "未完了" : {not_done}')
                lines.append("```")
                lines.append("")
            
            lines.append("### チェックリスト")
            lines.append("")
            for item in checklist:
                check = '✅' if item.get('done') else '⬜'
                lines.append(f"- {check} {item.get('item', '-')}")
            lines.append("")
    
    overview_section = format_overview_section(
        data.get('overview', {}), include_goal=False, include_related_docs=False
    )
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")
    overview = data.get('overview', {})
    if overview.get('changes_summary'):
        lines.append("## 変更概要")
        lines.append("")
        lines.append(overview['changes_summary'])
        lines.append("")
    
    # Testing
    testing = data.get('testing', {})
    if testing:
        lines.append("## テスト")
        lines.append("")
        if testing.get('tested_items'):
            lines.append("### テスト済み")
            for t in testing['tested_items']:
                lines.append(f"- ✅ {t}")
            lines.append("")
        if testing.get('not_tested'):
            lines.append("### 未テスト")
            for t in testing['not_tested']:
                lines.append(f"- ⬜ {t}")
            lines.append("")
    
    # Notes
    if data.get('notes'):
        lines.append("## メモ")
        lines.append("")
        for note in data['notes']:
            lines.append(f"- {note}")
        lines.append("")
    
    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
