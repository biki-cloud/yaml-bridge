#!/usr/bin/env python3
"""
プロジェクトルート・カテゴリ・doc_type のパス解決。
build.py / validate.py で共通利用。
"""

from pathlib import Path

# config は paths から見て同階層
from config import AI_DOCUMENT_SCHEME_JSON


def get_project_root() -> Path:
    """common/ の親 = プロジェクトルート"""
    return Path(__file__).resolve().parent.parent


def get_categories_dir() -> Path:
    return get_project_root() / 'categories'


def get_available_categories() -> list[str]:
    """ai_document_scheme.json が存在する doc_type を持つカテゴリのみ返す"""
    categories_dir = get_categories_dir()
    if not categories_dir.exists():
        return []

    categories = []
    for d in categories_dir.iterdir():
        if d.is_dir() and not d.name.startswith('_'):
            for sub in d.iterdir():
                if sub.is_dir() and (sub / AI_DOCUMENT_SCHEME_JSON).exists():
                    categories.append(d.name)
                    break
    return sorted(categories)


def get_doc_types(category: str) -> list[str]:
    """指定カテゴリ内の doc_type 一覧（スキーマが存在するもののみ）"""
    category_dir = get_categories_dir() / category
    if not category_dir.exists():
        return []

    doc_types = []
    for d in category_dir.iterdir():
        if d.is_dir() and (d / AI_DOCUMENT_SCHEME_JSON).exists():
            doc_types.append(d.name)
    return sorted(doc_types)
