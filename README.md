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
| プロジェクト全体の把握 | overview / project_summary, overview / wbs                                                                                                                   |
| 設計担当               | design / requirements                                                                                                                                        |
| 開発担当               | development / implementation_plan, implementation_detail, implementation_result, pull_request                                                                |
| 調査・検証担当         | investigation（code_understanding, domain_knowledge, related_code_research）, verification（verification_plan, verification_procedure, verification_result） |

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
| overview      | project_summary, wbs（WBS・マイルストーン・進捗管理、カテゴリ別タスク状態の集約表示あり） |
| investigation | code_understanding, domain_knowledge, related_code_research                               |
| design        | requirements                                                                              |
| development   | implementation_detail, implementation_plan, implementation_result, pull_request           |
| verification  | verification_plan, verification_procedure, verification_result                            |

各YAMLには `meta.category` と `meta.doc_type` を指定し、対応するスキーマで検証されます。

## Done の基準

`meta.status` が `done` であるとは、その doc_type としての記載が一通り揃い、必要に応じてレビュー済みである状態を指します。Done とする前に、`make validate` によるリンクチェック（ファイルパス・GitHub URL の 404 チェック）の通過を前提とします。詳細は [思想.md](思想.md) や各 doc_type の scheme の `x-ai-guid` を参照してください。

## 共通ツール

- **common/tools/build.py** … バリデーション → Markdown生成の一括実行
- **common/tools/validate.py** … 単体のYAMLをバリデート（`meta` からスキーマを自動検出）
- **common/md_base.py** … 各 create_human_document.py が利用するYAML読み込みヘルパー
