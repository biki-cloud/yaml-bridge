#!/usr/bin/env python3
"""
doc_type ディレクトリで使うファイル名の一元管理。
build / validate / 各 create_human_document.py で参照する。
"""

# AI が編集する YAML（ビルド対象）
AI_DOCUMENT_YAML = "ai_document.yaml"

# 生成される Markdown（人間向け）
HUMAN_DOCUMENT_MD = "human_document.md"

# YAML → Markdown 生成スクリプト
CREATE_HUMAN_DOCUMENT_SCRIPT = "create_human_document.py"

# ガイド・テンプレート（ビルド対象外）
AI_DOCUMENT_GUIDE_YAML = "ai_document_guide.yaml"

# JSON Schema（バリデーション用）
AI_DOCUMENT_SCHEME_JSON = "ai_document_scheme.json"
