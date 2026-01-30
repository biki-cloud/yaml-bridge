#!/usr/bin/env python3
"""verification_result YAML → Markdown 変換（Mermaid図含む）"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'common'))
from md_base import (
    format_ai_context_section,
    format_navigation_footer,
    format_overview_section,
    format_references_section,
    format_status,
    get_doc_type_role_description,
    load_yaml,
    run_create_human_document,
)


def generate_markdown(data: dict, output_path=None) -> str:
    lines = []
    meta = data.get('meta', {})
    
    lines.append(f"# {meta.get('title', '動作確認結果')}")
    lines.append("")
    lines.append(f"**タイプ:** ✅ 動作確認結果 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    role = get_doc_type_role_description(meta.get('category', ''), meta.get('doc_type', ''))
    if role:
        lines.append(f"**この doc_type の役割:** {role}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    overview_section = format_overview_section(data.get('overview', {}), output_path=output_path)
    if overview_section:
        lines.append(overview_section.rstrip())
        lines.append("")
    # Target
    target = data.get('target', {})
    if target:
        if target.get('feature'):
            lines.append(f"**対象機能:** {target['feature']}")
        if target.get('pr_url'):
            lines.append(f"**関連PR:** {target['pr_url']}")
        if target.get('environment'):
            lines.append(f"**テスト環境:** {target['environment']}")
        lines.append("")
    
    # Test results + Mermaid
    test_results = data.get('test_results', [])
    if test_results:
        lines.append("## テスト結果")
        lines.append("")
        
        # Mermaid結果分布
        counts = {'pass': 0, 'fail': 0, 'blocked': 0, 'skipped': 0}
        for tr in test_results:
            status = tr.get('status', 'pass')
            if status in counts:
                counts[status] += 1
        if sum(counts.values()) > 0:
            lines.append("```mermaid")
            lines.append("pie showData")
            lines.append("    title テスト結果")
            labels = {'pass': 'Pass', 'fail': 'Fail', 'blocked': 'Blocked', 'skipped': 'Skipped'}
            for s, count in counts.items():
                if count > 0:
                    lines.append(f'    "{labels[s]}" : {count}')
            lines.append("```")
            lines.append("")
        
        status_icons = {'pass': '✅', 'fail': '❌', 'blocked': '🚫', 'skipped': '⏭️'}
        
        lines.append("| ID | タイトル | 結果 |")
        lines.append("|----|----------|------|")
        for tr in test_results:
            icon = status_icons.get(tr.get('status', ''), '⬜')
            lines.append(f"| {tr.get('id', '-')} | {tr.get('title', '-')} | {icon} {tr.get('status', '-')} |")
        lines.append("")
        
        # Failed tests details
        failed = [tr for tr in test_results if tr.get('status') == 'fail']
        if failed:
            lines.append("### 失敗したテスト詳細")
            lines.append("")
            for tr in failed:
                lines.append(f"#### {tr.get('id', '-')}: {tr.get('title', '-')}")
                lines.append("")
                if tr.get('actual_result'):
                    lines.append(f"**実際の結果:** {tr['actual_result']}")
                if tr.get('notes'):
                    lines.append(f"**備考:** {tr['notes']}")
                lines.append("")
    
    # Summary + Mermaid
    summary = data.get('summary', {})
    if summary:
        lines.append("## サマリー")
        lines.append("")
        
        if summary.get('executed_at'):
            lines.append(f"**実行日時:** {summary['executed_at']}")
        if summary.get('executed_by'):
            lines.append(f"**実行者:** {summary['executed_by']}")
        lines.append("")
        
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        blocked = summary.get('blocked', 0)
        skipped = summary.get('skipped', 0)
        pass_rate = summary.get('pass_rate', 0)
        
        lines.append("| 合計 | Pass | Fail | Blocked | Skipped | 合格率 |")
        lines.append("|------|------|------|---------|---------|--------|")
        lines.append(f"| {total} | ✅ {passed} | ❌ {failed} | 🚫 {blocked} | ⏭️ {skipped} | {pass_rate:.1f}% |")
        lines.append("")
        
        if summary.get('conclusion'):
            lines.append("### 結論")
            lines.append("")
            lines.append(summary['conclusion'])
            lines.append("")
        
        issues = summary.get('issues_found', [])
        if issues:
            # Mermaid問題重要度
            severity_counts = {'blocker': 0, 'critical': 0, 'major': 0, 'minor': 0}
            for issue in issues:
                sev = issue.get('severity', 'major')
                if sev in severity_counts:
                    severity_counts[sev] += 1
            if sum(severity_counts.values()) > 0:
                lines.append("```mermaid")
                lines.append("pie showData")
                lines.append("    title 問題の重要度")
                for s, count in severity_counts.items():
                    if count > 0:
                        lines.append(f'    "{s.capitalize()}" : {count}')
                lines.append("```")
                lines.append("")
            
            lines.append("### 検出した問題")
            lines.append("")
            severity_icons = {'blocker': '🔴', 'critical': '🟠', 'major': '🟡', 'minor': '🟢'}
            status_labels = {'open': '📝 Open', 'fixed': '✅ Fixed', 'wont_fix': '⏭️ WontFix'}
            
            lines.append("| ID | 重要度 | ステータス | 説明 |")
            lines.append("|----|--------|----------|------|")
            for issue in issues:
                icon = severity_icons.get(issue.get('severity', ''), '')
                status = status_labels.get(issue.get('status', ''), issue.get('status', '-'))
                lines.append(f"| {issue.get('id', '-')} | {icon} {issue.get('severity', '-')} | {status} | {issue.get('description', '-')} |")
            lines.append("")
    
    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    nav = format_navigation_footer(output_path)
    if nav:
        lines.append(nav.rstrip())
    return '\n'.join(lines)


if __name__ == '__main__':
    run_create_human_document(generate_markdown)
