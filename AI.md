# AI 向けプロンプト：このプロジェクトの使い方とルール

このドキュメントは、生成AIが本プロジェクト（yaml-bridge）を使って開発・ドキュメント作業を行う際に従うべき**使い方**と**ルール**をまとめたものです。AIはこの内容をプロンプトとして受け取り、ルール通りに動作してください。

---

## 1. このプロジェクトの目的と思想

- **共通言語は YAML**  
  生成AIと人間の共通言語として YAML を使い、開発案件のドキュメントを管理するツールです。
- **役割分担**
  - **AI**: YAML を**読み**、YAML を**書く**。編集するのは `categories/{category}/{doc_type}/ai/document.yaml` のみ。
  - **人間**: ツールが YAML から生成した Markdown / Mermaid 図（`human/document.md`）を閲覧する。
  - **検証**: AI が書いた YAML は `make validate` / `common/tools/validate.py` でスキーマ検証・リンクチェックされる。

**AI が守るべき原則**

1. **書く場所は YAML のみ**  
   `ai/document.yaml` 以外（human/document.md やソースコードの無関係な部分）にドキュメント内容を直接書かない。
2. **スキーマに従う**  
   各 doc_type の `ai/scheme.json` および `common/scheme.json` の定義に厳密に従う。形式違反は `make validate` で失敗する。
3. **人間にわかりやすくする**  
   考えていること・次のアクションは YAML の `ai_context` や適切なセクションに書き、ツールが Markdown/図に変換して人間が確認できるようにする。
4. **エビデンスを残す**  
   各ドキュメントで `references`（関連資料の title + url）を必ず付ける。根拠・参照元をリンクで明示する。
5. **編集後は必ずビルドする**  
   `ai/document.yaml` を修正した後は、**必ず `make build` を実行する**。人間向けの `human/document.md` を最新にし、ビルド時の検証（スキーマ・リンク・MD 内相対リンク）で不備を検出するため。

---

## 2. ディレクトリ構成と「どこに何を書くか」

- 1 つの **doc_type** = `ai/`（YAML + スキーマ）+ `human/`（生成 MD）+ `tool/`（変換スクリプト）の 3 点セット。
- **AI が編集するファイルは次の 1 種類だけ**:
  - `categories/{category}/{doc_type}/ai/document.yaml`

例: WBS を編集する場合  
→ `categories/overview/wbs/ai/document.yaml`

- **編集しないもの**
  - `human/document.md` … ツールが生成するため手で編集しない。
  - `ai/scheme.json` … スキーマ定義。通常は変更しない（プロジェクト側で定義済み）。
  - `tool/create_human_document.py` … 変換ロジック。必要に応じてプロジェクト管理者が変更。

---

## 3. カテゴリと doc_type

フェーズの流れ: **overview → investigation → design → development → verification**

| カテゴリ       | 主な doc_type 例 |
|----------------|------------------|
| overview       | project_summary, wbs, open_items, decisions, risk_register, change_log, ... |
| investigation  | code_understanding, domain_knowledge, related_code_research, investigation_summary, open_items, tasks |
| design         | requirements, architecture, open_items, tasks, api_spec, data_model, security_design, ... |
| development    | implementation_plan, implementation_detail, implementation_result, pull_request, technical_debt, open_items, tasks, ... |
| verification   | verification_plan, verification_procedure, verification_result, open_items, tasks |

- どの doc_type に何を書くかは、`categories/{category}/{doc_type}/ai/scheme.json` の **`x-ai-guid`** に記載されている。
- 一覧は `make list` で確認できる。

---

## 4. YAML 記述ルール（共通）

### 4.1 meta（必須）

全 doc_type で必ず含める。

- **必須**: `title`, `category`, `doc_type`, `status`, `version`
- **任意**: `author`, `created_at`, `updated_at`
- `category` / `doc_type` は、その doc_type のスキーマで決まった値（const）と一致させる。
- `status`: `todo` | `wip` | `done`
- `version`: Semver（例: `1.0.0`）

### 4.2 references（関連資料）

- 多くの doc_type で **references** が必須または推奨。
- 形式: `{ title, url }` の配列。url は相対パス（例: `categories/design/requirements/ai/document.yaml`）または絶対 URL。
- リンク切れは `make validate`（オプションでリンクチェック）や `make build` で検出される。**必ず有効なパス/URL を書く。**

### 4.3 overview / background・goal・related_docs

- overview 系の doc_type では、`overview_background_goal` に従い **background**, **goal**, **related_docs**（1 件以上の `{ title, url }`）を書く。

### 4.4 ai_context（任意だが推奨）

- AI の「現在の考え」「次のアクション」を人間用 MD で図示するために使う。
- `current_thinking`（文字列または文字列配列）、`next_actions`（id, label, detail）、`decision_flow` などを記述すると、ツールが Markdown/図に反映する。

---

## 5. 作業フロー（AI が従う手順）

1. **編集**  
   対象の `categories/{category}/{doc_type}/ai/document.yaml` のみを編集する。
2. **編集後は必ず `make build` を実行する**  
   `ai/document.yaml` を修正したら、**必ず** 次を実行する:
   ```bash
   make build
   ```
   - `make build` は内部でバリデーション（スキーマ・リンクチェック）を行ってから Markdown を生成する。そのため、`make validate` を単独で実行する必要はない（編集後の確認は `make build` で十分）。
   - ビルドが失敗したら、エラーに従って YAML またはリンクを修正し、再度 `make build` を実行する。
   - 対象カテゴリだけビルドする場合:
   ```bash
   make overview
   make investigation
   make design
   make development
   make verification
   ```
3. **Done にする前に**  
   `meta.status` を `done` にする前に、`make build` が成功していること。`make build` では YAML のスキーマ検証・リンクチェックに加え、生成済み `human/document.md` 内の相対リンクのファイル存在チェックも行われる。

---

## 6. スキーマと x-ai-guid の参照

- 各 doc_type の **何を・どの形式で書くか** は、`categories/{category}/{doc_type}/ai/scheme.json` で定義されている。
- スキーマ内の **`x-ai-guid`** に、AI 向けの説明（intro、required_sections、各プロパティの意味）が書かれている。
- **新しい doc_type を編集するときは、必ずその doc_type の `ai/scheme.json` を開き、`x-ai-guid` を確認してから document.yaml を書く。**
- 共通定義（meta_base, overview_background_goal, references, ai_context）は `common/scheme.json` の `definitions` を参照する。

---

## 7. タスク・検討事項の扱い

- **WBS（overview/wbs）**: サマリ・マイルストーン・階層（wbs_code）を管理。細かいタスクは各カテゴリの **tasks** に記述し、WBS のビルド時に集約表示される。
- **詳細タスク**: 各カテゴリの `tasks/ai/document.yaml` に、id, title, status, wbs_code 等を書く。
- **検討事項・不明点**: 各カテゴリの **open_items** の `open_decisions` / `unclear_points` に書く。ブロッカーは project_summary または WBS の blockers で紐付ける。
- **決定したこと**: overview/decisions に結論を追記する。

---

## 8. 禁止事項・注意事項

- **human/document.md を手で編集しない**（上書きされるため）。
- **スキーマにないキーを追加しない**。未定義のキーはバリデーションで弾かれる場合がある。
- **references / related_docs の url を空やダミーにしない**。リンクチェックで失敗する。
- **meta.category / meta.doc_type をスキーマと違う値にしない**（該当 doc_type の scheme.json の const に合わせる）。
- **長文を 1 キーに詰め込まない**。スキーマで許されている構造（配列・ネスト）を使って、人間が読みやすい YAML を書く。

---

## 9. コマンド早見表

| 目的               | コマンド |
|--------------------|----------|
| 利用可能な doc_type 一覧 | `make list` |
| 全 YAML のバリデーションのみ | `make validate` |
| 全 doc_type のビルド     | `make build` |
| カテゴリ別ビルド         | `make overview` / `make investigation` / `make design` / `make development` / `make verification` |
| 単一 YAML のビルド例     | `python3 common/tools/build.py categories/overview/wbs/ai/document.yaml` |
| 生成 MD の削除           | `make clean` |
| ヘルプ                 | `make help` |

---

## 10. 参照ドキュメント

- 思想・背景: [doc/思想.md](doc/思想.md)
- 構成・データフロー: [doc/ABOUT.md](doc/ABOUT.md)
- 使い方・カテゴリ一覧・Done の基準: [README.md](README.md)

---

**要約**: AI は **ai/document.yaml だけを編集**し、**スキーマ（scheme.json の x-ai-guid 含む）に従い**、**編集後は必ず make build を実行する**。人間向けの説明とエビデンス（references）を欠かさず書く。
