# セキュリティ設計・脅威モデル

**タイプ:** 🔒 セキュリティ設計 | **ステータス:** 🔄 WIP | **バージョン:** 1.0.0
**作成者:** 山田太郎
**この doc_type の役割:** 脅威と対策を明文化し、セキュリティリスクを低減する。

## 背景

認証・認可・機密データ（パスワード・トークン）を扱うため、
脅威と対策を明示し、architecture とは別にセキュリティ観点を記述する。


## 目的

脅威と対策を明文化し、セキュリティリスクを低減する。


### 関連ドキュメント

- [要件整理](../../requirements/human/document.md)
- [アーキテクチャ](../../architecture/human/document.md)

## 脅威と対策一覧

| ID | 脅威 | 影響度 | 対策状況 |
|----|------|--------|----------|
| TH-001 | リフレッシュトークンの漏洩・横流し | 🔴 high | ✅ 対策済 |
| TH-002 | パスワードの推測・ブルートフォース | 🔴 high | ✅ 対策済 |
| TH-003 | アクセストークンの盗聴・中間者攻撃 | 🔴 high | ✅ 対策済 |
| TH-004 | 管理画面の権限昇格・横流し | 🟡 medium | ⬜ 未対応 |

### TH-001: リフレッシュトークンの漏洩・横流し

**影響度:** high

**対策:** ローテーション方式の採用。使用済みトークンは即無効化。有効期限を設定し、異常な使用頻度は検知・無効化する。

**対策状況:** ✅ 対策済

**関連資料:**
- [決定ログ ADR-002](categories/overview/decisions/ai/document.yaml)

### TH-002: パスワードの推測・ブルートフォース

**影響度:** high

**対策:** REQ-002 のパスワード強度、REQ-003 のロックアウト。レート制限とログ監視。

**対策状況:** ✅ 対策済

**関連資料:**
- [要件整理](categories/design/requirements/ai/document.yaml)

### TH-003: アクセストークンの盗聴・中間者攻撃

**影響度:** high

**対策:** HTTPS 必須。トークンは short-lived。Bearer のみで Cookie には載せない方針。

**対策状況:** ✅ 対策済

### TH-004: 管理画面の権限昇格・横流し

**影響度:** medium

**対策:** ロール（admin/operator/user）に応じた認可。操作単位の権限は U-002 で確定後、実装で反映。

**対策状況:** ⬜ 未対応

**関連資料:**
- [検討事項・不明点 U-002](categories/overview/open_items/ai/document.yaml)

## 関連資料（エビデンス）

- [要件整理](../../requirements/human/document.md)
- [アーキテクチャ](../../architecture/human/document.md)
- [リスク登録簿](../../../overview/risk_register/human/document.md)

---

[プロジェクト概要に戻る](../../../overview/project_summary/human/document.md)