#!/usr/bin/env python3
"""
Markdown生成用の共通ヘルパー関数
各タイプの create_human_document.py から利用されます。
"""

import yaml


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
