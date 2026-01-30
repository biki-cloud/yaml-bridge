# プロジェクト構造・考え方（図解）

このドキュメントでは、本プロジェクトの「思想」「ディレクトリ構造」「データフロー」「カテゴリ・doc_type の関係」「ツールの役割」を Mermaid 図で整理しています。詳細な文章説明は [思想.md](思想.md) と [README.md](README.md) を参照してください。

---

## 1. 思想・役割分担

**AI と人間の共通言語としての YAML**

- 生成 AI は YAML を読み・書く（共通言語として扱う）。
- 人はツールで生成した Markdown / Mermaid だけを閲覧する。
- 生成 AI が書いた YAML は検証スクリプトでバリデートする。

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

**`categories/{category}/{doc_type}/` と `common/` の関係**

- 各 doc_type は **ai/**（document.yaml + scheme.json）、**human/**（document.md・ビルド成果物）、**tool/**（create_human_document.py）の 3 点セット。
- common には config / paths / scheme の共通定義と、build / validate / build_open_items_aggregate を配置。

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

### 1 つの doc_type のディレクトリ例（release_log）

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

**YAML → バリデーション → Markdown 生成**

- validate.py: meta.category / meta.doc_type からスキーマを特定し、`ai/scheme.json` で JSON Schema 検証。オプションでリンクチェック（GitHub URL、生成済み MD 内の相対パス）。
- build.py: 全 YAML またはカテゴリ指定で、validate 実行後に各 doc_type の `tool/create_human_document.py` を呼び出し、`human/document.md` を生成。

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

**overview → investigation → design → development → verification**

ドキュメント参照の推奨順は、カテゴリの並びの通り。各カテゴリはフェーズに対応し、タスク・検討事項は各カテゴリの doc_type（tasks / open_items）で管理する。

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

**1 つの doc_type = ai（YAML + スキーマ）+ human（生成 MD）+ tool（変換スクリプト）**

- common/scheme.json の definitions（meta_base, overview_background_goal, ai_context 等）を各 doc_type の `ai/scheme.json` が `$ref` で参照。
- 変換は doc_type ごとの `create_human_document.py` が YAML を読み、Markdown と Mermaid を組み立てる。AI が書く場所は ai/document.yaml に一本化され、スキーマで形式が強制される。

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

**WBS とカテゴリ tasks / open_items の関係**

- **タスクの正**: overview/wbs がサマリ・マイルストーンを保持。細かいタスクは各カテゴリの doc_type: **tasks** に保持し、WBS のビルド時にカテゴリ別詳細タスクとして集約表示する。
- **検討事項・不明点**: 各カテゴリの **open_items** で管理。ブロッカーは project_summary または WBS の blockers で紐付ける。
- **build_open_items_aggregate.py**: 全カテゴリの open_items を 1 つの Markdown に集約し、PM が検討事項・不明点を一覧で確認できるようにする。

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

---

## 関連ドキュメント

- [思想.md](思想.md) … YAML を介した共通言語・改善できること
- [README.md](README.md) … 使い方・カテゴリと doc_type・タスク管理方針
- [doc_as_code.md](doc_as_code.md) … ドキュメントのコード化の対応関係
