#!/usr/bin/env python3
"""
ワークフロー自動化ツール
YAMLファイルのバリデーション → Markdown生成 → Mermaid図生成を一括実行します。

使い方:
  # 単一ファイルを処理
  python3 tools/build.py yaml_created_from_ai/bugfix_sample.yaml

  # 全YAMLファイルを処理
  python3 tools/build.py --all

  # バリデーションのみ
  python3 tools/build.py yaml_created_from_ai/bugfix_sample.yaml --validate-only

  # 出力ディレクトリを指定
  python3 tools/build.py yaml_created_from_ai/bugfix_sample.yaml -o custom_output/
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


# デフォルトのディレクトリ設定
DEFAULT_INPUT_DIR = 'yaml_created_from_ai'
DEFAULT_OUTPUT_DIR = 'output_for_human_read'


def get_project_root() -> Path:
    """プロジェクトルートを取得"""
    return Path(__file__).parent.parent


def run_command(cmd: list[str], description: str) -> bool:
    """コマンドを実行し、結果を返す"""
    print(f"  {description}...", end=" ", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅")
        return True
    else:
        print("❌")
        if result.stderr:
            print(f"    エラー: {result.stderr[:200]}")
        return False


def process_yaml(yaml_path: Path, output_dir: Path, validate_only: bool = False) -> bool:
    """
    単一のYAMLファイルを処理
    
    Returns:
        True: 全て成功, False: いずれかが失敗
    """
    project_root = get_project_root()
    tools_dir = project_root / 'tools'
    
    # ファイル名から出力ファイル名を生成
    stem = yaml_path.stem
    md_output = output_dir / f"{stem}.md"
    mermaid_output = output_dir / f"{stem}_diagrams.md"
    
    print(f"\n📄 処理中: {yaml_path.name}")
    print("-" * 40)
    
    success = True
    
    # 1. バリデーション
    cmd = [sys.executable, str(tools_dir / 'validate.py'), str(yaml_path)]
    if not run_command(cmd, "バリデーション"):
        success = False
        if validate_only:
            return False
    
    if validate_only:
        return success
    
    # 2. Markdown生成
    cmd = [
        sys.executable, str(tools_dir / 'to_md.py'),
        str(yaml_path), '-o', str(md_output)
    ]
    if not run_command(cmd, f"Markdown生成 → {md_output.name}"):
        success = False
    
    # 3. Mermaid図生成
    cmd = [
        sys.executable, str(tools_dir / 'to_mermaid.py'),
        str(yaml_path), '-o', str(mermaid_output)
    ]
    if not run_command(cmd, f"Mermaid生成 → {mermaid_output.name}"):
        success = False
    
    return success


def process_all(input_dir: Path, output_dir: Path, validate_only: bool = False) -> tuple[int, int]:
    """
    ディレクトリ内の全YAMLファイルを処理
    
    Returns:
        (成功数, 失敗数)
    """
    yaml_files = list(input_dir.glob('*.yaml')) + list(input_dir.glob('*.yml'))
    
    # invalid_ で始まるファイルはスキップ
    yaml_files = [f for f in yaml_files if not f.name.startswith('invalid_')]
    
    if not yaml_files:
        print(f"⚠️  {input_dir} にYAMLファイルがありません")
        return 0, 0
    
    success_count = 0
    fail_count = 0
    
    for yaml_file in sorted(yaml_files):
        if process_yaml(yaml_file, output_dir, validate_only):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description='YAMLファイルをバリデート → MD/Mermaid生成を一括実行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # 単一ファイルを処理
  python3 tools/build.py yaml_created_from_ai/bugfix_sample.yaml

  # 全YAMLファイルを処理
  python3 tools/build.py --all

  # バリデーションのみ
  python3 tools/build.py --all --validate-only
"""
    )
    parser.add_argument(
        'input',
        nargs='?',
        help='処理するYAMLファイルのパス'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help=f'全YAMLファイルを処理（デフォルト: {DEFAULT_INPUT_DIR}/）'
    )
    parser.add_argument(
        '--input-dir', '-i',
        default=None,
        help=f'入力ディレクトリ（デフォルト: {DEFAULT_INPUT_DIR}）'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=None,
        help=f'出力ディレクトリ（デフォルト: {DEFAULT_OUTPUT_DIR}）'
    )
    parser.add_argument(
        '--validate-only', '-v',
        action='store_true',
        help='バリデーションのみ実行（MD/Mermaid生成をスキップ）'
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    
    # 出力ディレクトリの設定
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = project_root / DEFAULT_OUTPUT_DIR
    
    # 出力ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 50)
    print("🔧 YAML → MD/Mermaid ビルドツール")
    print("=" * 50)
    
    if args.all or (not args.input):
        # 全ファイル処理モード
        if args.input_dir:
            input_dir = Path(args.input_dir)
        else:
            input_dir = project_root / DEFAULT_INPUT_DIR
        
        if not input_dir.exists():
            print(f"❌ 入力ディレクトリが見つかりません: {input_dir}")
            sys.exit(1)
        
        print(f"📂 入力: {input_dir}")
        print(f"📂 出力: {output_dir}")
        
        success, fail = process_all(input_dir, output_dir, args.validate_only)
        
        print("\n" + "=" * 50)
        print(f"📊 結果: 成功 {success} / 失敗 {fail}")
        print("=" * 50)
        
        sys.exit(0 if fail == 0 else 1)
    
    else:
        # 単一ファイル処理モード
        yaml_path = Path(args.input)
        
        if not yaml_path.exists():
            print(f"❌ ファイルが見つかりません: {yaml_path}")
            sys.exit(1)
        
        print(f"📂 出力: {output_dir}")
        
        success = process_yaml(yaml_path, output_dir, args.validate_only)
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 完了")
        else:
            print("❌ エラーあり")
        print("=" * 50)
        
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
