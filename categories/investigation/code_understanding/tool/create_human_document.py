#!/usr/bin/env python3
"""code_understanding YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', 'コード理解')}")
    lines.append("")
    lines.append(f"**タイプ:** 📖 コード理解 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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
    if target.get('repository'):
        lines.append(f"**リポジトリ:** {target['repository']}")
    if target.get('files'):
        lines.append("**対象ファイル:**")
        for f in target['files']:
            lines.append(f"- `{f}`")
        lines.append("")
    if target.get('components'):
        lines.append("**対象コンポーネント:**")
        for c in target['components']:
            lines.append(f"- {c}")
        lines.append("")
    
    # Questions + Mermaid調査フロー
    questions = data.get('questions', [])
    if questions:
        lines.append("## 調査項目")
        lines.append("")
        
        # Mermaid調査フロー
        lines.append("```mermaid")
        lines.append("flowchart TD")
        lines.append("    Start([調査開始])")
        for i, q in enumerate(questions[:5]):
            qid = q.get('id', f'Q{i+1}')
            question = q.get('question', '')[:20]
            lines.append(f'    Q{i}["{qid}: {question}..."]')
            if i == 0:
                lines.append(f"    Start --> Q{i}")
            else:
                lines.append(f"    Q{i-1} --> Q{i}")
        lines.append(f"    Q{len(questions[:5])-1} --> Analysis[分析]")
        lines.append("    Analysis --> Findings[結果まとめ]")
        lines.append("    Findings --> End([完了])")
        lines.append("```")
        lines.append("")
        
        icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines.append("| ID | 質問 | 優先度 |")
        lines.append("|----|------|--------|")
        for q in questions:
            icon = icons.get(q.get('priority', ''), '')
            lines.append(f"| {q.get('id', '-')} | {q.get('question', '-')} | {icon} {q.get('priority', '-')} |")
        lines.append("")
    
    # Findings + Mermaid影響度分布
    findings = data.get('findings', [])
    if findings:
        lines.append("## 調査結果")
        lines.append("")
        
        # Mermaid影響度分布
        counts = {'high': 0, 'medium': 0, 'low': 0}
        for f in findings:
            impact = f.get('impact', 'medium')
            if impact in counts:
                counts[impact] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 調査結果の影響度分布")
            labels = {'high': '高', 'medium': '中', 'low': '低'}
            for level, count in counts.items():
                if count > 0:
                    lines.append(f'    "{labels[level]}" : {count}')
            lines.append("```")
            lines.append("")
        
        impact_icons = {'high': '🔴 高', 'medium': '🟡 中', 'low': '🟢 低'}
        for i, f in enumerate(findings, 1):
            qid = f"[{f['question_id']}] " if f.get('question_id') else ""
            desc = f.get('description', '-')[:50]
            lines.append(f"### {i}. {qid}{desc}...")
            lines.append("")
            if f.get('impact'):
                lines.append(f"**影響度:** {impact_icons.get(f['impact'], f['impact'])}")
                lines.append("")
            lines.append(f.get('description', '-'))
            lines.append("")
            if f.get('evidence'):
                lines.append("**根拠:**")
                lines.append("```")
                lines.append(f['evidence'])
                lines.append("```")
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
        lines.append("| 優先度 | アクション |")
        lines.append("|--------|----------|")
        for a in data['next_actions']:
            lines.append(f"| {icons.get(a.get('priority', ''), a.get('priority', '-'))} | {a.get('action', '-')} |")
        lines.append("")
    
    ref_section = format_references_section(data)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
