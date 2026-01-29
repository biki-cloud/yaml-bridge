#!/usr/bin/env python3
"""implementation_plan YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import load_yaml, format_status, format_references_section, run_create_human_document


def generate_markdown(data: dict) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '実装計画')}")
    lines.append("")
    
    parts = [f"**タイプ:** 📋 実装計画", f"**ステータス:** {format_status(meta.get('status', 'todo'))}"]
    if meta.get('target_type'):
        labels = {'api': '🌐 API', 'batch': '⚙️ バッチ', 'web': '🖥️ Web', 'cli': '💻 CLI', 'library': '📦 ライブラリ', 'infrastructure': '🏗️ インフラ', 'other': '📄 その他'}
        parts.append(f"**対象:** {labels.get(meta['target_type'], meta['target_type'])}")
    parts.append(f"**バージョン:** {meta.get('version', '-')}")
    lines.append(" | ".join(parts))
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")
    
    # Mermaid開発フロー
    lines.append("## 開発フロー")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("    Start([開始])")
    lines.append("    Plan[実装計画]")
    lines.append("    Impl[実装]")
    lines.append("    Test[テスト]")
    lines.append("    PR[PR作成]")
    lines.append("    Review[レビュー]")
    lines.append("    Merge[マージ]")
    lines.append("    End([完了])")
    lines.append("")
    lines.append("    Start --> Plan")
    lines.append("    Plan --> Impl")
    lines.append("    Impl --> Test")
    lines.append("    Test --> PR")
    lines.append("    PR --> Review")
    lines.append("    Review --> Merge")
    lines.append("    Merge --> End")
    lines.append("    Review -->|修正要| Impl")
    lines.append("```")
    lines.append("")
    
    # Overview
    overview = data.get('overview', {})
    if overview.get('background'):
        lines.append("## 背景")
        lines.append("")
        lines.append(overview['background'])
        lines.append("")
    
    if overview.get('goal'):
        lines.append("## 目的")
        lines.append("")
        lines.append(overview['goal'])
        lines.append("")
    
    if overview.get('related_docs'):
        lines.append("### 関連ドキュメント")
        lines.append("")
        for doc in overview['related_docs']:
            lines.append(f"- {doc}")
        lines.append("")
    
    # Target (API)
    target = data.get('target', {})
    if target.get('endpoint'):
        lines.append("## 対象")
        lines.append("")
        lines.append(f"**エンドポイント:** `{target.get('method', 'GET')} {target['endpoint']}`")
        lines.append("")
        if target.get('description'):
            lines.append(target['description'])
            lines.append("")
    
    # Approach
    approach = data.get('approach', {})
    if approach:
        lines.append("## 実装アプローチ")
        lines.append("")
        if approach.get('summary'):
            lines.append(approach['summary'])
            lines.append("")
        if approach.get('patterns'):
            lines.append("### デザインパターン")
            for p in approach['patterns']:
                lines.append(f"- {p}")
            lines.append("")
        if approach.get('technologies'):
            lines.append("### 使用技術")
            for t in approach['technologies']:
                lines.append(f"- {t}")
            lines.append("")
    
    # Changes + Mermaid
    changes = data.get('changes', [])
    if changes:
        lines.append("## 変更内容")
        lines.append("")
        
        # Mermaid変更タイプ分布
        counts = {'add': 0, 'modify': 0, 'delete': 0, 'rename': 0}
        for c in changes:
            ct = c.get('change_type', 'modify')
            if ct in counts:
                counts[ct] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title 変更タイプ分布")
            labels = {'add': '追加', 'modify': '変更', 'delete': '削除', 'rename': 'リネーム'}
            for t, count in counts.items():
                if count > 0:
                    lines.append(f'    "{labels[t]}" : {count}')
            lines.append("```")
            lines.append("")
        
        icons = {'add': '➕', 'modify': '✏️', 'delete': '❌', 'rename': '📝'}
        for c in changes:
            icon = icons.get(c.get('change_type', 'modify'), '•')
            lines.append(f"### {icon} `{c.get('file', '-')}`")
            lines.append("")
            if c.get('description'):
                lines.append(c['description'])
                lines.append("")
    
    # Testing
    testing = data.get('testing', {})
    if testing:
        lines.append("## テスト")
        lines.append("")
        if testing.get('unit_tests'):
            lines.append("### ユニットテスト")
            for t in testing['unit_tests']:
                lines.append(f"- [ ] {t}")
            lines.append("")
        if testing.get('integration_tests'):
            lines.append("### 結合テスト")
            for t in testing['integration_tests']:
                lines.append(f"- [ ] {t}")
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
