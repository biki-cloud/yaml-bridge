#!/usr/bin/env python3
"""requirements YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, format_ai_context_section, format_overview_section, run_create_human_document


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '要件整理')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 要件整理 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
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
    overview = data.get('overview', {})
    if overview.get('scope'):
        scope = overview['scope']
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
    
    # Requirements + Mermaid
    requirements = data.get('requirements', [])
    if requirements:
        lines.append("## 要件一覧")
        lines.append("")
        
        # Mermaid優先度分布
        priority_counts = {'must': 0, 'should': 0, 'could': 0, 'wont': 0}
        type_counts = {'functional': 0, 'non_functional': 0}
        for r in requirements:
            p = r.get('priority', 'should')
            if p in priority_counts:
                priority_counts[p] += 1
            t = r.get('type', 'functional')
            if t in type_counts:
                type_counts[t] += 1
        
        if sum(priority_counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 要件の優先度分布")
            for p, count in priority_counts.items():
                if count > 0:
                    lines.append(f'    "{p.capitalize()}" : {count}')
            lines.append("```")
            lines.append("")
        
        if sum(type_counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 要件タイプ分布")
            labels = {'functional': '機能要件', 'non_functional': '非機能要件'}
            for t, count in type_counts.items():
                if count > 0:
                    lines.append(f'    "{labels[t]}" : {count}')
            lines.append("```")
            lines.append("")
        
        priority_icons = {'must': '🔴 Must', 'should': '🟠 Should', 'could': '🟡 Could', 'wont': '⚪ Wont'}
        type_labels = {'functional': '機能', 'non_functional': '非機能'}
        
        lines.append("| ID | 種類 | 優先度 | 説明 |")
        lines.append("|----|------|--------|------|")
        for req in requirements:
            req_type = type_labels.get(req.get('type', ''), req.get('type', '-'))
            priority = priority_icons.get(req.get('priority', ''), req.get('priority', '-'))
            lines.append(f"| {req.get('id', '-')} | {req_type} | {priority} | {req.get('description', '-')} |")
        lines.append("")
        
        # Acceptance criteria
        for req in requirements:
            if req.get('acceptance_criteria'):
                lines.append(f"### {req.get('id', '-')} 受け入れ条件")
                lines.append("")
                for ac in req['acceptance_criteria']:
                    lines.append(f"- [ ] {ac}")
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
    
    ref_section = format_references_section(data)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
