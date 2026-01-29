#!/usr/bin/env python3
"""
Markdown生成用の共通ヘルパー関数
各タイプの create_human_document.py から利用されます。
"""

import argparse
import yaml
from pathlib import Path
from typing import Callable


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def format_status(status: str) -> str:
    """meta.status を表示用ラベルに変換"""
    return {'todo': '⬜ TODO', 'wip': '🔄 WIP', 'done': '✅ Done'}.get(status, status)


def _mermaid_sanitize_id(raw: str) -> str:
    """MermaidノードID用: 英数字・アンダースコアのみにする"""
    if not raw:
        return 'n'
    s = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(raw))
    return s or 'n'


def _mermaid_quote_label(label: str, max_len: int = 40) -> str:
    """Mermaidラベル: 括弧・コロン等を含む場合はダブルクォートで囲む"""
    if not label:
        return '""'
    short = label[:max_len] + ('...' if len(label) > max_len else '')
    if any(c in short for c in '():[],'):
        return '"' + short.replace('"', '\\"') + '"'
    return short


def format_ai_context_section(data: dict) -> str:
    """
    data['ai_context'] から「AIの現在の考え」「これからのアクション」「判断・進め方の流れ」の
    Markdown セクションと Mermaid 図を生成する。全 create_human_document.py で共通利用。
    """
    ctx = data.get('ai_context')
    if not ctx:
        return ''

    lines = []

    # --- 現在の考え: マインドマップ + 箇条書き ---
    thinking = ctx.get('current_thinking')
    if thinking is not None:
        items = thinking if isinstance(thinking, list) else [s.strip() for s in str(thinking).splitlines() if s.strip()]
        if items:
            lines.append('## AIの現在の考え')
            lines.append('')
            # Mermaid mindmap（ルートは短く、枝は1項目ずつ・短く）
            lines.append('```mermaid')
            lines.append('mindmap')
            lines.append('  root((現在の考え))')
            for i, item in enumerate(items[:8]):
                short = item[:25] + ('...' if len(item) > 25 else '')
                safe = short.replace('"', '\\"')
                lines.append(f'    item{i + 1} "{safe}"')
            lines.append('```')
            lines.append('')
            for item in items:
                lines.append(f'- {item}')
            lines.append('')

    # --- これからのアクション: フローチャート ---
    actions = ctx.get('next_actions') or []
    if actions:
        lines.append('## これからのアクション')
        lines.append('')
        lines.append('```mermaid')
        lines.append('flowchart TB')
        prev_id = None
        for a in actions:
            nid = _mermaid_sanitize_id(a.get('id', ''))
            label = _mermaid_quote_label(a.get('label', ''))
            lines.append(f'    {nid}[{label}]')
            if prev_id is not None:
                lines.append(f'    {prev_id} --> {nid}')
            prev_id = nid
        lines.append('```')
        lines.append('')
        for a in actions:
            detail = a.get('detail', '')
            if detail:
                lines.append(f"- **{a.get('label', '-')}**: {detail}")
            else:
                lines.append(f"- {a.get('label', '-')}")
        lines.append('')

    # --- 判断・進め方の流れ: フローチャート（任意） ---
    flow = ctx.get('decision_flow') or []
    if flow:
        lines.append('## 判断・進め方の流れ')
        lines.append('')
        lines.append('```mermaid')
        lines.append('flowchart TB')
        seen = set()
        for node in flow:
            nid = _mermaid_sanitize_id(node.get('id', ''))
            label = _mermaid_quote_label(node.get('label', ''))
            if nid not in seen:
                lines.append(f'    {nid}[{label}]')
                seen.add(nid)
            next_id = node.get('next')
            if next_id:
                lines.append(f'    {nid} --> {_mermaid_sanitize_id(next_id)}')
            for cond_next in node.get('next_condition', []):
                lines.append(f'    {nid} --> {_mermaid_sanitize_id(cond_next)}')
        lines.append('```')
        lines.append('')

    return '\n'.join(lines).rstrip()


def format_references_section(data: dict) -> str:
    """
    data['references'] から「関連資料（エビデンス）」セクションの Markdown 文字列を生成する。
    全 create_human_document.py で共通利用。
    """
    refs = data.get('references', [])
    if not refs:
        return ''
    lines = ['## 関連資料（エビデンス）', '']
    for r in refs:
        title = r.get('title', '-')
        url = r.get('url', '')
        lines.append(f'- [{title}]({url})')
    lines.append('')
    return '\n'.join(lines)


def run_create_human_document(generate_markdown_fn: Callable[[dict], str]) -> None:
    """
    create_human_document の共通エントリポイント。
    argparse で input / -o を取得し、YAML 読み込み → generate_markdown_fn → 出力を行う。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    data = load_yaml(args.input)
    md = generate_markdown_fn(data)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding='utf-8')
        print(f"✅ {args.output}")
    else:
        print(md)
