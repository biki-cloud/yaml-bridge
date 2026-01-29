#!/usr/bin/env python3
"""
API設計YAML → Mermaid 変換ツール
API改修設計ドキュメントのYAMLファイルからMermaid図を生成します。

生成される図:
1. 移行フローチャート - 移行ステップの流れ
2. 変更サマリー図 - As-Is → To-Be の変化
3. リスクマトリクス - 深刻度×発生確率
4. 影響範囲図 - クライアント・DB・依存関係
"""

import yaml
import argparse
from pathlib import Path
from typing import Optional


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_migration_flowchart(data: dict) -> Optional[str]:
    """移行ステップのフローチャートを生成"""
    if 'migration' not in data or 'steps' not in data['migration']:
        return None
    
    steps = data['migration']['steps']
    if not steps:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("    Start([🚀 移行開始])")
    
    sorted_steps = sorted(steps, key=lambda x: x.get('order', 0))
    
    prev_node = "Start"
    for i, step in enumerate(sorted_steps):
        order = step.get('order', i + 1)
        desc = step.get('description', f'Step {order}')
        # 長い説明は短縮
        if len(desc) > 30:
            desc = desc[:27] + "..."
        
        node_id = f"Step{order}"
        lines.append(f"    {node_id}[\"{order}. {desc}\"]")
        lines.append(f"    {prev_node} --> {node_id}")
        
        # ロールバックがある場合
        if 'rollback' in step:
            rollback_id = f"Rollback{order}"
            rollback_desc = step['rollback']
            if len(rollback_desc) > 25:
                rollback_desc = rollback_desc[:22] + "..."
            lines.append(f"    {rollback_id}[/\"🔙 {rollback_desc}\"/]")
            lines.append(f"    {node_id} -.-> {rollback_id}")
        
        prev_node = node_id
    
    lines.append("    End([✅ 移行完了])")
    lines.append(f"    {prev_node} --> End")
    
    # スタイリング
    lines.append("")
    lines.append("    style Start fill:#e1f5fe")
    lines.append("    style End fill:#c8e6c9")
    
    lines.append("```")
    
    return '\n'.join(lines)


def generate_change_summary(data: dict) -> Optional[str]:
    """変更サマリー図を生成（As-Is → To-Be）"""
    if 'changes' not in data:
        return None
    
    changes = data['changes']
    if not changes:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("    subgraph AsIs[\"📦 現状 As-Is\"]")
    lines.append("        A1[既存の実装]")
    lines.append("    end")
    lines.append("")
    lines.append("    subgraph Changes[\"🔄 変更内容\"]")
    
    for i, change in enumerate(changes):
        ctype = change.get('type', 'modify')
        target = change.get('target', f'変更{i+1}')
        breaking = change.get('breaking', False)
        
        # アイコンとスタイル
        icons = {
            'add': '➕',
            'modify': '✏️',
            'remove': '❌',
            'deprecate': '⚠️'
        }
        icon = icons.get(ctype, '•')
        
        # 長い名前は短縮
        if len(target) > 20:
            target = target[:17] + "..."
        
        node_id = f"C{i}"
        if breaking:
            lines.append(f"        {node_id}[\"{icon} {target}<br/>⚠️破壊的\"]")
        else:
            lines.append(f"        {node_id}[\"{icon} {target}\"]")
    
    lines.append("    end")
    lines.append("")
    lines.append("    subgraph ToBe[\"🎯 改修後 To-Be\"]")
    lines.append("        B1[改修された実装]")
    lines.append("    end")
    lines.append("")
    lines.append("    AsIs --> Changes")
    lines.append("    Changes --> ToBe")
    lines.append("")
    
    # 破壊的変更のスタイリング
    for i, change in enumerate(changes):
        if change.get('breaking'):
            lines.append(f"    style C{i} fill:#ffcdd2,stroke:#c62828")
    
    lines.append("    style AsIs fill:#fff3e0")
    lines.append("    style ToBe fill:#e8f5e9")
    lines.append("```")
    
    return '\n'.join(lines)


def generate_risk_matrix(data: dict) -> Optional[str]:
    """リスクマトリクス（深刻度×発生確率）を生成"""
    if 'risks' not in data:
        return None
    
    risks = data['risks']
    if not risks:
        return None
    
    # 深刻度と発生確率のマッピング
    severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    prob_map = {'low': 1, 'medium': 2, 'high': 3}
    
    lines = []
    lines.append("```mermaid")
    lines.append("quadrantChart")
    lines.append("    title リスクマトリクス")
    lines.append("    x-axis 発生確率 低 --> 高")
    lines.append("    y-axis 深刻度 低 --> 高")
    lines.append("    quadrant-1 要対策")
    lines.append("    quadrant-2 監視")
    lines.append("    quadrant-3 許容")
    lines.append("    quadrant-4 注意")
    
    for i, risk in enumerate(risks):
        risk_name = risk.get('risk', f'リスク{i+1}')
        severity = risk.get('severity', 'medium')
        probability = risk.get('probability', 'medium')
        
        # 座標計算（0-1の範囲に正規化）
        x = (prob_map.get(probability, 2) - 0.5) / 3
        y = (severity_map.get(severity, 2) - 0.5) / 4
        
        # 名前を短縮
        if len(risk_name) > 15:
            risk_name = risk_name[:12] + "..."
        
        lines.append(f"    \"{risk_name}\": [{x:.2f}, {y:.2f}]")
    
    lines.append("```")
    
    return '\n'.join(lines)


def generate_impact_diagram(data: dict) -> Optional[str]:
    """影響範囲図を生成"""
    if 'impact' not in data:
        return None
    
    impact = data['impact']
    if not impact:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TB")
    
    # 中心にAPI
    api_name = data.get('target', {}).get('api_name', 'API')
    lines.append(f"    API(({api_name}))")
    lines.append("")
    
    # クライアント
    if 'clients' in impact and impact['clients']:
        lines.append("    subgraph Clients[\"👥 クライアント\"]")
        for i, client in enumerate(impact['clients']):
            lines.append(f"        CL{i}[\"{client}\"]")
        lines.append("    end")
        lines.append("    Clients --> API")
        lines.append("")
    
    # データベース
    if 'databases' in impact and impact['databases']:
        lines.append("    subgraph DB[\"🗄️ データベース\"]")
        for i, db in enumerate(impact['databases']):
            lines.append(f"        DB{i}[(\"{db}\")]")
        lines.append("    end")
        lines.append("    API --> DB")
        lines.append("")
    
    # 依存サービス
    if 'dependencies' in impact and impact['dependencies']:
        lines.append("    subgraph Deps[\"🔗 依存サービス\"]")
        for i, dep in enumerate(impact['dependencies']):
            lines.append(f"        DEP{i}[[\"{dep}\"]]")
        lines.append("    end")
        lines.append("    API <--> Deps")
        lines.append("")
    
    # スタイリング
    lines.append("    style API fill:#bbdefb,stroke:#1976d2")
    lines.append("    style Clients fill:#fff9c4")
    lines.append("    style DB fill:#c8e6c9")
    lines.append("    style Deps fill:#f3e5f5")
    
    lines.append("```")
    
    return '\n'.join(lines)


def generate_api_flow(data: dict) -> Optional[str]:
    """APIリクエスト/レスポンスのシーケンス図を生成"""
    target = data.get('target', {})
    to_be = data.get('to_be', {})
    
    if not target.get('endpoint'):
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("sequenceDiagram")
    lines.append("    autonumber")
    lines.append("    participant C as Client")
    lines.append("    participant A as API")
    lines.append("    participant D as Database")
    lines.append("")
    
    method = target.get('method', 'GET')
    endpoint = target.get('endpoint', '/api')
    
    lines.append(f"    C->>+A: {method} {endpoint}")
    lines.append("    A->>A: 認証・バリデーション")
    lines.append("    A->>+D: データ取得")
    lines.append("    D-->>-A: 結果")
    lines.append("    A-->>-C: レスポンス")
    
    # エラーケース
    lines.append("")
    lines.append("    alt エラー時")
    lines.append("    A-->>C: エラーレスポンス")
    lines.append("    end")
    
    lines.append("```")
    
    return '\n'.join(lines)


def generate_all_diagrams(data: dict) -> str:
    """すべての図を生成してMarkdownとして返す"""
    lines = []
    
    # タイトル
    title = data.get('meta', {}).get('title', 'API設計')
    lines.append(f"# {title} - Mermaid図")
    lines.append("")
    
    # 目次
    lines.append("## 目次")
    lines.append("1. [変更サマリー](#変更サマリー)")
    lines.append("2. [移行フロー](#移行フロー)")
    lines.append("3. [影響範囲](#影響範囲)")
    lines.append("4. [リスクマトリクス](#リスクマトリクス)")
    lines.append("5. [APIフロー](#apiフロー)")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 変更サマリー
    change_diagram = generate_change_summary(data)
    if change_diagram:
        lines.append("## 変更サマリー")
        lines.append("")
        lines.append("As-Is（現状）から To-Be（改修後）への変更の概要です。")
        lines.append("")
        lines.append(change_diagram)
        lines.append("")
    
    # 移行フロー
    migration_diagram = generate_migration_flowchart(data)
    if migration_diagram:
        lines.append("## 移行フロー")
        lines.append("")
        lines.append("移行ステップとロールバック手順です。")
        lines.append("")
        lines.append(migration_diagram)
        lines.append("")
    
    # 影響範囲
    impact_diagram = generate_impact_diagram(data)
    if impact_diagram:
        lines.append("## 影響範囲")
        lines.append("")
        lines.append("この改修が影響するシステムの範囲です。")
        lines.append("")
        lines.append(impact_diagram)
        lines.append("")
    
    # リスクマトリクス
    risk_diagram = generate_risk_matrix(data)
    if risk_diagram:
        lines.append("## リスクマトリクス")
        lines.append("")
        lines.append("深刻度と発生確率に基づくリスクの分布です。")
        lines.append("")
        lines.append(risk_diagram)
        lines.append("")
    
    # APIフロー
    api_flow = generate_api_flow(data)
    if api_flow:
        lines.append("## APIフロー")
        lines.append("")
        lines.append("APIリクエスト/レスポンスの流れです。")
        lines.append("")
        lines.append(api_flow)
        lines.append("")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='API設計YAMLからMermaid図を生成します'
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
        '--type',
        choices=['all', 'migration', 'change', 'risk', 'impact', 'flow'],
        default='all',
        help='生成する図の種類（デフォルト: all）'
    )
    
    args = parser.parse_args()
    
    # YAMLを読み込み
    data = load_yaml(args.input)
    
    # 図を生成
    if args.type == 'all':
        output = generate_all_diagrams(data)
    elif args.type == 'migration':
        output = generate_migration_flowchart(data) or "図を生成できませんでした"
    elif args.type == 'change':
        output = generate_change_summary(data) or "図を生成できませんでした"
    elif args.type == 'risk':
        output = generate_risk_matrix(data) or "図を生成できませんでした"
    elif args.type == 'impact':
        output = generate_impact_diagram(data) or "図を生成できませんでした"
    elif args.type == 'flow':
        output = generate_api_flow(data) or "図を生成できませんでした"
    
    # 出力
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output, encoding='utf-8')
        print(f"✅ {output_path} に出力しました")
    else:
        print(output)


if __name__ == '__main__':
    main()
