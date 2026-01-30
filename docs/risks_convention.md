# リスクの扱いに関するルール

## 正（Single Source of Truth）

- **プロジェクト全体のリスクの正は `overview/risk_register` とする。**
- リスクの登録・影響度・対策・オーナー・ステータスは `categories/overview/risk_register/ai/document.yaml` で一元的に管理する。

## 他 doc_type での risks の扱い

- **project_summary / wbs / implementation_plan / requirements など**に `risks` 配列がある場合:
  - **PM 視点:** 可能な限り `risk_register` のリスク id を参照する形にするか、その doc に紐づく「ローカルな要約」に限定すると重複が減る。
  - **エンジニア視点:** 実装計画・要件の「技術リスク」はその doc に書いておくと読みやすいため、**risk_register の id 参照 ＋ その doc 固有の要約**の併用を推奨する。

## 運用

- 新規リスクを識別したら、まず `risk_register` に登録し、id を発行する。
- 他 doc でそのリスクに言及するときは、`risk_register` の id を記載するか、短い要約のみ書く。
