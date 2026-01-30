#!/usr/bin/env python3
"""
Markdown生成用の共通ヘルパー関数
各タイプの create_human_document.py から利用されます。
"""

import argparse
import os
import yaml
from pathlib import Path
from typing import Callable, Optional


def load_yaml(file_path: str) -> dict:
    """YAMLファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def format_status(status: str) -> str:
    """meta.status を表示用ラベルに変換"""
    return {'todo': '⬜ TODO', 'wip': '🔄 WIP', 'done': '✅ Done'}.get(status, status)


def _mermaid_sanitize_id(raw: str) -> str:
    """MermaidノードID用: 英数字・アンダースコアのみにする"""
    if not raw:
        return 'n'
    s = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(raw))
    return s or 'n'


def _mermaid_quote_label(label: str, max_len: int = 40) -> str:
    """Mermaidラベル: 括弧・コロン等を含む場合はダブルクォートで囲む"""
    if not label:
        return '""'
    short = label[:max_len] + ('...' if len(label) > max_len else '')
    if any(c in short for c in '():[],'):
        return '"' + short.replace('"', '\\"') + '"'
    return short


def format_ai_context_section(data: dict) -> str:
    """
    data['ai_context'] から「AIの現在の考え」「これからのアクション」「判断・進め方の流れ」の
    Markdown セクションと Mermaid 図を生成する。全 create_human_document.py で共通利用。
    """
    ctx = data.get('ai_context')
    if not ctx:
        return ''

    lines = []

    # --- 現在の考え: マインドマップ + 箇条書き ---
    thinking = ctx.get('current_thinking')
    if thinking is not None:
        items = thinking if isinstance(thinking, list) else [s.strip() for s in str(thinking).splitlines() if s.strip()]
        if items:
            lines.append('## AIの現在の考え')
            lines.append('')
            # Mermaid mindmap（ルートは短く、枝は1項目ずつ・短く）
            lines.append('```mermaid')
            lines.append('mindmap')
            lines.append('  root((現在の考え))')
            for i, item in enumerate(items[:8]):
                short = item[:25] + ('...' if len(item) > 25 else '')
                safe = short.replace('"', '\\"')
                lines.append(f'    item{i + 1} "{safe}"')
            lines.append('```')
            lines.append('')
            for item in items:
                lines.append(f'- {item}')
            lines.append('')

    # --- これからのアクション: フローチャート ---
    actions = ctx.get('next_actions') or []
    if actions:
        lines.append('## これからのアクション')
        lines.append('')
        lines.append('```mermaid')
        lines.append('flowchart TB')
        prev_id = None
        for a in actions:
            nid = _mermaid_sanitize_id(a.get('id', ''))
            label = _mermaid_quote_label(a.get('label', ''))
            lines.append(f'    {nid}[{label}]')
            if prev_id is not None:
                lines.append(f'    {prev_id} --> {nid}')
            prev_id = nid
        lines.append('```')
        lines.append('')
        for a in actions:
            detail = a.get('detail', '')
            if detail:
                lines.append(f"- **{a.get('label', '-')}**: {detail}")
            else:
                lines.append(f"- {a.get('label', '-')}")
        lines.append('')

    # --- 判断・進め方の流れ: フローチャート（任意） ---
    flow = ctx.get('decision_flow') or []
    if flow:
        lines.append('## 判断・進め方の流れ')
        lines.append('')
        lines.append('```mermaid')
        lines.append('flowchart TB')
        seen = set()
        for node in flow:
            nid = _mermaid_sanitize_id(node.get('id', ''))
            label = _mermaid_quote_label(node.get('label', ''))
            if nid not in seen:
                lines.append(f'    {nid}[{label}]')
                seen.add(nid)
            next_id = node.get('next')
            if next_id:
                lines.append(f'    {nid} --> {_mermaid_sanitize_id(next_id)}')
            for cond_next in node.get('next_condition', []):
                lines.append(f'    {nid} --> {_mermaid_sanitize_id(cond_next)}')
        lines.append('```')
        lines.append('')

    return '\n'.join(lines).rstrip()


def _ref_url_for_markdown(url: str, output_path: Optional[Path]) -> str:
    """
    参照URLを Markdown 用のリンク先に変換する。
    output_path が渡された場合、プロジェクトルート基準のファイルパスを
    出力ファイル位置からの相対パスに変換する（クリックで辿れるようにする）。
    人が読むため、ai/document.yaml は human/document.md へのリンクに変換する。
    """
    if not url or not url.strip():
        return url
    s = url.strip()
    if s.startswith('http://') or s.startswith('https://') or s.startswith('file://'):
        return s
    if output_path is None:
        return s
    try:
        # 人が読む用なので ai/document.yaml → human/document.md に差し替え
        if 'ai/document.yaml' in s:
            s = s.replace('ai/document.yaml', 'human/document.md')
        elif 'ai/document.yml' in s:
            s = s.replace('ai/document.yml', 'human/document.md')
        out_dir = output_path.resolve().parent
        project_root = out_dir.parent.parent.parent.parent
        target = (project_root / s).resolve()
        if not target.exists():
            return s
        rel = os.path.relpath(target, out_dir)
        return rel.replace('\\', '/')
    except (ValueError, OSError):
        return s


def format_references_section(data: dict, output_path: Optional[Path] = None) -> str:
    """
    data['references'] から「関連資料（エビデンス）」セクションの Markdown 文字列を生成する。
    output_path を渡すと、ファイルパスを出力ファイルからの相対パスに変換する。
    全 create_human_document.py で共通利用。
    """
    refs = data.get('references', [])
    if not refs:
        return ''
    lines = ['## 関連資料（エビデンス）', '']
    for r in refs:
        title = r.get('title', '-')
        url = r.get('url', '')
        link = _ref_url_for_markdown(url, output_path)
        lines.append(f'- [{title}]({link})')
    lines.append('')
    return '\n'.join(lines)


def format_overview_section(
    overview: dict,
    *,
    include_background: bool = True,
    include_goal: bool = True,
    goal_heading: str = "目的",
    include_related_docs: bool = True,
    output_path: Optional[Path] = None,
) -> str:
    """
    overview 辞書から「背景」「目的/ゴール」「関連ドキュメント」の Markdown を生成する。
    各 create_human_document.py で共通利用。
    output_path を渡すと、関連ドキュメントのファイルパスを出力ファイルからの相対パスに変換する。
    """
    if not overview:
        return ''
    lines = []
    if include_background and overview.get('background'):
        lines.append('## 背景')
        lines.append('')
        lines.append(overview['background'])
        lines.append('')
    if include_goal and overview.get('goal'):
        lines.append(f'## {goal_heading}')
        lines.append('')
        lines.append(overview['goal'])
        lines.append('')
    if include_related_docs and overview.get('related_docs'):
        lines.append('### 関連ドキュメント')
        lines.append('')
        for doc in overview['related_docs']:
            if isinstance(doc, dict):
                title, url = doc.get('title', '-'), doc.get('url', '')
                link = _ref_url_for_markdown(url, output_path) if url else url
                lines.append(f'- [{title}]({link})' if link else f'- {title}')
            else:
                lines.append(f'- {doc}')
        lines.append('')
    if not lines:
        return ''
    return '\n'.join(lines).rstrip() + '\n'


def generate_open_items_markdown(data: dict, output_path: Optional[Path] = None) -> str:
    """
    open_items YAML から検討事項・不明点の Markdown を生成する。
    全カテゴリの open_items/tool/create_human_document.py で共通利用。
    """
    lines = []
    meta = data.get('meta', {})

    lines.append(f"# {meta.get('title', '検討事項・不明点')}")
    lines.append("")
    lines.append(f"**タイプ:** 📋 検討事項・不明点 | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    lines.append("")

    if meta.get('category') == 'overview':
        lines.append("**この doc_type の役割:** プロジェクト全体の検討事項・不明点の**目次**として使う。各カテゴリの未決事項は以下に分散している。ここでは「全体で何が未決か」を一覧し、必要に応じて各カテゴリの open_items へリンクする。")
        lines.append("")
        lines.append("- [設計の検討事項・不明点](../../../design/open_items/human/document.md)")
        lines.append("- [開発の検討事項・不明点](../../../development/open_items/human/document.md)")
        lines.append("- [調査の検討事項・不明点](../../../investigation/open_items/human/document.md)")
        lines.append("- [検証の検討事項・不明点](../../../verification/open_items/human/document.md)")
        lines.append("")

    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")

    open_decisions = data.get('open_decisions', [])
    if open_decisions:
        lines.append("## 検討事項")
        lines.append("")
        lines.append("決まらないと先に進めないこと。")
        lines.append("")
        lines.append("| ID | 決めること | 詳細 | ブロックするタスク | 状態 | 担当 | 期限 |")
        lines.append("|----|------------|------|-------------------|------|------|------|")
        for d in open_decisions:
            blocks = ", ".join(d.get('blocks_tasks') or []) or "-"
            status = (d.get('status') or 'open').lower()
            status_display = "✅ 解消" if status == 'resolved' else "⬜ 未解消"
            detail_s = (d.get('detail') or '-')
            detail_short = detail_s[:30] + ('...' if len(detail_s) > 30 else '')
            lines.append(f"| {d.get('id', '-')} | {d.get('decision_needed', '-')} | {detail_short} | {blocks} | {status_display} | {d.get('owner') or '-'} | {d.get('due') or '-'} |")
        lines.append("")
        for d in open_decisions:
            if d.get('detail'):
                lines.append(f"### {d.get('id', '-')}: {d.get('decision_needed', '')}")
                lines.append("")
                lines.append(d['detail'])
                lines.append("")
    else:
        lines.append("## 検討事項")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    unclear_points = data.get('unclear_points', [])
    if unclear_points:
        lines.append("## 不明点")
        lines.append("")
        lines.append("仕様・前提が不明な点。")
        lines.append("")
        lines.append("| ID | 不明点 | 詳細 | 状態 |")
        lines.append("|----|--------|------|------|")
        for u in unclear_points:
            status = (u.get('status') or 'open').lower()
            status_display = "✅ 解消" if status == 'resolved' else "⬜ 未解消"
            detail_s = (u.get('detail') or '-')
            detail_short = detail_s[:40] + ('...' if len(detail_s) > 40 else '')
            lines.append(f"| {u.get('id', '-')} | {u.get('point', '-')} | {detail_short} | {status_display} |")
        lines.append("")
        for u in unclear_points:
            if u.get('detail'):
                lines.append(f"### {u.get('id', '-')}: {u.get('point', '')}")
                lines.append("")
                lines.append(u['detail'])
                if u.get('related_docs'):
                    lines.append("")
                    lines.append("**関連資料:**")
                    for rd in u['related_docs']:
                        lines.append(f"- [{rd.get('title', '-')}]({rd.get('url', '')})")
                lines.append("")
    else:
        lines.append("## 不明点")
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    return '\n'.join(lines)


def run_create_human_document(generate_markdown_fn: Callable[[dict], str]) -> None:
    """
    create_human_document の共通エントリポイント。
    argparse で input / -o を取得し、YAML 読み込み → generate_markdown_fn → 出力を行う。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    data = load_yaml(args.input)
    output_path = Path(args.output).resolve() if args.output else None
    md = generate_markdown_fn(data, output_path=output_path)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding='utf-8')
        print(f"✅ {args.output}")
    else:
        print(md)
