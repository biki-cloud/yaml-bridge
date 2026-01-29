#!/usr/bin/env python3
"""
Markdown生成用の共通ヘルパー関数
各タイプのto_md.pyから利用されます。
"""

import yaml
from pathlib import Path


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# ====================
# フォーマットヘルパー
# ====================

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


def format_priority(priority: str) -> str:
    """優先度をアイコン付きで表示"""
    icons = {
        'must': '🔴 Must',
        'should': '🟠 Should',
        'could': '🟡 Could',
        'wont': '⚪ Won\'t'
    }
    return icons.get(priority, priority)


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


def format_type_badge(doc_type: str) -> str:
    """ドキュメントタイプをバッジで表示"""
    badges = {
        'api_design': '🔌 API設計',
        'bugfix': '🐛 バグ修正',
    }
    return badges.get(doc_type, doc_type)


# ====================
# 共通セクション生成
# ====================

def generate_meta_section(data: dict) -> list[str]:
    """メタ情報セクション"""
    lines = []
    if 'meta' not in data:
        return lines
    
    meta = data['meta']
    title = meta.get('title', 'Untitled')
    doc_type = meta.get('type', 'unknown')
    status = meta.get('status', 'unknown')
    version = meta.get('version', '-')
    
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**タイプ:** {format_type_badge(doc_type)} | **ステータス:** {format_status_badge(status)} | **バージョン:** {version}")
    
    if meta.get('author') or meta.get('created_at'):
        author = meta.get('author', '-')
        created = meta.get('created_at', '-')
        updated = meta.get('updated_at', '-')
        lines.append(f"**作成者:** {author} | **作成日:** {created} | **更新日:** {updated}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    return lines


def generate_background_section(data: dict) -> list[str]:
    """背景・目的セクション"""
    lines = []
    if 'background' not in data:
        return lines
    
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
    
    return lines


def generate_scope_section(data: dict) -> list[str]:
    """スコープセクション"""
    lines = []
    if 'scope' not in data:
        return lines
    
    scope = data['scope']
    lines.append("## スコープ")
    lines.append("")
    
    if 'in' in scope:
        lines.append("### 対象")
        lines.append("")
        for item in scope['in']:
            lines.append(f"- ✅ {item}")
        lines.append("")
    
    if 'out' in scope:
        lines.append("### 対象外")
        lines.append("")
        for item in scope['out']:
            lines.append(f"- ❌ {item}")
        lines.append("")
    
    return lines


def generate_risks_section(data: dict) -> list[str]:
    """リスクセクション"""
    lines = []
    if 'risks' not in data:
        return lines
    
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
    
    return lines


def generate_testing_section(data: dict) -> list[str]:
    """テスト計画セクション"""
    lines = []
    if 'testing' not in data:
        return lines
    
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
    
    return lines


def generate_custom_section(data: dict) -> list[str]:
    """カスタムフィールドセクション"""
    lines = []
    if 'custom' not in data:
        return lines
    
    custom = data['custom']
    lines.append("## カスタムフィールド")
    lines.append("")
    lines.append("| キー | 値 |")
    lines.append("|------|-----|")
    for key, value in custom.items():
        if isinstance(value, (list, dict)):
            value = f"`{value}`"
        lines.append(f"| {key} | {value} |")
    lines.append("")
    
    return lines


def generate_migration_section(data: dict) -> list[str]:
    """移行計画セクション"""
    lines = []
    if 'migration' not in data:
        return lines
    
    migration = data['migration']
    lines.append("## 移行計画")
    lines.append("")
    
    if 'strategy' in migration:
        strategy_labels = {
            'big_bang': '🚀 ビッグバン（一括切替）',
            'gradual': '📈 段階的移行',
            'feature_flag': '🚩 フィーチャーフラグ',
            'versioning': '🔢 バージョニング',
            'lift_and_shift': '📦 リフト＆シフト',
            'replatform': '🔄 リプラットフォーム',
            'refactor': '🔧 リファクタ',
            'blue_green': '🔵🟢 ブルー/グリーン',
            'canary': '🐤 カナリアリリース'
        }
        label = strategy_labels.get(migration['strategy'], migration['strategy'])
        lines.append(f"**移行戦略:** {label}")
        lines.append("")
    
    if 'downtime_window' in migration:
        lines.append(f"**想定ダウンタイム:** {migration['downtime_window']}")
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
    
    return lines
