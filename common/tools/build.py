#!/usr/bin/env python3
"""
ワークフロー自動化ツール（doc_typeディレクトリ版）
YAMLファイルのバリデーション → Markdown生成（Mermaid図含む）を一括実行します。

使い方:
  # 単一ファイルを処理
  python3 common/tools/build.py categories/development/implementation_plan/samples/sample.yaml

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


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_categories_dir() -> Path:
    return get_project_root() / 'categories'


def get_available_categories() -> list[str]:
    categories_dir = get_categories_dir()
    if not categories_dir.exists():
        return []
    
    categories = []
    for d in categories_dir.iterdir():
        if d.is_dir() and not d.name.startswith('_'):
            # doc_typeサブディレクトリがあるカテゴリのみ
            for sub in d.iterdir():
                if sub.is_dir() and (sub / 'schema.json').exists():
                    categories.append(d.name)
                    break
    return sorted(categories)


def get_doc_types(category: str) -> list[str]:
    category_dir = get_categories_dir() / category
    if not category_dir.exists():
        return []
    
    doc_types = []
    for d in category_dir.iterdir():
        if d.is_dir() and (d / 'schema.json').exists():
            doc_types.append(d.name)
    return sorted(doc_types)


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
    
    output_dir = doc_type_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stem = yaml_path.stem
    md_output = output_dir / f"{stem}.md"
    
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
    to_md_script = doc_type_dir / 'to_md.py'
    if to_md_script.exists():
        cmd = [sys.executable, str(to_md_script), str(yaml_path), '-o', str(md_output)]
        if not run_command(cmd, f"Markdown生成 → {md_output.name}"):
            success = False
    else:
        print(f"  ⚠️  to_md.py が見つかりません")
        success = False
    
    return success


def process_doc_type(category: str, doc_type: str, validate_only: bool = False) -> tuple[int, int]:
    doc_type_dir = get_categories_dir() / category / doc_type
    samples_dir = doc_type_dir / 'samples'
    
    if not samples_dir.exists():
        return 0, 0
    
    yaml_files = list(samples_dir.glob('*.yaml')) + list(samples_dir.glob('*.yml'))
    yaml_files = [f for f in yaml_files if not f.name.startswith('invalid_')]
    
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
