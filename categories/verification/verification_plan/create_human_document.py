#!/usr/bin/env python3
"""verification_plan YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, run_create_human_document


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '動作確認計画')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 動作確認計画 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Target
    target = data.get('target', {})
    if target:
        lines.append("## テスト対象")
        lines.append("")
        lines.append(f"**対象機能:** {target.get('feature', '-')}")
        if target.get('pr_url'):
            lines.append(f"**関連PR:** {target['pr_url']}")
        if target.get('environment'):
            lines.append(f"**テスト環境:** {target['environment']}")
        lines.append("")
        if target.get('related_docs'):
            lines.append("**関連ドキュメント:**")
            for doc in target['related_docs']:
                lines.append(f"- {doc}")
            lines.append("")
    
    # Scope
    scope = data.get('scope', {})
    if scope:
        lines.append("## スコープ")
        lines.append("")
        if scope.get('in'):
            lines.append("### テスト対象")
            for item in scope['in']:
                lines.append(f"- {item}")
            lines.append("")
        if scope.get('out'):
            lines.append("### テスト対象外")
            for item in scope['out']:
                lines.append(f"- {item}")
            lines.append("")
    
    # Prerequisites
    if data.get('prerequisites'):
        lines.append("## 事前条件")
        lines.append("")
        for p in data['prerequisites']:
            check = '✅' if p.get('verified') else '⬜'
            lines.append(f"- {check} {p.get('description', '-')}")
        lines.append("")
    
    # Test cases + Mermaid
    test_cases = data.get('test_cases', [])
    if test_cases:
        lines.append("## テストケース")
        lines.append("")
        
        # Mermaidカテゴリ分布
        category_counts = {'normal': 0, 'boundary': 0, 'error': 0, 'performance': 0, 'security': 0}
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        for tc in test_cases:
            cat = tc.get('category', 'normal')
            if cat in category_counts:
                category_counts[cat] += 1
            p = tc.get('priority', 'medium')
            if p in priority_counts:
                priority_counts[p] += 1
        
        if sum(category_counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title テストカテゴリ分布")
            labels = {'normal': '正常系', 'boundary': '境界値', 'error': '異常系', 'performance': '性能', 'security': 'セキュリティ'}
            for cat, count in category_counts.items():
                if count > 0:
                    lines.append(f'    "{labels[cat]}" : {count}')
            lines.append("```")
            lines.append("")
        
        if sum(priority_counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 優先度分布")
            for p, count in priority_counts.items():
                if count > 0:
                    lines.append(f'    "{p.capitalize()}" : {count}')
            lines.append("```")
            lines.append("")
        
        category_labels = {'normal': '🔵 正常系', 'boundary': '🟡 境界値', 'error': '🔴 異常系', 'performance': '⚡ 性能', 'security': '🔒 セキュリティ'}
        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        
        lines.append("| ID | タイトル | カテゴリ | 優先度 |")
        lines.append("|----|----------|----------|--------|")
        for tc in test_cases:
            category = category_labels.get(tc.get('category', ''), tc.get('category', '-'))
            priority = priority_icons.get(tc.get('priority', ''), '') + ' ' + tc.get('priority', '-')
            lines.append(f"| {tc.get('id', '-')} | {tc.get('title', '-')} | {category} | {priority} |")
        lines.append("")
        
        # Details
        for tc in test_cases:
            lines.append(f"### {tc.get('id', '-')}: {tc.get('title', '-')}")
            lines.append("")
            if tc.get('precondition'):
                lines.append(f"**事前条件:** {tc['precondition']}")
                lines.append("")
            if tc.get('steps'):
                lines.append("**手順:**")
                for i, step in enumerate(tc['steps'], 1):
                    lines.append(f"{i}. {step}")
                lines.append("")
            if tc.get('expected_result'):
                lines.append(f"**期待結果:** {tc['expected_result']}")
                lines.append("")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
