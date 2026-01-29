#!/usr/bin/env python3
"""
設計YAML 汎用バリデーションツール（doc_typeディレクトリ版）
meta.category + meta.doc_type からスキーマを自動検出して検証します。
"""

import yaml
import json
import argparse
import sys
from pathlib import Path
from typing import Optional

# common/config.py を import するため
_common_dir = Path(__file__).resolve().parent.parent
if str(_common_dir) not in sys.path:
    sys.path.insert(0, str(_common_dir))
from config import AI_DOCUMENT_SCHEME_JSON

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("❌ jsonschema パッケージがインストールされていません")
    print("   pip install jsonschema でインストールしてください")
    sys.exit(1)


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_categories_dir() -> Path:
    return get_project_root() / 'categories'


def get_schema_path(category: str, doc_type: str) -> Optional[Path]:
    """category/doc_typeに対応するスキーマパスを取得"""
    schema_path = get_categories_dir() / category / doc_type / AI_DOCUMENT_SCHEME_JSON
    return schema_path if schema_path.exists() else None


def load_yaml(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_schema(schema_path: Path) -> dict:
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_category_and_doc_type(yaml_data: dict) -> tuple[Optional[str], Optional[str]]:
    """YAMLデータからcategory, doc_typeを検出"""
    meta = yaml_data.get('meta', {})
    return meta.get('category'), meta.get('doc_type')


def format_error_path(error: ValidationError) -> str:
    if error.absolute_path:
        return ' → '.join(str(p) for p in error.absolute_path)
    return '(ルート)'


def validate_yaml(yaml_data: dict, schema: dict, verbose: bool = False) -> tuple[bool, list[str]]:
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(yaml_data))
    
    if not errors:
        return True, []
    
    error_messages = []
    for error in sorted(errors, key=lambda e: str(list(e.absolute_path))):
        path = format_error_path(error)
        message = error.message
        
        if verbose:
            error_messages.append(f"❌ [{path}] {message}")
            if error.context:
                for suberror in error.context:
                    error_messages.append(f"   └─ {suberror.message}")
        else:
            error_messages.append(f"❌ [{path}] {message}")
    
    return False, error_messages


def run_common_checks(yaml_data: dict) -> list[str]:
    warnings = []
    
    meta = yaml_data.get('meta', {})
    if meta.get('status') == 'done' and not meta.get('author'):
        warnings.append("⚠️ ステータスがdoneですが、作成者(author)が定義されていません")
    
    return warnings


def main():
    parser = argparse.ArgumentParser(description='設計YAMLをバリデートします')
    parser.add_argument('input', help='入力YAMLファイルのパス')
    parser.add_argument('-s', '--schema', default=None, help='JSON Schemaファイルのパス')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細なエラー情報を表示')
    parser.add_argument('--strict', action='store_true', help='警告もエラーとして扱う')
    parser.add_argument('--list', action='store_true', help='利用可能なcategory/doc_typeを表示')
    
    args = parser.parse_args()
    
    if args.list:
        print("利用可能なcategory/doc_type:")
        for cat_dir in get_categories_dir().iterdir():
            if cat_dir.is_dir() and not cat_dir.name.startswith('_'):
                doc_types = []
                for dt_dir in cat_dir.iterdir():
                    if dt_dir.is_dir() and (dt_dir / AI_DOCUMENT_SCHEME_JSON).exists():
                        doc_types.append(dt_dir.name)
                if doc_types:
                    print(f"\n📦 {cat_dir.name}")
                    for dt in sorted(doc_types):
                        print(f"   └─ {dt}")
        sys.exit(0)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 入力ファイルが見つかりません: {input_path}")
        sys.exit(1)
    
    try:
        yaml_data = load_yaml(args.input)
    except yaml.YAMLError as e:
        print(f"❌ YAMLの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    # スキーマパスの解決
    if args.schema:
        schema_path = Path(args.schema)
        category, doc_type = detect_category_and_doc_type(yaml_data)
    else:
        category, doc_type = detect_category_and_doc_type(yaml_data)
        
        if not category or not doc_type:
            print("❌ category/doc_typeを検出できません")
            print("   meta.category, meta.doc_type フィールドを指定してください")
            sys.exit(1)
        
        schema_path = get_schema_path(category, doc_type)
        
        if not schema_path:
            print(f"❌ スキーマが見つかりません: {category}/{doc_type}")
            sys.exit(1)
    
    if not schema_path.exists():
        print(f"❌ スキーマファイルが見つかりません: {schema_path}")
        sys.exit(1)
    
    print(f"📄 検証対象: {input_path}")
    print(f"📋 スキーマ: {schema_path}")
    print(f"📁 パス: {category}/{doc_type}")
    print()
    
    try:
        schema = load_schema(schema_path)
    except json.JSONDecodeError as e:
        print(f"❌ スキーマの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    print("🔍 スキーマ検証中...")
    is_valid, errors = validate_yaml(yaml_data, schema, args.verbose)
    
    if errors:
        print()
        print("=== エラー ===")
        for error in errors:
            print(error)
    
    print()
    print("🔍 追加チェック中...")
    warnings = run_common_checks(yaml_data)
    
    if warnings:
        print()
        print("=== 警告 ===")
        for warning in warnings:
            print(warning)
    
    print()
    print("=" * 40)
    
    if is_valid and (not warnings or not args.strict):
        if warnings:
            print(f"✅ バリデーション成功（警告 {len(warnings)} 件）")
        else:
            print("✅ バリデーション成功")
        sys.exit(0)
    else:
        error_count = len(errors)
        warning_count = len(warnings)
        if args.strict:
            print(f"❌ バリデーション失敗（エラー {error_count} 件、警告 {warning_count} 件）")
        else:
            print(f"❌ バリデーション失敗（エラー {error_count} 件）")
        sys.exit(1)


if __name__ == '__main__':
    main()
