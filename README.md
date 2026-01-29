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
make overview        # プロジェクト概要（design / development / investigation / verification のタスク状態を集約表示）
make investigation   # 調査
make design          # 設計
make development     # 開発
make verification    # 動作確認
```

### 単一YAMLの処理

```bash
python3 common/tools/build.py categories/design/task_breakdown/ai_handled.yaml
```

## ディレクトリ構成

```
categories/{category}/{doc_type}/
  schema.json     # JSON Schema（バリデーション用）
  to_md.py        # YAML → Markdown（Mermaid図はここで埋め込み）
  guide.yaml      # ガイド・テンプレート
  ai_handled.yaml # AIが扱うファイル（ビルド対象）
  human_readable.md # 生成されたMarkdown
```

## カテゴリと doc_type

| カテゴリ | doc_type |
|----------|----------|
| overview | project_summary（カテゴリ別タスク状態の集約表示あり） |
| investigation | code_understanding, domain_knowledge, related_code_research |
| design | requirements, task_breakdown |
| development | implementation_detail, implementation_plan, implementation_result, pull_request |
| verification | verification_plan, verification_procedure, verification_result |

各YAMLには `meta.category` と `meta.doc_type` を指定し、対応するスキーマで検証されます。

## 共通ツール

- **common/tools/build.py** … バリデーション → Markdown生成の一括実行
- **common/tools/validate.py** … 単体のYAMLをバリデート（`meta` からスキーマを自動検出）
- **common/md_base.py** … 各 to_md.py が利用するYAML読み込みヘルパー
