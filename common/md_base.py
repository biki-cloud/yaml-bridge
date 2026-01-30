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

from config import HUMAN_DOCUMENT_MD
from paths import DOC_CATEGORIES, get_category_label

# (category, doc_type) → この doc_type の役割（1行説明）
DOC_TYPE_ROLE_DESCRIPTIONS: dict[tuple[str, str], str] = {
    ("overview", "acceptance_sign_off"): "受入条件のサインオフ結果を記録する。",
    ("overview", "change_log"): "スコープ・計画・体制の変更履歴を記録する。いつ・何を・なぜ変更したか、承認有無を残す。本番リリースの日時・バージョン・変更内容はリリースログを参照する。",
    ("overview", "decisions"): "プロジェクトで行った重要な決定と理由を記録する。",
    ("overview", "dependency_external"): "外部システム・サービス・組織への依存を一覧し、リスクを把握する。",
    ("overview", "document"): "そのカテゴリで他 doc_type に当てはまらない情報用の汎用ドキュメント。",
    ("overview", "glossary"): "プロジェクトで使う用語の定義を一覧にし、認識のズレを防ぐ。",
    ("overview", "lessons_learned"): "振り返りで得た教訓を記録し、次に活かす。",
    ("overview", "open_items"): "プロジェクト全体の検討事項・不明点の目次として使う。各カテゴリの未決事項へリンクする。",
    ("overview", "project_summary"): "プロジェクトの概要・ゴール・スコープ・ステークホルダー・タイムライン・リスクを一覧にする。",
    ("overview", "quality_criteria"): "品質・受入基準を明文化する。",
    ("overview", "release_log"): "本番リリースの日時・バージョン・変更内容を記録する。",
    ("overview", "risk_register"): "プロジェクトリスクを登録し、影響度と対策を管理する。",
    ("overview", "stakeholder_raci"): "ステークホルダーと RACI を明示する。",
    ("overview", "wbs"): "作業分解構成とタスク・マイルストーンを管理する。",
    ("design", "api_spec"): "API の仕様（エンドポイント・リクエスト/レスポンス）を定義する。",
    ("design", "architecture"): "システム全体像・コンポーネント境界を明文化する。",
    ("design", "data_model"): "エンティティとその関係を定義し、要件・アーキテクチャと整合させる。",
    ("design", "document"): "設計カテゴリで他 doc_type に当てはまらない情報用の汎用ドキュメント。",
    ("design", "open_items"): "設計フェーズの検討事項・不明点を記録する。",
    ("design", "requirements"): "要件を整理し、優先度・受け入れ条件を明示する。",
    ("design", "security_design"): "脅威と対策を明文化し、セキュリティリスクを低減する。",
    ("design", "tasks"): "設計フェーズの詳細タスクを一覧にする。",
    ("development", "dependencies"): "ライブラリ・ツール等の依存関係を一覧にする。",
    ("development", "document"): "開発カテゴリで他 doc_type に当てはまらない情報用の汎用ドキュメント。",
    ("development", "environment"): "環境・インフラの構成と手順を記述する。",
    ("development", "implementation_detail"): "実装の詳細（アルゴリズム・処理フロー等）を記述する。",
    ("development", "implementation_plan"): "実装の計画・手順を記述する。",
    ("development", "implementation_result"): "実装の結果・変更内容を記録する。",
    ("development", "incident_postmortem"): "障害の振り返りと再発防止策を記録する。",
    ("development", "open_items"): "開発フェーズの検討事項・不明点を記録する。",
    ("development", "pull_request"): "PR の概要・変更内容・レビュー観点を記録する。",
    ("development", "runbook"): "運用時の手順・トラブルシュートを記述する。",
    ("development", "tasks"): "開発フェーズの詳細タスクを一覧にする。",
    ("development", "technical_debt"): "技術的負債を一覧にし、対応方針を管理する。",
    ("investigation", "code_understanding"): "コードの理解・解析結果を記録する。",
    ("investigation", "document"): "調査カテゴリで他 doc_type に当てはまらない情報用の汎用ドキュメント。",
    ("investigation", "domain_knowledge"): "ドメイン知識・業務理解の調査結果を記録する。",
    ("investigation", "investigation_summary"): "調査のサマリと結論を記録する。",
    ("investigation", "open_items"): "調査フェーズの検討事項・不明点を記録する。",
    ("investigation", "related_code_research"): "関連コードの調査結果を記録する。",
    ("investigation", "tasks"): "調査フェーズの詳細タスクを一覧にする。",
    ("verification", "document"): "検証カテゴリで他 doc_type に当てはまらない情報用の汎用ドキュメント。",
    ("verification", "open_items"): "検証フェーズの検討事項・不明点を記録する。",
    ("verification", "tasks"): "検証フェーズの詳細タスクを一覧にする。",
    ("verification", "verification_plan"): "動作確認・検証の計画を記述する。",
    ("verification", "verification_procedure"): "動作確認・検証の手順を記述する。",
    ("verification", "verification_result"): "動作確認・検証の結果を記録する。",
}


def get_doc_type_role_description(category: str, doc_type: str) -> str:
    """(category, doc_type) に対応する「この doc_type の役割」の 1 行を返す。"""
    return DOC_TYPE_ROLE_DESCRIPTIONS.get((category, doc_type), "")


def format_empty_section_hint(yaml_key: str = "") -> str:
    """一覧が空のとき「（なし）」の前に出す案内文。"""
    if yaml_key:
        return f"*該当する項目を ai/document.yaml の `{yaml_key}` に追加するとここに表示されます。*"
    return "*該当する項目を ai/document.yaml に追加するとここに表示されます。*"


def compute_task_hours(tasks: list) -> tuple[float, float, float]:
    """
    タスクリストから工数を計算する。
    tasks は estimated_hours（number）と status を持つ dict のリスト。
    返却: (total_hours, done_hours, remaining_hours)。
    欠損・非数は 0 扱い。
    """
    total_hours = 0.0
    done_hours = 0.0
    for t in tasks:
        try:
            h = float(t.get("estimated_hours") or 0)
        except (TypeError, ValueError):
            h = 0.0
        total_hours += h
        if t.get("status") == "done":
            done_hours += h
    remaining_hours = total_hours - done_hours
    return total_hours, done_hours, remaining_hours


def format_navigation_footer(
    output_path: Optional[Path] = None,
    *,
    skip_for_project_summary: bool = False,
) -> str:
    """「プロジェクト概要に戻る」リンクを返す。project_summary のときは空または省略可。"""
    if skip_for_project_summary:
        return ""
    href = rel_path_to_human_doc(output_path, "overview", "project_summary")
    return "\n---\n\n[プロジェクト概要に戻る]({})\n".format(href)


def format_meta_dates(meta: dict) -> str:
    """meta から created_at / updated_at があれば「**作成日:**」「**更新日:**」の行を返す。"""
    lines = []
    if meta.get("created_at"):
        lines.append(f"**作成日:** {meta['created_at']}")
    if meta.get("updated_at"):
        lines.append(f"**更新日:** {meta['updated_at']}")
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


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


def rel_path_to_human_doc(
    from_output_path: Optional[Path],
    to_category: str,
    to_doc_type: str,
) -> str:
    """
    現在の human/document.md の出力パスから、指定した (category, doc_type) の
    human/document.md への相対パスを返す。human ディレクトリ基準でクリックで飛べるようにする。
    from_output_path が None のときは、同 category 内を仮定したフォールバック文字列を返す。
    """
    if from_output_path is None:
        return f"../../{to_doc_type}/{HUMAN_DOCUMENT_MD}"
    from_dir = from_output_path.resolve().parent
    categories_dir = from_dir.parent.parent.parent
    target = categories_dir / to_category / to_doc_type / HUMAN_DOCUMENT_MD
    rel = os.path.relpath(target, from_dir)
    return rel.replace('\\', '/')


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
        role = get_doc_type_role_description(meta.get('category', ''), meta.get('doc_type', ''))
        if role:
            lines.append(f"**この doc_type の役割:** {role}")
        lines.append("")
        for cat in DOC_CATEGORIES:
            if cat == 'overview':
                continue
            label = f"{get_category_label(cat)}の検討事項・不明点"
            href = rel_path_to_human_doc(output_path, cat, 'open_items')
            lines.append(f"- [{label}]({href})")
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
        lines.append(format_empty_section_hint("open_decisions"))
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
        lines.append(format_empty_section_hint("unclear_points"))
        lines.append("")
        lines.append("（なし）")
        lines.append("")

    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    nav = format_navigation_footer(output_path)
    if nav:
        lines.append(nav.rstrip())
    return '\n'.join(lines)


def generate_document_markdown(data: dict, output_path: Optional[Path] = None) -> str:
    """
    汎用 document YAML（meta, summary, references, ai_context）から Markdown を生成する。
    各カテゴリの document/tool/create_human_document.py で利用。
    """
    lines = []
    meta = data.get('meta', {})
    title = meta.get('title', '汎用ドキュメント')
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**タイプ:** 📄 汎用ドキュメント | **ステータス:** {format_status(meta.get('status', 'todo'))} | **バージョン:** {meta.get('version', '-')}")
    if meta.get('author'):
        lines.append(f"**作成者:** {meta['author']}")
    dates = format_meta_dates(meta)
    if dates:
        lines.append(dates.rstrip())
    role = get_doc_type_role_description(meta.get('category', ''), meta.get('doc_type', ''))
    if role:
        lines.append(f"**この doc_type の役割:** {role}")
    lines.append("")
    ai_section = format_ai_context_section(data)
    if ai_section:
        lines.append(ai_section)
        lines.append("")
    summary = data.get('summary', '')
    lines.append("## 概要・まとめ")
    lines.append("")
    lines.append(summary if summary else "（内容を追記してください）")
    lines.append("")
    ref_section = format_references_section(data, output_path=output_path)
    if ref_section:
        lines.append(ref_section.rstrip())
    nav = format_navigation_footer(output_path)
    if nav:
        lines.append(nav.rstrip())
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
