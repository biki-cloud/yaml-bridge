#!/usr/bin/env python3
"""
設計YAML → Mermaid 汎用変換ツール
各種設計ドキュメントのYAMLファイルからMermaid図を生成します。
"""

import yaml
import argparse
from pathlib import Path
from typing import Optional


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# ====================
# 共通図生成
# ====================

def generate_risk_matrix(data: dict) -> Optional[str]:
    """リスクマトリクス（深刻度×発生確率）を生成"""
    if 'risks' not in data:
        return None
    
    risks = data['risks']
    if not risks:
        return None
    
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
        
        x = (prob_map.get(probability, 2) - 0.5) / 3
        y = (severity_map.get(severity, 2) - 0.5) / 4
        
        if len(risk_name) > 15:
            risk_name = risk_name[:12] + "..."
        
        lines.append(f"    \"{risk_name}\": [{x:.2f}, {y:.2f}]")
    
    lines.append("```")
    
    return '\n'.join(lines)


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
        if len(desc) > 30:
            desc = desc[:27] + "..."
        
        node_id = f"Step{order}"
        lines.append(f"    {node_id}[\"{order}. {desc}\"]")
        lines.append(f"    {prev_node} --> {node_id}")
        
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
    lines.append("")
    lines.append("    style Start fill:#e1f5fe")
    lines.append("    style End fill:#c8e6c9")
    lines.append("```")
    
    return '\n'.join(lines)


# ====================
# API設計用図
# ====================

def generate_api_change_summary(data: dict) -> Optional[str]:
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
    
    icons = {'add': '➕', 'modify': '✏️', 'remove': '❌', 'deprecate': '⚠️'}
    
    for i, change in enumerate(changes):
        ctype = change.get('type', 'modify')
        target = change.get('target', f'変更{i+1}')
        breaking = change.get('breaking', False)
        icon = icons.get(ctype, '•')
        
        if len(target) > 20:
            target = target[:17] + "..."
        
        node_id = f"C{i}"
        if breaking:
            lines.append(f"        {node_id}[\"{icon} {target} ⚠️\"]")
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
    
    for i, change in enumerate(changes):
        if change.get('breaking'):
            lines.append(f"    style C{i} fill:#ffcdd2,stroke:#c62828")
    
    lines.append("    style AsIs fill:#fff3e0")
    lines.append("    style ToBe fill:#e8f5e9")
    lines.append("```")
    
    return '\n'.join(lines)


def generate_api_impact_diagram(data: dict) -> Optional[str]:
    """影響範囲図を生成"""
    if 'impact' not in data:
        return None
    
    impact = data['impact']
    if not impact:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TB")
    
    api_name = data.get('target', {}).get('api_name', 'API')
    if len(api_name) > 15:
        api_name = api_name[:12] + "..."
    lines.append(f"    API(({api_name}))")
    lines.append("")
    
    if 'clients' in impact and impact['clients']:
        lines.append("    subgraph Clients[\"👥 クライアント\"]")
        for i, client in enumerate(impact['clients']):
            client_name = client if len(client) <= 20 else client[:17] + "..."
            lines.append(f"        CL{i}[\"{client_name}\"]")
        lines.append("    end")
        lines.append("    Clients --> API")
        lines.append("")
    
    if 'databases' in impact and impact['databases']:
        lines.append("    subgraph DB[\"🗄️ データベース\"]")
        for i, db in enumerate(impact['databases']):
            db_name = db if len(db) <= 20 else db[:17] + "..."
            lines.append(f"        DB{i}[(\"{db_name}\")]")
        lines.append("    end")
        lines.append("    API --> DB")
        lines.append("")
    
    if 'dependencies' in impact and impact['dependencies']:
        lines.append("    subgraph Deps[\"🔗 依存サービス\"]")
        for i, dep in enumerate(impact['dependencies']):
            dep_name = dep if len(dep) <= 20 else dep[:17] + "..."
            lines.append(f"        DEP{i}[[\"{dep_name}\"]]")
        lines.append("    end")
        lines.append("    API <--> Deps")
        lines.append("")
    
    lines.append("    style API fill:#bbdefb,stroke:#1976d2")
    lines.append("    style Clients fill:#fff9c4")
    lines.append("    style DB fill:#c8e6c9")
    lines.append("    style Deps fill:#f3e5f5")
    lines.append("```")
    
    return '\n'.join(lines)


def generate_api_flow(data: dict) -> Optional[str]:
    """APIリクエスト/レスポンスのシーケンス図を生成"""
    target = data.get('target', {})
    
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
    lines.append("")
    lines.append("    alt エラー時")
    lines.append("    A-->>C: エラーレスポンス")
    lines.append("    end")
    lines.append("```")
    
    return '\n'.join(lines)


# ====================
# 新機能設計用図
# ====================

def generate_component_diagram(data: dict) -> Optional[str]:
    """コンポーネント図を生成"""
    if 'components' not in data:
        return None
    
    components = data['components']
    if not components:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TB")
    
    # コンポーネントノード作成
    for i, comp in enumerate(components):
        name = comp.get('name', f'Component{i}')
        resp = comp.get('responsibility', '')
        if len(resp) > 20:
            resp = resp[:17] + "..."
        lines.append(f"    C{i}[\"{name}\"]")
    
    lines.append("")
    
    # 依存関係のエッジ
    comp_name_to_id = {comp.get('name', f'Component{i}'): f'C{i}' for i, comp in enumerate(components)}
    
    for i, comp in enumerate(components):
        deps = comp.get('dependencies', [])
        for dep in deps:
            if dep in comp_name_to_id:
                lines.append(f"    C{i} --> {comp_name_to_id[dep]}")
    
    lines.append("```")
    
    return '\n'.join(lines)


def generate_requirements_chart(data: dict) -> Optional[str]:
    """要件優先度チャートを生成"""
    if 'requirements' not in data or 'functional' not in data['requirements']:
        return None
    
    functional = data['requirements']['functional']
    if not functional:
        return None
    
    # 優先度別にカウント
    priority_counts = {'must': 0, 'should': 0, 'could': 0, 'wont': 0}
    for req in functional:
        priority = req.get('priority', 'should')
        if priority in priority_counts:
            priority_counts[priority] += 1
    
    lines = []
    lines.append("```mermaid")
    lines.append("pie showData")
    lines.append("    title 要件優先度分布")
    for priority, count in priority_counts.items():
        if count > 0:
            labels = {'must': 'Must', 'should': 'Should', 'could': 'Could', 'wont': "Won't"}
            lines.append(f"    \"{labels.get(priority, priority)}\" : {count}")
    lines.append("```")
    
    return '\n'.join(lines)


def generate_architecture_diagram(data: dict) -> Optional[str]:
    """アーキテクチャ概要図を生成"""
    if 'architecture' not in data:
        return None
    
    arch = data['architecture']
    patterns = arch.get('patterns', [])
    decisions = arch.get('decisions', [])
    
    if not patterns and not decisions:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("mindmap")
    lines.append("  root((アーキテクチャ))")
    
    if patterns:
        lines.append("    パターン")
        for pattern in patterns[:5]:  # 最大5つ
            if len(pattern) > 20:
                pattern = pattern[:17] + "..."
            lines.append(f"      {pattern}")
    
    if decisions:
        lines.append("    決定事項")
        for decision in decisions[:5]:  # 最大5つ
            title = decision.get('title', '')
            if len(title) > 20:
                title = title[:17] + "..."
            lines.append(f"      {title}")
    
    lines.append("```")
    
    return '\n'.join(lines)


# ====================
# バグ修正用図
# ====================

def generate_bugfix_flow(data: dict) -> Optional[str]:
    """バグ修正フロー図を生成"""
    symptom = data.get('symptom', {})
    root_cause = data.get('root_cause', {})
    fix = data.get('fix', {})
    
    if not symptom and not root_cause and not fix:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TD")
    lines.append("    S[\"🐛 症状発見\"]")
    lines.append("    I[\"🔍 調査\"]")
    lines.append("    R[\"💡 原因特定\"]")
    lines.append("    F[\"🔧 修正実装\"]")
    lines.append("    V[\"✅ 検証\"]")
    lines.append("    D[\"🚀 デプロイ\"]")
    lines.append("")
    lines.append("    S --> I")
    lines.append("    I --> R")
    lines.append("    R --> F")
    lines.append("    F --> V")
    lines.append("    V --> D")
    lines.append("")
    lines.append("    V -->|失敗| F")
    lines.append("")
    lines.append("    style S fill:#ffcdd2")
    lines.append("    style D fill:#c8e6c9")
    lines.append("```")
    
    return '\n'.join(lines)


def generate_why_analysis_diagram(data: dict) -> Optional[str]:
    """なぜなぜ分析図を生成"""
    if 'root_cause' not in data or 'why_analysis' not in data['root_cause']:
        return None
    
    why_analysis = data['root_cause']['why_analysis']
    if not why_analysis:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TD")
    
    for i, why in enumerate(why_analysis):
        why_text = why.get('why', f'Why {i+1}')
        answer = why.get('answer', '')
        
        if len(why_text) > 25:
            why_text = why_text[:22] + "..."
        if len(answer) > 25:
            answer = answer[:22] + "..."
        
        lines.append(f"    W{i}{{\"Why: {why_text}\"}}")
        lines.append(f"    A{i}[\"{answer}\"]")
        lines.append(f"    W{i} --> A{i}")
        
        if i < len(why_analysis) - 1:
            lines.append(f"    A{i} --> W{i+1}")
    
    # 最後に根本原因
    lines.append(f"    A{len(why_analysis)-1} --> RC[\"🎯 根本原因\"]")
    lines.append("    style RC fill:#ffeb3b")
    
    lines.append("```")
    
    return '\n'.join(lines)


# ====================
# インフラ用図
# ====================

def generate_infra_diagram(data: dict) -> Optional[str]:
    """インフラ構成図を生成"""
    target_state = data.get('target_state', {})
    components = target_state.get('components', [])
    
    if not components:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TB")
    
    # タイプ別にグループ化
    type_groups = {}
    for i, comp in enumerate(components):
        ctype = comp.get('type', 'other')
        if ctype not in type_groups:
            type_groups[ctype] = []
        type_groups[ctype].append((i, comp))
    
    type_labels = {
        'server': '🖥️ サーバー',
        'container': '📦 コンテナ',
        'serverless': '⚡ サーバーレス',
        'database': '🗄️ データベース',
        'cache': '💾 キャッシュ',
        'queue': '📨 キュー',
        'storage': '📁 ストレージ',
        'network': '🌐 ネットワーク',
        'cdn': '🌍 CDN',
        'other': '📌 その他'
    }
    
    for ctype, comps in type_groups.items():
        label = type_labels.get(ctype, ctype)
        lines.append(f"    subgraph {ctype}[\"{label}\"]")
        for i, comp in comps:
            name = comp.get('name', f'Component{i}')
            tech = comp.get('technology', '')
            if tech:
                if len(tech) > 15:
                    tech = tech[:12] + "..."
                lines.append(f"        COMP{i}[\"{name}<br/>{tech}\"]")
            else:
                lines.append(f"        COMP{i}[\"{name}\"]")
        lines.append("    end")
        lines.append("")
    
    # 接続関係
    comp_name_to_id = {}
    for i, comp in enumerate(components):
        comp_name_to_id[comp.get('name', '')] = f'COMP{i}'
    
    for i, comp in enumerate(components):
        connections = comp.get('connections', [])
        for conn in connections:
            if conn in comp_name_to_id:
                lines.append(f"    COMP{i} --> {comp_name_to_id[conn]}")
    
    lines.append("```")
    
    return '\n'.join(lines)


def generate_cost_chart(data: dict) -> Optional[str]:
    """コスト内訳チャートを生成"""
    if 'cost' not in data or 'breakdown' not in data['cost']:
        return None
    
    breakdown = data['cost']['breakdown']
    if not breakdown:
        return None
    
    lines = []
    lines.append("```mermaid")
    lines.append("pie showData")
    lines.append("    title コスト内訳")
    
    for item in breakdown[:8]:  # 最大8項目
        name = item.get('item', 'その他')
        cost = item.get('cost', '0')
        # コストから数値を抽出（簡易的に）
        cost_num = ''.join(c for c in str(cost) if c.isdigit())
        if cost_num:
            lines.append(f"    \"{name}\" : {cost_num}")
    
    lines.append("```")
    
    return '\n'.join(lines)


# ====================
# タイプ別全図生成
# ====================

def generate_api_design_diagrams(data: dict) -> str:
    """API設計用の全図を生成"""
    lines = []
    title = data.get('meta', {}).get('title', 'API設計')
    lines.append(f"# {title} - Mermaid図")
    lines.append("")
    
    sections = [
        ("変更サマリー", "As-Is（現状）から To-Be（改修後）への変更の概要です。", generate_api_change_summary(data)),
        ("移行フロー", "移行ステップとロールバック手順です。", generate_migration_flowchart(data)),
        ("影響範囲", "この改修が影響するシステムの範囲です。", generate_api_impact_diagram(data)),
        ("リスクマトリクス", "深刻度と発生確率に基づくリスクの分布です。", generate_risk_matrix(data)),
        ("APIフロー", "APIリクエスト/レスポンスの流れです。", generate_api_flow(data)),
    ]
    
    for title, desc, diagram in sections:
        if diagram:
            lines.append(f"## {title}")
            lines.append("")
            lines.append(desc)
            lines.append("")
            lines.append(diagram)
            lines.append("")
    
    return '\n'.join(lines)


def generate_bugfix_diagrams(data: dict) -> str:
    """バグ修正用の全図を生成"""
    lines = []
    title = data.get('meta', {}).get('title', 'バグ修正')
    lines.append(f"# {title} - Mermaid図")
    lines.append("")
    
    sections = [
        ("修正フロー", "バグ修正の全体フローです。", generate_bugfix_flow(data)),
        ("なぜなぜ分析", "根本原因を特定するための分析です。", generate_why_analysis_diagram(data)),
        ("リスクマトリクス", "深刻度と発生確率に基づくリスクの分布です。", generate_risk_matrix(data)),
    ]
    
    for title, desc, diagram in sections:
        if diagram:
            lines.append(f"## {title}")
            lines.append("")
            lines.append(desc)
            lines.append("")
            lines.append(diagram)
            lines.append("")
    
    return '\n'.join(lines)


def generate_all_diagrams(data: dict) -> str:
    """ドキュメントタイプに応じた全図を生成"""
    doc_type = data.get('meta', {}).get('type', 'api_design')
    
    generators = {
        'api_design': generate_api_design_diagrams,
        'bugfix': generate_bugfix_diagrams,
    }
    
    generator = generators.get(doc_type, generate_api_design_diagrams)
    return generator(data)


def main():
    parser = argparse.ArgumentParser(
        description='設計YAMLからMermaid図を生成します（タイプ自動検出）'
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
        choices=['api_design', 'bugfix'],
        default=None,
        help='ドキュメントタイプを明示的に指定（省略時はmeta.typeから自動検出）'
    )
    parser.add_argument(
        '--diagram',
        choices=['all', 'risk', 'migration'],
        default='all',
        help='生成する図の種類（デフォルト: all）'
    )
    
    args = parser.parse_args()
    
    # YAMLを読み込み
    data = load_yaml(args.input)
    
    # タイプの上書き
    if args.type:
        if 'meta' not in data:
            data['meta'] = {}
        data['meta']['type'] = args.type
    
    # 図を生成
    if args.diagram == 'all':
        output = generate_all_diagrams(data)
    elif args.diagram == 'risk':
        output = generate_risk_matrix(data) or "リスクデータがありません"
    elif args.diagram == 'migration':
        output = generate_migration_flowchart(data) or "移行データがありません"
    else:
        output = generate_all_diagrams(data)
    
    # 出力
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output, encoding='utf-8')
        print(f"✅ {output_path} に出力しました")
    else:
        print(output)


if __name__ == '__main__':
    main()
