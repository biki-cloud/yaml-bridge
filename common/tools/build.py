#!/usr/bin/env python3
"""
ワークフロー自動化ツール（doc_typeディレクトリ版）
YAMLファイルのバリデーション → Markdown生成（Mermaid図含む）を一括実行します。

使い方:
  # 単一ファイルを処理
  python3 common/tools/build.py categories/development/implementation_plan/ai/document.yaml

  # 全doc_typesを処理
  python3 common/tools/build.py --all

  # 特定カテゴリのみ処理
  python3 common/tools/build.py --category development

  # バリデーションのみ
  python3 common/tools/build.py --all --validate-only
"""

import argparse
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Optional

# common/ を import するため
_common_dir = Path(__file__).resolve().parent.parent
if str(_common_dir) not in sys.path:
    sys.path.insert(0, str(_common_dir))
from config import (
    AI_DOCUMENT_SCHEME_JSON,
    CREATE_HUMAN_DOCUMENT_SCRIPT,
    HUMAN_DOCUMENT_MD,
    AI_DOCUMENT_YAML,
)
from paths import (
    get_project_root,
    get_categories_dir,
    get_available_categories,
    get_doc_types,
)


def detect_doc_type_from_yaml(yaml_path: Path) -> Optional[tuple[str, str]]:
    """YAMLファイルからcategory, doc_typeを検出"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        meta = data.get('meta', {})
        return meta.get('category'), meta.get('doc_type')
    except Exception:
        return None, None


def run_command(cmd: list[str], description: str) -> bool:
    print(f"  {description}...", end=" ", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅")
        return True
    else:
        print("❌")
        if result.stderr:
            stderr = result.stderr
            if 'DeprecationWarning' not in stderr:
                print(f"    エラー: {stderr[:200]}")
        return False


def process_yaml(yaml_path: Path, validate_only: bool = False) -> bool:
    project_root = get_project_root()
    
    category, doc_type = detect_doc_type_from_yaml(yaml_path)
    if not category or not doc_type:
        print(f"  ⚠️  category/doc_typeを検出できません: {yaml_path}")
        return False
    
    doc_type_dir = get_categories_dir() / category / doc_type
    if not doc_type_dir.exists():
        print(f"  ⚠️  doc_typeディレクトリが見つかりません: {doc_type_dir}")
        return False
    
    stem = yaml_path.stem
    md_name = HUMAN_DOCUMENT_MD if stem == Path(AI_DOCUMENT_YAML).stem else f"{stem}.md"
    md_output = doc_type_dir / md_name
    
    print(f"\n📄 処理中: {yaml_path.name} ({category}/{doc_type})")
    print("-" * 40)
    
    success = True
    
    # 1. バリデーション
    validate_script = project_root / 'common' / 'tools' / 'validate.py'
    cmd = [sys.executable, str(validate_script), str(yaml_path)]
    if not run_command(cmd, "バリデーション"):
        success = False
        if validate_only:
            return False
    
    if validate_only:
        return success
    
    # 2. Markdown生成（Mermaid図含む）
    to_md_script = doc_type_dir / CREATE_HUMAN_DOCUMENT_SCRIPT
    if to_md_script.exists():
        cmd = [sys.executable, str(to_md_script), str(yaml_path), '-o', str(md_output)]
        if not run_command(cmd, f"Markdown生成 → {md_output.name}"):
            success = False
    else:
        print(f"  ⚠️  {CREATE_HUMAN_DOCUMENT_SCRIPT} が見つかりません")
        success = False
    
    return success


def process_doc_type(category: str, doc_type: str, validate_only: bool = False) -> tuple[int, int]:
    doc_type_dir = get_categories_dir() / category / doc_type
    ai_dir = doc_type_dir / "ai"
    yaml_files = (
        list(ai_dir.glob("*.yaml")) + list(ai_dir.glob("*.yml"))
        if ai_dir.exists() else []
    )
    yaml_files = [f for f in yaml_files if not f.name.startswith("invalid_")]

    if not yaml_files:
        return 0, 0
    
    success_count = 0
    fail_count = 0
    
    for yaml_file in sorted(yaml_files):
        if process_yaml(yaml_file, validate_only):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count


def process_category(category: str, validate_only: bool = False) -> tuple[int, int]:
    total_success = 0
    total_fail = 0
    
    for doc_type in get_doc_types(category):
        success, fail = process_doc_type(category, doc_type, validate_only)
        total_success += success
        total_fail += fail
    
    return total_success, total_fail


def process_all(validate_only: bool = False) -> tuple[int, int]:
    total_success = 0
    total_fail = 0
    
    for category in get_available_categories():
        print(f"\n📦 カテゴリ: {category}")
        print("=" * 50)
        success, fail = process_category(category, validate_only)
        total_success += success
        total_fail += fail
    
    return total_success, total_fail


def main():
    parser = argparse.ArgumentParser(description='YAMLファイルをバリデート → MD生成（Mermaid含む）を一括実行')
    parser.add_argument('input', nargs='?', help='処理するYAMLファイルのパス')
    parser.add_argument('--all', '-a', action='store_true', help='全カテゴリを処理')
    parser.add_argument('--category', '-c', default=None, help='特定カテゴリのみ処理')
    parser.add_argument('--validate-only', '-v', action='store_true', help='バリデーションのみ')
    parser.add_argument('--list', action='store_true', help='カテゴリ/doc_type一覧を表示')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🔧 YAML → Markdown ビルドツール")
    print("=" * 50)
    
    if args.list:
        print("\n利用可能なカテゴリ/doc_type:")
        for category in get_available_categories():
            print(f"\n📦 {category}")
            for doc_type in get_doc_types(category):
                print(f"   └─ {doc_type}")
        sys.exit(0)
    
    if args.all:
        success, fail = process_all(args.validate_only)
        print("\n" + "=" * 50)
        print(f"📊 結果: 成功 {success} / 失敗 {fail}")
        print("=" * 50)
        sys.exit(0 if fail == 0 else 1)
    
    elif args.category:
        available = get_available_categories()
        if args.category not in available:
            print(f"❌ 未知のカテゴリ: {args.category}")
            print(f"   利用可能: {', '.join(available)}")
            sys.exit(1)
        
        success, fail = process_category(args.category, args.validate_only)
        print("\n" + "=" * 50)
        print(f"📊 結果: 成功 {success} / 失敗 {fail}")
        print("=" * 50)
        sys.exit(0 if fail == 0 else 1)
    
    elif args.input:
        yaml_path = Path(args.input)
        if not yaml_path.exists():
            print(f"❌ ファイルが見つかりません: {yaml_path}")
            sys.exit(1)
        
        success = process_yaml(yaml_path, args.validate_only)
        print("\n" + "=" * 50)
        print("✅ 完了" if success else "❌ エラーあり")
        print("=" * 50)
        sys.exit(0 if success else 1)
    
    else:
        success, fail = process_all(args.validate_only)
        print("\n" + "=" * 50)
        print(f"📊 結果: 成功 {success} / 失敗 {fail}")
        print("=" * 50)
        sys.exit(0 if fail == 0 else 1)


if __name__ == '__main__':
    main()
