# このプロジェクトについて

本プロジェクトは「Documentation as Code」の考え方に沿い、YAML を生成 AI と人間の共通言語として使い、開発案件のドキュメントを管理するツールです。詳細な思想は [思想.md](思想.md) を、使い方・カテゴリ一覧は [README.md](../README.md) を参照してください。

---

## Documentation as Code との対応

- **ソースがコード（YAML）**: 要件・設計・実装メモなどは `ai/document.yaml` に構造化して記述し、`ai/scheme.json` で形式を規定する。
- **ビルドで人間用ドキュメントを生成**: 各 doc_type の `tool/create_human_document.py` が YAML を読み、`human/document.md` や Mermaid 図を生成する。
- **検証**: `validate.py` で YAML をスキーマ検証し、リンクチェックも行う。
- **役割の分離**: AI は YAML の読み書き、人はツールが生成した Markdown/図の閲覧に専念する（[思想.md](思想.md) の通り）。

| 概念 | このプロジェクトでの対応 |
|------|---------------------------|
| ドキュメントをテキスト/構造で管理 | YAML ＋ スキーマで管理 |
| バージョン管理 | Git で管理可能 |
| 自動検証 | `validate.py` |
| ビルド/生成 | `build.py` → Markdown / Mermaid 生成 |

---

## 1. 思想・役割分担

生成 AI は YAML を読み・書く。人はツールで生成した Markdown / Mermaid だけを閲覧する。生成 AI が書いた YAML は検証スクリプトでバリデートする。

```mermaid
flowchart LR
  subgraph ai_role [AI の役割]
    AI[生成AI]
    ReadYAML[YAML を読む]
    WriteYAML[YAML を書く]
    AI --> ReadYAML
    AI --> WriteYAML
  end
  subgraph common [共通言語]
    YAML[(document.yaml)]
  end
  subgraph human_role [人の役割]
    Tool[create_human_document.py]
    MD[human/document.md]
    Tool --> MD
    Human[人が閲覧]
    MD --> Human
  end
  subgraph validation [検証]
    Validate[validate.py]
  end
  WriteYAML --> YAML
  YAML --> ReadYAML
  YAML --> Tool
  YAML --> Validate
```

---

## 2. ディレクトリ構造

各 doc_type は **ai/**（document.yaml + scheme.json）、**human/**（document.md・ビルド成果物）、**tool/**（create_human_document.py）の 3 点セット。common には config / paths / scheme の共通定義と、build / validate / build_open_items_aggregate を配置する。

```mermaid
flowchart TB
  subgraph root [プロジェクトルート]
    categories[categories/]
    common[common/]
  end
  subgraph cat_content [categories の中身]
    overview[overview]
    investigation[investigation]
    design[design]
    development[development]
    verification[verification]
  end
  subgraph doc_type_pattern [1 doc_type のパターン]
    ai[ai/document.yaml + scheme.json]
    human[human/document.md 生成物]
    tool[tool/create_human_document.py]
  end
  subgraph common_content [common の中身]
    config[config.py]
    paths[paths.py]
    scheme[common/scheme.json]
    tools[tools/build.py, validate.py, build_open_items_aggregate.py]
  end
  categories --> cat_content
  categories --> doc_type_pattern
  common --> common_content
```

### 1 つの doc_type の例（release_log）

```
categories/overview/release_log/
  ai/
    document.yaml    # AI が編集するソース
    scheme.json      # バリデーション用スキーマ
  human/
    document.md      # ビルドで生成される人間向け Markdown
  tool/
    create_human_document.py   # YAML → Markdown 変換スクリプト
```

---

## 3. ビルド・検証のデータフロー

validate.py が meta.category / meta.doc_type からスキーマを特定し `ai/scheme.json` で JSON Schema 検証（オプションでリンクチェック）。build.py が validate 実行後に各 doc_type の create_human_document.py を呼び出し、`human/document.md` を生成する。

```mermaid
sequenceDiagram
  participant User
  participant Build as build.py
  participant Validate as validate.py
  participant Schema as ai/scheme.json
  participant CreateMD as create_human_document.py
  participant YAML as ai/document.yaml
  participant MD as human/document.md

  User->>Build: make build / python build.py --all
  Build->>Validate: 各 YAML を検証
  Validate->>YAML: 読み込み
  Validate->>Schema: meta からスキーマ特定
  Schema-->>Validate: スキーマ
  Validate->>Validate: JSON Schema 検証・リンクチェック
  Validate-->>Build: OK/NG
  Build->>CreateMD: 各 doc_type のスクリプト実行
  CreateMD->>YAML: 読み込み
  CreateMD->>MD: Markdown/Mermaid 出力
```

---

## 4. カテゴリとフェーズの関係

overview → investigation → design → development → verification の順でフェーズが進む。タスク・検討事項は各カテゴリの doc_type（tasks / open_items）で管理する。

```mermaid
flowchart LR
  O[overview]
  I[investigation]
  D[design]
  Dev[development]
  V[verification]
  O --> I --> D --> Dev --> V
  O -.->|WBS がサマリ・マイルストーン| O
  O -.->|open_items ブロッカー紐付け| O
  I -.->|tasks 詳細| I
  D -.->|tasks 詳細| D
  Dev -.->|tasks 詳細| Dev
  V -.->|tasks 詳細| V
```

---

## 5. doc_type の「3 点セット」とスキーマ

1 つの doc_type = ai（YAML + スキーマ）+ human（生成 MD）+ tool（変換スクリプト）。common/scheme.json の definitions を各 doc_type の `ai/scheme.json` が `$ref` で参照する。AI が書く場所は ai/document.yaml に一本化され、スキーマで形式が強制される。

```mermaid
flowchart TB
  subgraph one_doc_type [1 つの doc_type 例: release_log]
    ay[ai/document.yaml]
    sc[ai/scheme.json]
    hd[human/document.md]
    cr[tool/create_human_document.py]
  end
  common_scheme[common/scheme.json definitions]
  sc -->|"$ref"| common_scheme
  ay -->|入力| cr
  sc -->|検証| validate_py[validate.py]
  ay -->|検証| validate_py
  cr -->|出力| hd
```

---

## 6. タスク・検討事項の集約関係

- **タスク**: overview/wbs がサマリ・マイルストーンを保持。細かいタスクは各カテゴリの **tasks** に保持し、WBS のビルド時にカテゴリ別詳細タスクとして集約表示する。
- **検討事項・不明点**: 各カテゴリの **open_items** で管理。ブロッカーは project_summary または WBS の blockers で紐付ける。
- **build_open_items_aggregate.py**: 全カテゴリの open_items を 1 つの Markdown に集約し、PM が一覧で確認できるようにする。

doc_type ごとの「ai/document.yaml → tool → human/document.md」の依存関係（WBS・project_summary が他 YAML を参照する部分を含む）は [依存関係図.md](依存関係図.md) を参照。

```mermaid
flowchart TB
  WBS[overview/wbs]
  T_overview[overview/tasks]
  T_design[design/tasks]
  T_dev[development/tasks]
  T_inv[investigation/tasks]
  T_ver[verification/tasks]
  O_all[open_items 各カテゴリ]
  Agg[build_open_items_aggregate.py]
  MD_agg[検討事項一覧 MD]

  T_overview --> WBS
  T_design --> WBS
  T_dev --> WBS
  T_inv --> WBS
  T_ver --> WBS
  WBS -->|ビルド時に集約| WBS
  O_all --> Agg
  Agg --> MD_agg
```

タスク管理の詳細は [README.md](../README.md) の「タスク管理方針」を参照してください。
