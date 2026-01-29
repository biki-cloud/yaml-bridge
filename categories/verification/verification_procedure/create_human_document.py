#!/usr/bin/env python3
"""verification_procedure YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, run_create_human_document


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '動作確認手順')}")
    lines.append("")
    lines.append(f"**タイプ:** 📝 動作確認手順 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Overview
    overview = data.get('overview', {})
    if overview.get('related_plan'):
        lines.append(f"**関連計画:** {overview['related_plan']}")
    if overview.get('environment'):
        lines.append(f"**テスト環境:** {overview['environment']}")
    if overview:
        lines.append("")
    
    # Mermaidテストフロー + Procedures
    procedures = data.get('procedures', [])
    if procedures:
        # Mermaidテストフロー
        lines.append("## テストフロー")
        lines.append("")
        lines.append("```mermaid")
        lines.append("flowchart TD")
        lines.append("    Start([開始])")
        
        for i, proc in enumerate(procedures[:5]):
            pid = proc.get('id', f'P{i+1}')
            title_short = proc.get('title', '')[:15]
            lines.append(f'    {pid}["{pid}: {title_short}"]')
            if i == 0:
                lines.append(f"    Start --> {pid}")
            else:
                prev_id = procedures[i-1].get('id', f'P{i}')
                lines.append(f"    {prev_id} --> {pid}")
        
        last_id = procedures[min(len(procedures)-1, 4)].get('id', 'P1')
        lines.append(f"    {last_id} --> End([完了])")
        lines.append("```")
        lines.append("")
        
        # Procedures詳細
        for proc in procedures:
            lines.append(f"## {proc.get('id', '-')}: {proc.get('title', '-')}")
            lines.append("")
            
            if proc.get('precondition'):
                lines.append(f"**事前条件:** {proc['precondition']}")
                lines.append("")
            
            lines.append("### 手順")
            lines.append("")
            for i, step in enumerate(proc.get('steps', []), 1):
                lines.append(f"**{i}. {step.get('action', '-')}**")
                lines.append("")
                if step.get('expected'):
                    lines.append(f"   期待結果: {step['expected']}")
                if step.get('note'):
                    lines.append(f"   備考: {step['note']}")
                lines.append("")
            
            if proc.get('postcondition'):
                lines.append(f"**事後条件:** {proc['postcondition']}")
                lines.append("")
    
    ref_section = format_references_section(data)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
