#!/usr/bin/env python3
"""
API設計YAML → Markdown 変換ツール
API改修設計ドキュメントのYAMLファイルを読みやすいMarkdownに変換します。
"""

import yaml
import argparse
from pathlib import Path
from typing import Any


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def format_status_badge(status: str) -> str:
    """ステータスをバッジ形式で表示"""
    badges = {
        'draft': '🔵 Draft',
        'review': '🟡 Review',
        'approved': '🟢 Approved',
        'implemented': '✅ Implemented'
    }
    return badges.get(status, status)


def format_severity(severity: str) -> str:
    """深刻度をアイコン付きで表示"""
    icons = {
        'low': '🟢 低',
        'medium': '🟡 中',
        'high': '🟠 高',
        'critical': '🔴 致命的'
    }
    return icons.get(severity, severity)


def format_change_type(change_type: str) -> str:
    """変更タイプをアイコン付きで表示"""
    icons = {
        'add': '➕ 追加',
        'modify': '✏️ 変更',
        'remove': '❌ 削除',
        'deprecate': '⚠️ 非推奨化'
    }
    return icons.get(change_type, change_type)


def format_param_table(params: list[dict]) -> list[str]:
    """パラメータをテーブル形式で出力"""
    lines = []
    lines.append("| 名前 | 型 | 必須 | 説明 |")
    lines.append("|------|-----|------|------|")
    for param in params:
        name = param.get('name', '-')
        ptype = param.get('type', '-')
        required = '✅' if param.get('required') else '-'
        desc = param.get('description', '-')
        if 'example' in param:
            desc += f" (例: `{param['example']}`)"
        lines.append(f"| `{name}` | {ptype} | {required} | {desc} |")
    return lines


def generate_markdown(data: dict) -> str:
    """YAMLデータからMarkdownを生成する"""
    lines = []
    
    # ========== Meta セクション ==========
    if 'meta' in data:
        meta = data['meta']
        title = meta.get('title', 'Untitled')
        status = meta.get('status', 'unknown')
        version = meta.get('version', '-')
        
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**ステータス:** {format_status_badge(status)} | **バージョン:** {version}")
        
        if meta.get('author') or meta.get('created_at'):
            author = meta.get('author', '-')
            created = meta.get('created_at', '-')
            updated = meta.get('updated_at', '-')
            lines.append(f"**作成者:** {author} | **作成日:** {created} | **更新日:** {updated}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # ========== Target セクション ==========
    if 'target' in data:
        target = data['target']
        lines.append("## 改修対象")
        lines.append("")
        lines.append("| 項目 | 値 |")
        lines.append("|------|-----|")
        lines.append(f"| API名 | {target.get('api_name', '-')} |")
        lines.append(f"| エンドポイント | `{target.get('endpoint', '-')}` |")
        if 'method' in target:
            lines.append(f"| メソッド | `{target['method']}` |")
        if 'current_version' in target:
            lines.append(f"| 現行バージョン | {target['current_version']} |")
        lines.append("")
    
    # ========== Background セクション ==========
    if 'background' in data:
        bg = data['background']
        lines.append("## 背景・目的")
        lines.append("")
        lines.append(f"**目的:** {bg.get('purpose', '-')}")
        lines.append("")
        
        if 'context' in bg:
            lines.append("### 背景")
            lines.append("")
            lines.append(bg['context'].strip())
            lines.append("")
        
        if 'issue_links' in bg:
            lines.append("### 関連リンク")
            lines.append("")
            for link in bg['issue_links']:
                lines.append(f"- {link}")
            lines.append("")
    
    # ========== As-Is / To-Be セクション ==========
    if 'as_is' in data or 'to_be' in data:
        lines.append("## 現状 → 改修後")
        lines.append("")
        
        # As-Is
        if 'as_is' in data:
            as_is = data['as_is']
            lines.append("### 現状 (As-Is)")
            lines.append("")
            if 'description' in as_is:
                lines.append(f"> {as_is['description']}")
                lines.append("")
            
            if 'issues' in as_is:
                lines.append("**現状の問題点:**")
                lines.append("")
                for issue in as_is['issues']:
                    lines.append(f"- ⚠️ {issue}")
                lines.append("")
            
            # Request
            if 'request' in as_is:
                lines.append("#### リクエスト")
                lines.append("")
                req = as_is['request']
                if 'headers' in req and req['headers']:
                    lines.append("**ヘッダー:**")
                    lines.append("")
                    lines.extend(format_param_table(req['headers']))
                    lines.append("")
                if 'query_params' in req and req['query_params']:
                    lines.append("**クエリパラメータ:**")
                    lines.append("")
                    lines.extend(format_param_table(req['query_params']))
                    lines.append("")
                if 'body' in req and req['body']:
                    lines.append("**ボディ:**")
                    lines.append("")
                    lines.extend(format_param_table(req['body']))
                    lines.append("")
            
            # Response
            if 'response' in as_is:
                lines.append("#### レスポンス")
                lines.append("")
                res = as_is['response']
                if 'status_codes' in res:
                    lines.append("**ステータスコード:**")
                    lines.append("")
                    for sc in res['status_codes']:
                        lines.append(f"- `{sc['code']}`: {sc.get('description', '-')}")
                    lines.append("")
                if 'body' in res and res['body']:
                    lines.append("**レスポンスボディ:**")
                    lines.append("")
                    lines.extend(format_param_table(res['body']))
                    lines.append("")
        
        # To-Be
        if 'to_be' in data:
            to_be = data['to_be']
            lines.append("### 改修後 (To-Be)")
            lines.append("")
            if 'description' in to_be:
                lines.append(f"> {to_be['description']}")
                lines.append("")
            
            # Request
            if 'request' in to_be:
                lines.append("#### リクエスト")
                lines.append("")
                req = to_be['request']
                if 'headers' in req and req['headers']:
                    lines.append("**ヘッダー:**")
                    lines.append("")
                    lines.extend(format_param_table(req['headers']))
                    lines.append("")
                if 'query_params' in req and req['query_params']:
                    lines.append("**クエリパラメータ:**")
                    lines.append("")
                    lines.extend(format_param_table(req['query_params']))
                    lines.append("")
                if 'body' in req and req['body']:
                    lines.append("**ボディ:**")
                    lines.append("")
                    lines.extend(format_param_table(req['body']))
                    lines.append("")
            
            # Response
            if 'response' in to_be:
                lines.append("#### レスポンス")
                lines.append("")
                res = to_be['response']
                if 'status_codes' in res:
                    lines.append("**ステータスコード:**")
                    lines.append("")
                    for sc in res['status_codes']:
                        lines.append(f"- `{sc['code']}`: {sc.get('description', '-')}")
                    lines.append("")
                if 'body' in res and res['body']:
                    lines.append("**レスポンスボディ:**")
                    lines.append("")
                    lines.extend(format_param_table(res['body']))
                    lines.append("")
    
    # ========== Changes セクション ==========
    if 'changes' in data:
        changes = data['changes']
        lines.append("## 変更内容")
        lines.append("")
        
        # 破壊的変更の警告
        breaking_changes = [c for c in changes if c.get('breaking')]
        if breaking_changes:
            lines.append("> ⚠️ **破壊的変更があります**")
            lines.append("")
        
        lines.append("| 種類 | 対象 | 内容 | 理由 | 破壊的 |")
        lines.append("|------|------|------|------|--------|")
        for change in changes:
            ctype = format_change_type(change.get('type', '-'))
            target = change.get('target', '-')
            desc = change.get('description', '-')
            reason = change.get('reason', '-')
            breaking = '⚠️ Yes' if change.get('breaking') else 'No'
            lines.append(f"| {ctype} | {target} | {desc} | {reason} | {breaking} |")
        lines.append("")
    
    # ========== Impact セクション ==========
    if 'impact' in data:
        impact = data['impact']
        lines.append("## 影響範囲")
        lines.append("")
        
        if 'clients' in impact:
            lines.append("### 影響を受けるクライアント")
            lines.append("")
            for client in impact['clients']:
                lines.append(f"- {client}")
            lines.append("")
        
        if 'databases' in impact:
            lines.append("### 影響を受けるデータベース")
            lines.append("")
            for db in impact['databases']:
                lines.append(f"- {db}")
            lines.append("")
        
        if 'dependencies' in impact:
            lines.append("### 依存サービス")
            lines.append("")
            for dep in impact['dependencies']:
                lines.append(f"- {dep}")
            lines.append("")
    
    # ========== Migration セクション ==========
    if 'migration' in data:
        migration = data['migration']
        lines.append("## 移行計画")
        lines.append("")
        
        if 'strategy' in migration:
            strategy_labels = {
                'big_bang': '🚀 ビッグバン（一括切替）',
                'gradual': '📈 段階的移行',
                'feature_flag': '🚩 フィーチャーフラグ',
                'versioning': '🔢 バージョニング'
            }
            label = strategy_labels.get(migration['strategy'], migration['strategy'])
            lines.append(f"**移行戦略:** {label}")
            lines.append("")
        
        if 'steps' in migration:
            lines.append("### 移行ステップ")
            lines.append("")
            for step in sorted(migration['steps'], key=lambda x: x.get('order', 0)):
                order = step.get('order', '-')
                desc = step.get('description', '-')
                lines.append(f"**Step {order}:** {desc}")
                if 'rollback' in step:
                    lines.append(f"  - 🔙 ロールバック: {step['rollback']}")
                lines.append("")
        
        if 'rollback_plan' in migration:
            lines.append("### 全体ロールバック計画")
            lines.append("")
            lines.append(migration['rollback_plan'].strip())
            lines.append("")
    
    # ========== Risks セクション ==========
    if 'risks' in data:
        risks = data['risks']
        lines.append("## リスクと対策")
        lines.append("")
        lines.append("| リスク | 深刻度 | 発生確率 | 対策 |")
        lines.append("|--------|--------|----------|------|")
        for risk in risks:
            r = risk.get('risk', '-')
            severity = format_severity(risk.get('severity', '-'))
            prob = risk.get('probability', '-')
            mitigation = risk.get('mitigation', '-')
            lines.append(f"| {r} | {severity} | {prob} | {mitigation} |")
        lines.append("")
    
    # ========== Testing セクション ==========
    if 'testing' in data:
        testing = data['testing']
        lines.append("## テスト計画")
        lines.append("")
        
        if 'unit_tests' in testing:
            lines.append("### ユニットテスト")
            lines.append("")
            for test in testing['unit_tests']:
                lines.append(f"- [ ] {test}")
            lines.append("")
        
        if 'integration_tests' in testing:
            lines.append("### 結合テスト")
            lines.append("")
            for test in testing['integration_tests']:
                lines.append(f"- [ ] {test}")
            lines.append("")
        
        if 'regression_tests' in testing:
            lines.append("### 回帰テスト")
            lines.append("")
            for test in testing['regression_tests']:
                lines.append(f"- [ ] {test}")
            lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='API設計YAMLをMarkdownに変換します'
    )
    parser.add_argument(
        'input',
        help='入力YAMLファイルのパス'
    )
    parser.add_argument(
        '-o', '--output',
        help='出力Markdownファイルのパス（省略時は標準出力）'
    )
    
    args = parser.parse_args()
    
    # YAMLを読み込み
    data = load_yaml(args.input)
    
    # Markdownを生成
    markdown = generate_markdown(data)
    
    # 出力
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding='utf-8')
        print(f"✅ {output_path} に出力しました")
    else:
        print(markdown)


if __name__ == '__main__':
    main()
