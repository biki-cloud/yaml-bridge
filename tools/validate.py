#!/usr/bin/env python3
"""
設計YAML 汎用バリデーションツール
meta.type フィールドからスキーマを自動検出して検証します。
"""

import yaml
import json
import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError, RefResolver
except ImportError:
    print("❌ jsonschema パッケージがインストールされていません")
    print("   pip install jsonschema でインストールしてください")
    sys.exit(1)


# 案件タイプとスキーマファイルの対応
SCHEMA_MAP = {
    'api_design': 'api_design.schema.json',
    'feature_design': 'feature_design.schema.json',
    'bugfix': 'bugfix.schema.json',
    'infrastructure': 'infrastructure.schema.json',
}


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_schema(schema_path: Path) -> dict:
    """JSON Schemaファイルを読み込む"""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_schemas_dir() -> Path:
    """スキーマディレクトリのパスを取得"""
    tools_dir = Path(__file__).parent
    return tools_dir.parent / 'schemas'


def detect_schema_type(yaml_data: dict) -> Optional[str]:
    """YAMLデータからスキーマタイプを検出"""
    meta = yaml_data.get('meta', {})
    return meta.get('type')


def create_resolver(schema: dict, schema_dir: Path) -> RefResolver:
    """$ref を解決するためのリゾルバを作成"""
    # ファイルURIベースでリゾルバを作成
    base_uri = f"file://{schema_dir}/"
    
    # スキーマストアを作成（全スキーマをロード）
    store = {}
    for schema_file in schema_dir.glob('*.schema.json'):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = json.load(f)
            schema_id = schema_content.get('$id', schema_file.name)
            store[schema_id] = schema_content
            # ファイル名でもアクセスできるように
            store[schema_file.name] = schema_content
    
    return RefResolver(base_uri, schema, store=store)


def format_error_path(error: ValidationError) -> str:
    """エラーのパスをフォーマット"""
    if error.absolute_path:
        return ' → '.join(str(p) for p in error.absolute_path)
    return '(ルート)'


def validate_yaml(yaml_data: dict, schema: dict, resolver: RefResolver, verbose: bool = False) -> tuple[bool, list[str]]:
    """
    YAMLデータをJSON Schemaで検証する
    
    Returns:
        (is_valid, error_messages)
    """
    validator = Draft7Validator(schema, resolver=resolver)
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
    """共通の追加チェック"""
    warnings = []
    
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
    
    # ステータスがdraftでないのにauthor/datesがない
    meta = yaml_data.get('meta', {})
    if meta.get('status') in ['review', 'approved'] and not meta.get('author'):
        warnings.append("⚠️ ステータスがreview/approvedですが、作成者(author)が定義されていません")
    
    return warnings


def run_api_design_checks(yaml_data: dict) -> list[str]:
    """API設計固有のチェック"""
    warnings = []
    
    # 破壊的変更があるのにmigration戦略がない場合の警告
    if 'changes' in yaml_data:
        has_breaking = any(c.get('breaking') for c in yaml_data['changes'])
        if has_breaking:
            if 'migration' not in yaml_data:
                warnings.append("⚠️ 破壊的変更がありますが、移行計画(migration)が定義されていません")
            elif 'rollback_plan' not in yaml_data.get('migration', {}):
                warnings.append("⚠️ 破壊的変更がありますが、ロールバック計画が定義されていません")
    
    # as_is と to_be の両方がない場合の警告
    if 'as_is' not in yaml_data and 'to_be' not in yaml_data:
        warnings.append("⚠️ 現状(as_is)と改修後(to_be)の仕様が両方とも定義されていません")
    
    return warnings


def run_feature_design_checks(yaml_data: dict) -> list[str]:
    """新機能設計固有のチェック"""
    warnings = []
    
    # 必須要件がない場合の警告
    requirements = yaml_data.get('requirements', {})
    functional = requirements.get('functional', [])
    must_requirements = [r for r in functional if r.get('priority') == 'must']
    if functional and not must_requirements:
        warnings.append("⚠️ must優先度の機能要件がありません")
    
    # アーキテクチャ決定がない場合の警告
    if 'architecture' not in yaml_data:
        warnings.append("⚠️ アーキテクチャ設計(architecture)が定義されていません")
    
    return warnings


def run_bugfix_checks(yaml_data: dict) -> list[str]:
    """バグ修正固有のチェック"""
    warnings = []
    
    # 再現手順がない場合の警告
    symptom = yaml_data.get('symptom', {})
    if not symptom.get('reproduction_steps'):
        warnings.append("⚠️ 再現手順(reproduction_steps)が定義されていません")
    
    # 検証計画がない場合の警告
    if 'verification' not in yaml_data:
        warnings.append("⚠️ 検証計画(verification)が定義されていません")
    
    # 再発防止策がない場合の警告
    if 'prevention' not in yaml_data:
        warnings.append("⚠️ 再発防止策(prevention)が定義されていません")
    
    return warnings


def run_infrastructure_checks(yaml_data: dict) -> list[str]:
    """インフラ構築固有のチェック"""
    warnings = []
    
    # 現状構成がない場合の警告
    if 'current_state' not in yaml_data:
        warnings.append("⚠️ 現状のインフラ構成(current_state)が定義されていません")
    
    # セキュリティ設計がない場合の警告
    if 'security' not in yaml_data:
        warnings.append("⚠️ セキュリティ設計(security)が定義されていません")
    
    # 監視設計がない場合の警告
    if 'monitoring' not in yaml_data:
        warnings.append("⚠️ 監視設計(monitoring)が定義されていません")
    
    # コスト見積もりがない場合の警告
    if 'cost' not in yaml_data:
        warnings.append("⚠️ コスト見積もり(cost)が定義されていません")
    
    return warnings


def run_additional_checks(yaml_data: dict, schema_type: str) -> tuple[bool, list[str]]:
    """
    スキーマでは表現しにくい追加のビジネスルールチェック
    
    Returns:
        (is_valid, warning_messages)
    """
    warnings = []
    
    # 共通チェック
    warnings.extend(run_common_checks(yaml_data))
    
    # タイプ固有のチェック
    type_checks = {
        'api_design': run_api_design_checks,
        'feature_design': run_feature_design_checks,
        'bugfix': run_bugfix_checks,
        'infrastructure': run_infrastructure_checks,
    }
    
    if schema_type in type_checks:
        warnings.extend(type_checks[schema_type](yaml_data))
    
    return len(warnings) == 0, warnings


def main():
    parser = argparse.ArgumentParser(
        description='設計YAMLをバリデートします（スキーマ自動検出）'
    )
    parser.add_argument(
        'input',
        help='入力YAMLファイルのパス'
    )
    parser.add_argument(
        '-s', '--schema',
        default=None,
        help='JSON Schemaファイルのパス（省略時はmeta.typeから自動検出）'
    )
    parser.add_argument(
        '-t', '--type',
        choices=list(SCHEMA_MAP.keys()),
        default=None,
        help='案件タイプを明示的に指定（省略時はmeta.typeから自動検出）'
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
    parser.add_argument(
        '--list-types',
        action='store_true',
        help='利用可能な案件タイプを表示'
    )
    
    args = parser.parse_args()
    
    # タイプ一覧表示
    if args.list_types:
        print("利用可能な案件タイプ:")
        for type_name, schema_file in SCHEMA_MAP.items():
            print(f"  - {type_name}: {schema_file}")
        sys.exit(0)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 入力ファイルが見つかりません: {input_path}")
        sys.exit(1)
    
    # ファイル読み込み
    try:
        yaml_data = load_yaml(args.input)
    except yaml.YAMLError as e:
        print(f"❌ YAMLの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    # スキーマパスの解決
    schemas_dir = get_schemas_dir()
    
    if args.schema:
        schema_path = Path(args.schema)
        schema_type = args.type or detect_schema_type(yaml_data) or 'unknown'
    else:
        # スキーマの自動検出
        schema_type = args.type or detect_schema_type(yaml_data)
        
        if not schema_type:
            print("❌ スキーマタイプを検出できません")
            print("   meta.type フィールドを指定するか、--type オプションを使用してください")
            print(f"   利用可能なタイプ: {', '.join(SCHEMA_MAP.keys())}")
            sys.exit(1)
        
        if schema_type not in SCHEMA_MAP:
            print(f"❌ 未知のスキーマタイプ: {schema_type}")
            print(f"   利用可能なタイプ: {', '.join(SCHEMA_MAP.keys())}")
            sys.exit(1)
        
        schema_path = schemas_dir / SCHEMA_MAP[schema_type]
    
    if not schema_path.exists():
        print(f"❌ スキーマファイルが見つかりません: {schema_path}")
        sys.exit(1)
    
    print(f"📄 検証対象: {input_path}")
    print(f"📋 スキーマ: {schema_path}")
    print(f"📁 タイプ: {schema_type}")
    print()
    
    try:
        schema = load_schema(schema_path)
    except json.JSONDecodeError as e:
        print(f"❌ スキーマの解析に失敗しました:")
        print(f"   {e}")
        sys.exit(1)
    
    # リゾルバを作成（$ref 解決用）
    resolver = create_resolver(schema, schemas_dir)
    
    # スキーマバリデーション
    print("🔍 スキーマ検証中...")
    is_valid, errors = validate_yaml(yaml_data, schema, resolver, args.verbose)
    
    if errors:
        print()
        print("=== エラー ===")
        for error in errors:
            print(error)
    
    # 追加チェック
    print()
    print("🔍 追加チェック中...")
    additional_ok, warnings = run_additional_checks(yaml_data, schema_type)
    
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
