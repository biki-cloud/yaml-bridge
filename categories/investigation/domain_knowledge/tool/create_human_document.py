#!/usr/bin/env python3
"""domain_knowledge YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, run_create_human_document


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    title = meta.get('title', 'ドメイン知識')
    
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**タイプ:** 🧠 ドメイン知識 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    # Target
    target = data.get('target', {})
    lines.append("## 調査対象")
    lines.append("")
    if target.get('description'):
        lines.append(target['description'])
        lines.append("")
    if target.get('domain'):
        lines.append(f"**ドメイン:** {target['domain']}")
        lines.append("")
    
    # Mermaid知識マップ
    glossary = data.get('glossary', [])
    findings = data.get('findings', [])
    if glossary or findings:
        lines.append("```mermaid")
        lines.append("mindmap")
        short_title = title[:20] if len(title) > 20 else title
        lines.append(f"  root(({short_title}))")
        if glossary:
            lines.append("    用語")
            for g in glossary[:5]:
                term = g.get('term', '')[:15]
                lines.append(f"      {term}")
        if findings:
            lines.append("    発見事項")
            for i, f in enumerate(findings[:3], 1):
                lines.append(f"      発見{i}")
        lines.append("```")
        lines.append("")
    
    # Glossary
    if glossary:
        lines.append("## 用語集")
        lines.append("")
        lines.append("| 用語 | 定義 |")
        lines.append("|------|------|")
        for g in glossary:
            lines.append(f"| {g.get('term', '-')} | {g.get('definition', '-')} |")
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
    
    # Findings
    if findings:
        lines.append("## 調査結果")
        lines.append("")
        for i, f in enumerate(findings, 1):
            qid = f"[{f['question_id']}] " if f.get('question_id') else ""
            lines.append(f"### {i}. {qid}{f.get('description', '-')[:50]}...")
            lines.append("")
            lines.append(f.get('description', '-'))
            lines.append("")
            if f.get('source'):
                lines.append(f"**情報源:** {f['source']}")
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
    
    ref_section = format_references_section(data)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
