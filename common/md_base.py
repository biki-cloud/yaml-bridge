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
        Path(args.output).write_text(md, encoding='utf-8')
        print(f"✅ {args.output}")
    else:
        print(md)
