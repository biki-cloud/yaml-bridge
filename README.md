# YAML → Markdown / Mermaid ビルドツール

生成AIと人間の共通言語としてYAMLを使い、開発案件のドキュメントを管理するためのツールです。

- **生成AI** … YAMLを読み、YAMLを書く
- **人間** … ツールでYAMLからMarkdownやMermaid図を生成して閲覧する
- **検証** … 生成AIが書いたYAMLはスクリプトでバリデートする

詳細な考え方は [思想.md](思想.md) を参照してください。

## 必要環境

- Python 3
- 依存パッケージ: `pip install -r requirements.txt`
  - PyYAML, jsonschema

## 使い方

```bash
make help    # コマンド一覧
make list    # 利用可能なカテゴリ・doc_type一覧
make build   # 全YAMLをバリデートし、Markdownを生成
make validate # バリデーションのみ（MD生成なし）
make clean   # 生成したMDを削除
```

### カテゴリ別ビルド

```bash
make overview        # プロジェクト概要（WBS にカテゴリ別タスク状態を集約表示）
make investigation   # 調査
make design          # 設計
make development     # 開発
make verification    # 動作確認
```

### 単一YAMLの処理

```bash
python3 common/tools/build.py categories/overview/wbs/ai/document.yaml
```

## 誰が何を読むか

各カテゴリの `human/document.md` は、YAML からビルドされた人間向けドキュメントです。ロール別の推奨は以下のとおりです。

| ロール                 | 主に読む doc_type（human/document.md）                                                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| プロジェクト全体の把握 | overview / project_summary, overview / wbs, overview / decisions, overview / risk_register, overview / change_log                                                                 |
| 設計担当               | design / requirements, design / architecture                                                                                                                                        |
| 開発担当               | development / implementation_plan, implementation_detail, implementation_result, pull_request, development / technical_debt                                                                |
| 調査・検証担当         | investigation（code_understanding, domain_knowledge, related_code_research, investigation_summary）, verification（verification_plan, verification_procedure, verification_result） |

全体の流れは overview → investigation → design → development → verification の順で参照するとよいです。

## ディレクトリ構成

```
categories/{category}/{doc_type}/
  ai/
    document.yaml   # AIが扱うファイル（ビルド対象）
    scheme.json     # JSON Schema（バリデーション用）
  human/
    document.md     # 生成されたMarkdown
  tool/
    create_human_document.py  # YAML → Markdown（Mermaid図はここで埋め込み）
```

## カテゴリと doc_type

| カテゴリ      | doc_type                                                                                  |
| ------------- | ----------------------------------------------------------------------------------------- |
| overview      | project_summary, wbs, open_items（検討事項・不明点）, decisions（決定ログ）, risk_register（リスク登録簿）, change_log（変更履歴） |
| investigation | code_understanding, domain_knowledge, related_code_research, investigation_summary（調査サマリ）, open_items, tasks（詳細タスク） |
| design        | requirements, architecture（アーキテクチャ）, open_items, tasks                                                          |
| development   | implementation_detail, implementation_plan, implementation_result, pull_request, technical_debt（技術的負債）, open_items, tasks |
| verification  | verification_plan, verification_procedure, verification_result, open_items, tasks         |

- **open_items**: 各カテゴリの「検討事項」（決まらないと先に進めないこと）と「不明点」を 1 doc_type で管理。ブロッカー紐付けは project_summary / WBS で行う。
- **decisions**: プロジェクト横断の重要決定（決まったこと）の記録。open_items の検討事項が決まったら結論をここに追記する。
- **risk_register**: プロジェクト全体のリスクを一元的に管理（影響度・対策・オーナー・ステータス）。
- **change_log**: スコープ・スケジュール・要件などの変更履歴。
- **architecture**: システム・コンポーネント構成と境界。要件と実装計画の間の全体像を記述する。
- **technical_debt**: 技術的負債一覧。wbs_code / task_id でタスクと紐付け可能。
- **tasks**: design / development / investigation / verification の各カテゴリの**詳細タスク**。WBS の wbs_code で紐付け可能。WBS の human/document.md ビルド時にカテゴリ別詳細タスクを集約表示する。
- **investigation_summary**: 調査フェーズの結論・推奨・設計へのインプットを一箇所にまとめる。code_understanding / domain_knowledge / related_code_research を総括する。

**運用方針（全プロジェクト共通）:** 各 doc_type は全プロジェクトで枠を用意し、該当しない場合は空・N/A でよい。api_spec（API がない案件）, security_design, data_model（データを持たない案件）, runbook（本番運用しない案件）, incident_postmortem（障害記録）, stakeholder_raci, dependency_external などは、案件によっては使わない場合があるが、テンプレートとして枠を残し、該当しない場合は空でよい。

各YAMLには `meta.category` と `meta.doc_type` を指定し、対応するスキーマで検証されます。

## タスク管理方針

- **タスクの定義・一覧・進捗**: WBS（overview/wbs）がサマリ・マイルストーンを保持。**細かいタスク**は各カテゴリの **doc_type: tasks** で保持する。
- **カテゴリ別詳細タスク**: design / development / investigation / verification の各 `tasks/ai/document.yaml` に、そのカテゴリのタスク一覧（id, title, wbs_code, status, estimated_hours 等）を記述。WBS の create_human_document が各カテゴリの tasks を読み、「カテゴリ別詳細タスク」として WBS の Markdown に集約表示する。
- **検討事項・不明点**: 各カテゴリの **open_items** に open_decisions（検討事項）と unclear_points（不明点）を記述。ブロッカーは **project_summary** または **WBS** の blockers セクションで案件・WBS 要素に紐付ける。
- **階層**: WBS の wbs_elements は wbs_code（1, 1.1, 1.1.1）と type: summary / task / milestone で階層を表現。カテゴリ tasks の各タスクは wbs_code で WBS のまとまりに対応付ける。

## Done の基準

`meta.status` が `done` であるとは、その doc_type としての記載が一通り揃い、必要に応じてレビュー済みである状態を指します。Done とする前に、`make validate` によるリンクチェック（YAML 内のファイルパス・GitHub URL の 404 チェック）の通過を前提とします。`make build` 実行時には、全 human/document.md 生成後に MD 内の相対リンクのファイル存在チェックも行い、失敗時はビルドが失敗します。詳細は [思想.md](思想.md) や各 doc_type の scheme の `x-ai-guid` を参照してください。

## 共通ツール

- **common/tools/build.py** … バリデーション → Markdown生成の一括実行
- **common/tools/validate.py** … 単体のYAMLをバリデート（`meta` からスキーマを自動検出）。`--check-md-links --all` で生成済み human/document.md 内の相対リンクのファイル存在を検証可能。
- **common/md_base.py** … 各 create_human_document.py が利用するYAML読み込みヘルパー
