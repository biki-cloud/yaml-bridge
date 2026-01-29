#!/usr/bin/env python3
"""
Mermaid図生成用の共通ヘルパー関数
各タイプのto_mermaid.pyから利用されます。
"""

import yaml
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
