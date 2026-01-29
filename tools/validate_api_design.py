#!/usr/bin/env python3
"""
API設計YAML バリデーションツール
JSON Schemaを使用してAPI設計YAMLファイルを検証します。
"""

import yaml
import json
import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
except ImportError:
    print("❌ jsonschema パッケージがインストールされていません")
    print("   pip install jsonschema でインストールしてください")
    sys.exit(1)


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_schema(schema_path: str) -> dict:
    """JSON Schemaファイルを読み込む"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_error_path(error: ValidationError) -> str:
    """エラーのパスをフォーマット"""
    if error.absolute_path:
        return ' → '.join(str(p) for p in error.absolute_path)
    return '(ルート)'


def validate_yaml(yaml_data: dict, schema: dict, verbose: bool = False) -> tuple[bool, list[str]]:
    """
    YAMLデータをJSON Schemaで検証する
    
    Returns:
        (is_valid, error_messages)
    """
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


def run_additional_checks(yaml_data: dict) -> tuple[bool, list[str]]:
    """
    スキーマでは表現しにくい追加のビジネスルールチェック
    
    Returns:
        (is_valid, warning_messages)
    """
    warnings = []
    
    # 破壊的変更があるのにmigration戦略がない場合の警告
    if 'changes' in yaml_data:
        has_breaking = any(c.get('breaking') for c in yaml_data['changes'])
        if has_breaking:
            if 'migration' not in yaml_data:
                warnings.append("⚠️ 破壊的変更がありますが、移行計画(migration)が定義されていません")
            elif 'rollback_plan' not in yaml_data.get('migration', {}):
                warnings.append("⚠️ 破壊的変更がありますが、ロールバック計画が定義されていません")
    
    # リスクの深刻度がhigh以上なのに対策が短すぎる場合の警告
    if 'risks' in yaml_data:
        for i, risk in enumerate(yaml_data['risks']):
            severity = risk.get('severity', '')
            mitigation = risk.get('mitigation', '')
            if severity in ['high', 'critical'] and len(mitigation) < 20:
                warnings.append(f"⚠️ risks[{i}]: 高リスクですが、対策の記述が短すぎる可能性があります")
    
    # テスト計画がない場合の警告
    if 'testing' not in yaml_data:
        warnings.append("⚠️ テスト計画(testing)が定義されていません")
    
    # as_is と to_be の両方がない場合の警告
    if 'as_is' not in yaml_data and 'to_be' not in yaml_data:
        warnings.append("⚠️ 現状(as_is)と改修後(to_be)の仕様が両方とも定義されていません")
    
    # ステータスがdraftでないのにauthor/datesがない
    meta = yaml_data.get('meta', {})
    if meta.get('status') in ['review', 'approved'] and not meta.get('author'):
        warnings.append("⚠️ ステータスがreview/approvedですが、作成者(author)が定義されていません")
    
    return len(warnings) == 0, warnings


def main():
    parser = argparse.ArgumentParser(
        description='API設計YAMLをバリデートします'
    )
    parser.add_argument(
        'input',
        help='入力YAMLファイルのパス'
    )
    parser.add_argument(
        '-s', '--schema',
        default=None,
        help='JSON Schemaファイルのパス（省略時はデフォルトスキーマを使用）'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細なエラー情報を表示'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='警告もエラーとして扱う'
    )
    
    args = parser.parse_args()
    
    # スキーマパスの解決
    if args.schema:
        schema_path = Path(args.schema)
    else:
        # デフォルトスキーマ: toolsディレクトリの親の schemas/api_design.schema.json
        tools_dir = Path(__file__).parent
        schema_path = tools_dir.parent / 'schemas' / 'api_design.schema.json'
    
    if not schema_path.exists():
        print(f"❌ スキーマファイルが見つかりません: {schema_path}")
        sys.exit(1)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 入力ファイルが見つかりません: {input_path}")
        sys.exit(1)
    
    print(f"📄 検証対象: {input_path}")
    print(f"📋 スキーマ: {schema_path}")
    print()
    
    # ファイル読み込み
    try:
        yaml_data = load_yaml(args.input)
    except yaml.YAMLError as e:
        print(f"❌ YAMLの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    try:
        schema = load_schema(str(schema_path))
    except json.JSONDecodeError as e:
        print(f"❌ スキーマの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    # スキーマバリデーション
    print("🔍 スキーマ検証中...")
    is_valid, errors = validate_yaml(yaml_data, schema, args.verbose)
    
    if errors:
        print()
        print("=== エラー ===")
        for error in errors:
            print(error)
    
    # 追加チェック
    print()
    print("🔍 追加チェック中...")
    additional_ok, warnings = run_additional_checks(yaml_data)
    
    if warnings:
        print()
        print("=== 警告 ===")
        for warning in warnings:
            print(warning)
    
    # 結果サマリー
    print()
    print("=" * 40)
    
    if is_valid and (additional_ok or not args.strict):
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
