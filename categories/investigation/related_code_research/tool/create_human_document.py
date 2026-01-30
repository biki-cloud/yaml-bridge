#!/usr/bin/env python3
"""related_code_research YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '関連コード調査')}")
    lines.append("")
    lines.append(f"**タイプ:** 🔍 関連コード調査 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    overview_section = format_overview_section(data.get('overview', {}))
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")
    # Target
    target = data.get('target', {})
    lines.append("## 調査対象")
    lines.append("")
    if target.get('description'):
        lines.append(target['description'])
        lines.append("")
    if target.get('project_context'):
        lines.append(f"**プロジェクトコンテキスト:** {target['project_context']}")
        lines.append("")
    if target.get('search_scope'):
        lines.append("**調査範囲:**")
        for s in target['search_scope']:
            lines.append(f"- {s}")
        lines.append("")
    
    # Questions
    if data.get('questions'):
        lines.append("## 調査項目")
        lines.append("")
        icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines.append("| ID | 質問 | 優先度 |")
        lines.append("|----|------|--------|")
        for q in data['questions']:
            icon = icons.get(q.get('priority', ''), '')
            lines.append(f"| {q.get('id', '-')} | {q.get('question', '-')} | {icon} {q.get('priority', '-')} |")
        lines.append("")
    
    # Findings + Mermaid関連度分布
    findings = data.get('findings', [])
    if findings:
        lines.append("## 調査結果")
        lines.append("")
        
        # Mermaid関連度分布
        counts = {'high': 0, 'medium': 0, 'low': 0}
        for f in findings:
            rel = f.get('relevance', 'medium')
            if rel in counts:
                counts[rel] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 関連度分布")
            labels = {'high': '高', 'medium': '中', 'low': '低'}
            for level, count in counts.items():
                if count > 0:
                    lines.append(f'    "{labels[level]}" : {count}')
            lines.append("```")
            lines.append("")
        
        relevance_icons = {'high': '🔴 高', 'medium': '🟡 中', 'low': '🟢 低'}
        for i, f in enumerate(findings, 1):
            qid = f"[{f['question_id']}] " if f.get('question_id') else ""
            lines.append(f"### {i}. {qid}{f.get('description', '-')[:50]}...")
            lines.append("")
            if f.get('relevance'):
                lines.append(f"**関連度:** {relevance_icons.get(f['relevance'], f['relevance'])}")
            if f.get('location'):
                lines.append(f"**場所:** `{f['location']}`")
            lines.append("")
            lines.append(f.get('description', '-'))
            lines.append("")
    
    # Conclusions
    if data.get('conclusions'):
        lines.append("## 結論")
        lines.append("")
        for c in data['conclusions']:
            lines.append(f"- {c}")
        lines.append("")
    
    # Next actions
    if data.get('next_actions'):
        lines.append("## 次のアクション")
        lines.append("")
        icons = {'must': '🔴 Must', 'should': '🟠 Should', 'could': '🟡 Could'}
        for a in data['next_actions']:
            lines.append(f"- {icons.get(a.get('priority', ''), '')} {a.get('action', '-')}")
        lines.append("")
    
    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
