#!/usr/bin/env python3
"""
プロジェクトルート・カテゴリ・doc_type のパス解決。
build.py / validate.py / 各 create_human_document.py で共通利用。
"""

from pathlib import Path
from typing import Iterator

# config は paths から見て同階層
from config import AI_DOCUMENT_SCHEME_JSON, AI_DOCUMENT_YAML, HUMAN_DOCUMENT_MD

# カテゴリの表示順・処理順（project_summary / wbs 等で共通利用）
DOC_CATEGORIES = ('overview', 'design', 'development', 'investigation', 'verification')

# カテゴリ名 → 表示ラベル（WBS・open_items 等で共通利用）
DOC_CATEGORY_LABELS = {
    'overview': '概要',
    'design': '設計',
    'development': '開発',
    'investigation': '調査',
    'verification': '動作確認',
}


def get_project_root() -> Path:
    """common/ の親 = プロジェクトルート"""
    return Path(__file__).resolve().parent.parent


def get_categories_dir() -> Path:
    """categories ディレクトリの絶対パス"""
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


def get_category_label(category: str) -> str:
    """カテゴリ名の表示ラベルを返す（未定義ならそのまま返す）"""
    return DOC_CATEGORY_LABELS.get(category, category)


def get_all_category_doc_type_pairs() -> list[tuple[str, str]]:
    """全 (category, doc_type) を DOC_CATEGORIES 順で返す（存在するもののみ）"""
    available = set(get_available_categories())
    pairs = []
    for category in DOC_CATEGORIES:
        if category not in available:
            continue
        for doc_type in get_doc_types(category):
            pairs.append((category, doc_type))
    return pairs


def get_doc_type_dir(category: str, doc_type: str) -> Path:
    """指定 (category, doc_type) のディレクトリの絶対パス（例: .../categories/overview/change_log）"""
    return get_categories_dir() / category / doc_type


def get_doc_type_dir_relative(category: str, doc_type: str) -> Path:
    """指定 (category, doc_type) のディレクトリのプロジェクトルート相対パス（例: categories/overview/change_log）"""
    return Path('categories') / category / doc_type


def get_ai_document_path(category: str, doc_type: str) -> Path:
    """指定 (category, doc_type) の ai/document.yaml の絶対パス"""
    return get_doc_type_dir(category, doc_type) / AI_DOCUMENT_YAML


def get_human_document_path(category: str, doc_type: str) -> Path:
    """指定 (category, doc_type) の human/document.md の絶対パス"""
    return get_doc_type_dir(category, doc_type) / HUMAN_DOCUMENT_MD


def iter_doc_type_dirs() -> Iterator[tuple[str, str, Path]]:
    """全 (category, doc_type) について (category, doc_type, 絶対パス) を yield する"""
    for category in get_available_categories():
        for doc_type in get_doc_types(category):
            yield category, doc_type, get_doc_type_dir(category, doc_type)
