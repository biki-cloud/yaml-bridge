#!/usr/bin/env python3
"""
設計YAML → Markdown 汎用変換ツール
各種設計ドキュメントのYAMLファイルを読みやすいMarkdownに変換します。
"""

import yaml
import argparse
from pathlib import Path
from typing import Any, Optional


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
        'feature_design': '✨ 新機能設計',
        'bugfix': '🐛 バグ修正',
        'infrastructure': '🏗️ インフラ構築'
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


# ====================
# API設計固有セクション
# ====================

def generate_api_target_section(data: dict) -> list[str]:
    """API改修対象セクション"""
    lines = []
    if 'target' not in data:
        return lines
    
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
    
    return lines


def generate_api_spec_section(data: dict, section_key: str, title: str) -> list[str]:
    """APIスペック（As-Is/To-Be）セクション"""
    lines = []
    if section_key not in data:
        return lines
    
    spec = data[section_key]
    lines.append(f"### {title}")
    lines.append("")
    
    if 'description' in spec:
        lines.append(f"> {spec['description']}")
        lines.append("")
    
    if 'issues' in spec:
        lines.append("**問題点:**")
        lines.append("")
        for issue in spec['issues']:
            lines.append(f"- ⚠️ {issue}")
        lines.append("")
    
    # Request
    if 'request' in spec:
        lines.append("#### リクエスト")
        lines.append("")
        req = spec['request']
        for field, label in [('headers', 'ヘッダー'), ('query_params', 'クエリパラメータ'), ('body', 'ボディ')]:
            if field in req and req[field]:
                lines.append(f"**{label}:**")
                lines.append("")
                lines.extend(format_param_table(req[field]))
                lines.append("")
    
    # Response
    if 'response' in spec:
        lines.append("#### レスポンス")
        lines.append("")
        res = spec['response']
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
    
    return lines


def generate_api_changes_section(data: dict) -> list[str]:
    """変更内容セクション"""
    lines = []
    if 'changes' not in data:
        return lines
    
    changes = data['changes']
    lines.append("## 変更内容")
    lines.append("")
    
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
    
    return lines


def generate_api_impact_section(data: dict) -> list[str]:
    """影響範囲セクション"""
    lines = []
    if 'impact' not in data:
        return lines
    
    impact = data['impact']
    lines.append("## 影響範囲")
    lines.append("")
    
    for field, title in [('clients', '影響を受けるクライアント'), ('databases', '影響を受けるデータベース'), ('dependencies', '依存サービス')]:
        if field in impact:
            lines.append(f"### {title}")
            lines.append("")
            for item in impact[field]:
                lines.append(f"- {item}")
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


# ====================
# 新機能設計固有セクション
# ====================

def generate_requirements_section(data: dict) -> list[str]:
    """要件定義セクション"""
    lines = []
    if 'requirements' not in data:
        return lines
    
    requirements = data['requirements']
    lines.append("## 要件定義")
    lines.append("")
    
    # 機能要件
    if 'functional' in requirements:
        lines.append("### 機能要件")
        lines.append("")
        lines.append("| ID | 説明 | 優先度 |")
        lines.append("|----|------|--------|")
        for req in requirements['functional']:
            req_id = req.get('id', '-')
            desc = req.get('description', '-')
            priority = format_priority(req.get('priority', '-'))
            lines.append(f"| {req_id} | {desc} | {priority} |")
        lines.append("")
        
        # 受け入れ条件
        for req in requirements['functional']:
            if 'acceptance_criteria' in req:
                lines.append(f"**{req.get('id', '-')} 受け入れ条件:**")
                lines.append("")
                for ac in req['acceptance_criteria']:
                    lines.append(f"- [ ] {ac}")
                lines.append("")
    
    # 非機能要件
    if 'non_functional' in requirements:
        lines.append("### 非機能要件")
        lines.append("")
        lines.append("| ID | カテゴリ | 説明 | 測定指標 |")
        lines.append("|----|----------|------|----------|")
        for req in requirements['non_functional']:
            req_id = req.get('id', '-')
            category = req.get('category', '-')
            desc = req.get('description', '-')
            metric = req.get('metric', '-')
            lines.append(f"| {req_id} | {category} | {desc} | {metric} |")
        lines.append("")
    
    return lines


def generate_architecture_section(data: dict) -> list[str]:
    """アーキテクチャセクション"""
    lines = []
    if 'architecture' not in data:
        return lines
    
    arch = data['architecture']
    lines.append("## アーキテクチャ")
    lines.append("")
    
    if 'overview' in arch:
        lines.append(arch['overview'])
        lines.append("")
    
    if 'patterns' in arch:
        lines.append("### デザインパターン")
        lines.append("")
        for pattern in arch['patterns']:
            lines.append(f"- {pattern}")
        lines.append("")
    
    if 'decisions' in arch:
        lines.append("### アーキテクチャ決定 (ADR)")
        lines.append("")
        for i, decision in enumerate(arch['decisions'], 1):
            lines.append(f"#### ADR-{i}: {decision.get('title', '-')}")
            lines.append("")
            if 'context' in decision:
                lines.append(f"**背景:** {decision['context']}")
                lines.append("")
            lines.append(f"**決定:** {decision.get('decision', '-')}")
            lines.append("")
            lines.append(f"**理由:** {decision.get('rationale', '-')}")
            lines.append("")
            if 'alternatives' in decision:
                lines.append("**検討した代替案:**")
                for alt in decision['alternatives']:
                    lines.append(f"- {alt}")
                lines.append("")
    
    return lines


def generate_components_section(data: dict) -> list[str]:
    """コンポーネントセクション"""
    lines = []
    if 'components' not in data:
        return lines
    
    components = data['components']
    lines.append("## コンポーネント")
    lines.append("")
    lines.append("| コンポーネント | 責務 | 依存 |")
    lines.append("|---------------|------|------|")
    for comp in components:
        name = comp.get('name', '-')
        resp = comp.get('responsibility', '-')
        deps = ', '.join(comp.get('dependencies', [])) or '-'
        lines.append(f"| {name} | {resp} | {deps} |")
    lines.append("")
    
    return lines


def generate_milestones_section(data: dict) -> list[str]:
    """マイルストーンセクション"""
    lines = []
    if 'milestones' not in data:
        return lines
    
    milestones = data['milestones']
    lines.append("## マイルストーン")
    lines.append("")
    for i, ms in enumerate(milestones, 1):
        lines.append(f"### {i}. {ms.get('name', '-')}")
        lines.append("")
        lines.append("**成果物:**")
        for deliverable in ms.get('deliverables', []):
            lines.append(f"- {deliverable}")
        lines.append("")
    
    return lines


# ====================
# バグ修正固有セクション
# ====================

def generate_symptom_section(data: dict) -> list[str]:
    """症状セクション"""
    lines = []
    if 'symptom' not in data:
        return lines
    
    symptom = data['symptom']
    lines.append("## 症状")
    lines.append("")
    lines.append(f"**説明:** {symptom.get('description', '-')}")
    lines.append("")
    
    if 'frequency' in symptom or 'impact' in symptom:
        freq_labels = {'always': '常に', 'often': '頻繁', 'sometimes': '時々', 'rare': '稀'}
        impact_labels = {'critical': '🔴 致命的', 'major': '🟠 重大', 'minor': '🟡 軽微', 'trivial': '⚪ 些細'}
        freq = freq_labels.get(symptom.get('frequency', ''), symptom.get('frequency', '-'))
        impact = impact_labels.get(symptom.get('impact', ''), symptom.get('impact', '-'))
        lines.append(f"**発生頻度:** {freq} | **影響度:** {impact}")
        lines.append("")
    
    if 'affected_users' in symptom:
        lines.append(f"**影響範囲:** {symptom['affected_users']}")
        lines.append("")
    
    if 'reproduction_steps' in symptom:
        lines.append("### 再現手順")
        lines.append("")
        for i, step in enumerate(symptom['reproduction_steps'], 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    
    if 'expected_behavior' in symptom or 'actual_behavior' in symptom:
        lines.append("### 期待動作 vs 実際の動作")
        lines.append("")
        lines.append(f"**期待:** {symptom.get('expected_behavior', '-')}")
        lines.append("")
        lines.append(f"**実際:** {symptom.get('actual_behavior', '-')}")
        lines.append("")
    
    if 'error_logs' in symptom:
        lines.append("### エラーログ")
        lines.append("")
        lines.append("```")
        lines.append(symptom['error_logs'])
        lines.append("```")
        lines.append("")
    
    return lines


def generate_root_cause_section(data: dict) -> list[str]:
    """根本原因セクション"""
    lines = []
    if 'root_cause' not in data:
        return lines
    
    root_cause = data['root_cause']
    lines.append("## 根本原因")
    lines.append("")
    lines.append(f"**原因:** {root_cause.get('description', '-')}")
    lines.append("")
    
    if 'location' in root_cause:
        loc = root_cause['location']
        lines.append("**問題箇所:**")
        lines.append("")
        if 'file' in loc:
            lines.append(f"- ファイル: `{loc['file']}`")
        if 'line' in loc:
            lines.append(f"- 行: {loc['line']}")
        if 'function' in loc:
            lines.append(f"- 関数: `{loc['function']}`")
        lines.append("")
    
    if 'why_analysis' in root_cause:
        lines.append("### なぜなぜ分析")
        lines.append("")
        for i, why in enumerate(root_cause['why_analysis'], 1):
            lines.append(f"**Why {i}:** {why.get('why', '-')}")
            lines.append(f"→ {why.get('answer', '-')}")
            lines.append("")
    
    if 'introduced_by' in root_cause:
        lines.append(f"**混入元:** {root_cause['introduced_by']}")
        lines.append("")
    
    return lines


def generate_fix_section(data: dict) -> list[str]:
    """修正内容セクション"""
    lines = []
    if 'fix' not in data:
        return lines
    
    fix = data['fix']
    lines.append("## 修正内容")
    lines.append("")
    lines.append(f"**アプローチ:** {fix.get('approach', '-')}")
    lines.append("")
    
    if 'changes' in fix:
        lines.append("### 変更ファイル")
        lines.append("")
        for change in fix['changes']:
            lines.append(f"#### `{change.get('file', '-')}`")
            lines.append("")
            lines.append(change.get('description', '-'))
            lines.append("")
            if 'before' in change:
                lines.append("**Before:**")
                lines.append("```")
                lines.append(change['before'])
                lines.append("```")
                lines.append("")
            if 'after' in change:
                lines.append("**After:**")
                lines.append("```")
                lines.append(change['after'])
                lines.append("```")
                lines.append("")
    
    if 'side_effects' in fix:
        lines.append("### 想定される副作用")
        lines.append("")
        for effect in fix['side_effects']:
            lines.append(f"- ⚠️ {effect}")
        lines.append("")
    
    return lines


def generate_verification_section(data: dict) -> list[str]:
    """検証計画セクション"""
    lines = []
    if 'verification' not in data:
        return lines
    
    verification = data['verification']
    lines.append("## 検証計画")
    lines.append("")
    
    if 'test_cases' in verification:
        lines.append("### テストケース")
        lines.append("")
        for i, tc in enumerate(verification['test_cases'], 1):
            lines.append(f"**TC-{i}:** {tc.get('description', '-')}")
            lines.append("")
            if 'steps' in tc:
                for j, step in enumerate(tc['steps'], 1):
                    lines.append(f"  {j}. {step}")
                lines.append("")
            lines.append(f"  **期待結果:** {tc.get('expected_result', '-')}")
            lines.append("")
    
    if 'environments' in verification:
        lines.append("### 検証環境")
        lines.append("")
        for env in verification['environments']:
            lines.append(f"- {env}")
        lines.append("")
    
    return lines


def generate_prevention_section(data: dict) -> list[str]:
    """再発防止策セクション"""
    lines = []
    if 'prevention' not in data:
        return lines
    
    prevention = data['prevention']
    lines.append("## 再発防止策")
    lines.append("")
    
    if 'immediate_actions' in prevention:
        lines.append("### 即時対応")
        lines.append("")
        for action in prevention['immediate_actions']:
            lines.append(f"- [ ] {action}")
        lines.append("")
    
    if 'long_term_actions' in prevention:
        lines.append("### 長期対応")
        lines.append("")
        for action in prevention['long_term_actions']:
            lines.append(f"- [ ] {action}")
        lines.append("")
    
    return lines


# ====================
# インフラ固有セクション
# ====================

def generate_infra_state_section(data: dict, section_key: str, title: str) -> list[str]:
    """インフラ状態セクション（current/target）"""
    lines = []
    if section_key not in data:
        return lines
    
    state = data[section_key]
    lines.append(f"## {title}")
    lines.append("")
    
    if 'description' in state:
        lines.append(state['description'])
        lines.append("")
    
    if 'components' in state:
        lines.append("### コンポーネント")
        lines.append("")
        lines.append("| 名前 | 種別 | 技術 | 説明 |")
        lines.append("|------|------|------|------|")
        for comp in state['components']:
            name = comp.get('name', '-')
            ctype = comp.get('type', '-')
            tech = comp.get('technology', '-')
            desc = comp.get('description', '-')
            lines.append(f"| {name} | {ctype} | {tech} | {desc} |")
        lines.append("")
    
    if 'issues' in state:
        lines.append("### 問題点")
        lines.append("")
        for issue in state['issues']:
            lines.append(f"- ⚠️ {issue}")
        lines.append("")
    
    if 'benefits' in state:
        lines.append("### 期待効果")
        lines.append("")
        for benefit in state['benefits']:
            lines.append(f"- ✅ {benefit}")
        lines.append("")
    
    return lines


def generate_resources_section(data: dict) -> list[str]:
    """リソース計画セクション"""
    lines = []
    if 'resources' not in data:
        return lines
    
    resources = data['resources']
    lines.append("## リソース計画")
    lines.append("")
    
    if 'compute' in resources:
        lines.append("### コンピュート")
        lines.append("")
        lines.append("| 名前 | タイプ | 数量 | CPU | メモリ | ストレージ |")
        lines.append("|------|--------|------|-----|--------|-----------|")
        for comp in resources['compute']:
            name = comp.get('name', '-')
            ctype = comp.get('type', '-')
            count = comp.get('count', 1)
            specs = comp.get('specs', {})
            cpu = specs.get('cpu', '-')
            mem = specs.get('memory', '-')
            storage = specs.get('storage', '-')
            lines.append(f"| {name} | {ctype} | {count} | {cpu} | {mem} | {storage} |")
        lines.append("")
    
    if 'services' in resources:
        lines.append("### マネージドサービス")
        lines.append("")
        lines.append("| 名前 | プロバイダー | サービス種別 |")
        lines.append("|------|-------------|-------------|")
        for svc in resources['services']:
            name = svc.get('name', '-')
            provider = svc.get('provider', '-')
            stype = svc.get('service_type', '-')
            lines.append(f"| {name} | {provider} | {stype} |")
        lines.append("")
    
    return lines


def generate_security_section(data: dict) -> list[str]:
    """セキュリティセクション"""
    lines = []
    if 'security' not in data:
        return lines
    
    security = data['security']
    lines.append("## セキュリティ設計")
    lines.append("")
    
    if 'authentication' in security:
        lines.append(f"**認証:** {security['authentication']}")
        lines.append("")
    if 'authorization' in security:
        lines.append(f"**認可:** {security['authorization']}")
        lines.append("")
    
    if 'encryption' in security:
        enc = security['encryption']
        lines.append("### 暗号化")
        lines.append("")
        if 'at_rest' in enc:
            lines.append(f"- **保存時:** {enc['at_rest']}")
        if 'in_transit' in enc:
            lines.append(f"- **通信時:** {enc['in_transit']}")
        lines.append("")
    
    if 'compliance' in security:
        lines.append("### 準拠規格")
        lines.append("")
        for comp in security['compliance']:
            lines.append(f"- {comp}")
        lines.append("")
    
    return lines


def generate_monitoring_section(data: dict) -> list[str]:
    """監視セクション"""
    lines = []
    if 'monitoring' not in data:
        return lines
    
    monitoring = data['monitoring']
    lines.append("## 監視設計")
    lines.append("")
    
    if 'metrics' in monitoring:
        lines.append("### メトリクス")
        lines.append("")
        lines.append("| メトリクス | 閾値 | アラート条件 |")
        lines.append("|-----------|------|-------------|")
        for metric in monitoring['metrics']:
            name = metric.get('name', '-')
            threshold = metric.get('threshold', '-')
            condition = metric.get('alert_condition', '-')
            lines.append(f"| {name} | {threshold} | {condition} |")
        lines.append("")
    
    if 'logging' in monitoring:
        log = monitoring['logging']
        lines.append("### ログ設定")
        lines.append("")
        lines.append(f"- **保存先:** {log.get('destination', '-')}")
        lines.append(f"- **保持期間:** {log.get('retention_days', '-')}日")
        lines.append("")
    
    return lines


def generate_cost_section(data: dict) -> list[str]:
    """コストセクション"""
    lines = []
    if 'cost' not in data:
        return lines
    
    cost = data['cost']
    lines.append("## コスト見積もり")
    lines.append("")
    
    if 'monthly_estimate' in cost:
        lines.append(f"**月額概算:** {cost['monthly_estimate']}")
        lines.append("")
    
    if 'breakdown' in cost:
        lines.append("### 内訳")
        lines.append("")
        lines.append("| 項目 | コスト |")
        lines.append("|------|--------|")
        for item in cost['breakdown']:
            lines.append(f"| {item.get('item', '-')} | {item.get('cost', '-')} |")
        lines.append("")
    
    if 'notes' in cost:
        lines.append(f"**備考:** {cost['notes']}")
        lines.append("")
    
    return lines


# ====================
# メイン生成関数
# ====================

def generate_api_design_markdown(data: dict) -> str:
    """API設計用Markdown生成"""
    lines = []
    lines.extend(generate_meta_section(data))
    lines.extend(generate_api_target_section(data))
    lines.extend(generate_background_section(data))
    lines.extend(generate_scope_section(data))
    
    if 'as_is' in data or 'to_be' in data:
        lines.append("## 現状 → 改修後")
        lines.append("")
        lines.extend(generate_api_spec_section(data, 'as_is', '現状 (As-Is)'))
        lines.extend(generate_api_spec_section(data, 'to_be', '改修後 (To-Be)'))
    
    lines.extend(generate_api_changes_section(data))
    lines.extend(generate_api_impact_section(data))
    lines.extend(generate_migration_section(data))
    lines.extend(generate_risks_section(data))
    lines.extend(generate_testing_section(data))
    lines.extend(generate_custom_section(data))
    
    return '\n'.join(lines)


def generate_feature_design_markdown(data: dict) -> str:
    """新機能設計用Markdown生成"""
    lines = []
    lines.extend(generate_meta_section(data))
    lines.extend(generate_background_section(data))
    lines.extend(generate_scope_section(data))
    lines.extend(generate_requirements_section(data))
    lines.extend(generate_architecture_section(data))
    lines.extend(generate_components_section(data))
    lines.extend(generate_milestones_section(data))
    lines.extend(generate_risks_section(data))
    lines.extend(generate_testing_section(data))
    lines.extend(generate_custom_section(data))
    
    return '\n'.join(lines)


def generate_bugfix_markdown(data: dict) -> str:
    """バグ修正用Markdown生成"""
    lines = []
    lines.extend(generate_meta_section(data))
    lines.extend(generate_background_section(data))
    lines.extend(generate_symptom_section(data))
    lines.extend(generate_root_cause_section(data))
    lines.extend(generate_fix_section(data))
    lines.extend(generate_verification_section(data))
    lines.extend(generate_prevention_section(data))
    lines.extend(generate_risks_section(data))
    lines.extend(generate_testing_section(data))
    lines.extend(generate_custom_section(data))
    
    return '\n'.join(lines)


def generate_infrastructure_markdown(data: dict) -> str:
    """インフラ構築用Markdown生成"""
    lines = []
    lines.extend(generate_meta_section(data))
    lines.extend(generate_background_section(data))
    lines.extend(generate_scope_section(data))
    lines.extend(generate_infra_state_section(data, 'current_state', '現状のインフラ構成'))
    lines.extend(generate_infra_state_section(data, 'target_state', '目標のインフラ構成'))
    lines.extend(generate_resources_section(data))
    lines.extend(generate_security_section(data))
    lines.extend(generate_monitoring_section(data))
    lines.extend(generate_migration_section(data))
    lines.extend(generate_cost_section(data))
    lines.extend(generate_risks_section(data))
    lines.extend(generate_testing_section(data))
    lines.extend(generate_custom_section(data))
    
    return '\n'.join(lines)


def generate_markdown(data: dict) -> str:
    """YAMLデータからMarkdownを生成する"""
    doc_type = data.get('meta', {}).get('type', 'api_design')
    
    generators = {
        'api_design': generate_api_design_markdown,
        'feature_design': generate_feature_design_markdown,
        'bugfix': generate_bugfix_markdown,
        'infrastructure': generate_infrastructure_markdown,
    }
    
    generator = generators.get(doc_type, generate_api_design_markdown)
    return generator(data)


def main():
    parser = argparse.ArgumentParser(
        description='設計YAMLをMarkdownに変換します（タイプ自動検出）'
    )
    parser.add_argument(
        'input',
        help='入力YAMLファイルのパス'
    )
    parser.add_argument(
        '-o', '--output',
        help='出力Markdownファイルのパス（省略時は標準出力）'
    )
    parser.add_argument(
        '-t', '--type',
        choices=['api_design', 'feature_design', 'bugfix', 'infrastructure'],
        default=None,
        help='ドキュメントタイプを明示的に指定（省略時はmeta.typeから自動検出）'
    )
    
    args = parser.parse_args()
    
    # YAMLを読み込み
    data = load_yaml(args.input)
    
    # タイプの上書き
    if args.type:
        if 'meta' not in data:
            data['meta'] = {}
        data['meta']['type'] = args.type
    
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
