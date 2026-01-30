#!/usr/bin/env python3
"""
全カテゴリの open_items を 1 つの Markdown に集約する。
PM が「全検討事項・不明点を一覧で見たい」ときに利用する。

使い方:
  python3 common/tools/build_open_items_aggregate.py
  python3 common/tools/build_open_items_aggregate.py -o docs/open_items_all.md
"""

import sys
from pathlib import Path

_common_dir = Path(__file__).resolve().parent.parent
if str(_common_dir) not in sys.path:
    sys.path.insert(0, str(_common_dir))
from paths import get_categories_dir, get_available_categories, get_doc_types, get_project_root
from md_base import load_yaml, generate_open_items_markdown


def build_open_items_aggregate(output_path: Path | None = None) -> str:
    """全カテゴリの open_items YAML を読み、1 つの Markdown 文字列を返す。"""
    categories_dir = get_categories_dir()
    project_root = get_project_root()
    lines = [
        "# 検討事項・不明点 一覧（全カテゴリ）",
        "",
        "PM 向け：全カテゴリの検討事項・不明点を一覧にしています。",
        "",
    ]
    categories_with_open_items = [
        c for c in get_available_categories()
        if "open_items" in get_doc_types(c)
    ]
    for category in sorted(categories_with_open_items):
        yaml_path = categories_dir / category / "open_items" / "ai" / "document.yaml"
        if not yaml_path.exists():
            continue
        try:
            data = load_yaml(str(yaml_path))
        except Exception:
            continue
        body = generate_open_items_markdown(data, output_path=output_path).strip()
        # 先頭の # タイトル行を「## カテゴリ: {category}」に差し替え
        body_lines = body.split("\n")
        if body_lines and body_lines[0].startswith("# "):
            body_lines = body_lines[1:]
        rest = "\n".join(body_lines).lstrip()
        lines.append(f"## カテゴリ: {category}")
        lines.append("")
        lines.append(rest)
        lines.append("")
    md = "\n".join(lines).rstrip()
    # 出力が docs/ 以下のとき、プロジェクトルート相対のリンクを相対パスに変換
    if output_path and "docs" in str(output_path):
        md = md.replace("](categories/", "](../categories/")
    return md


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="全カテゴリの open_items を 1 つの MD に集約")
    parser.add_argument("-o", "--output", default=None, help="出力ファイルパス（省略時は標準出力）")
    args = parser.parse_args()
    output_path = Path(args.output).resolve() if args.output else None
    md = build_open_items_aggregate(output_path=output_path)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"✅ {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
