# 依存一覧

**タイプ:** 📦 依存一覧 | **ステータス:** 🔄 WIP | **バージョン:** 1.0.0
**作成者:** 山田太郎
**この doc_type の役割:** ライブラリ・ツール等の依存関係を一覧にする。

## 依存一覧

| ID | 名前 | 種別 | バージョン | ライセンス | 利用目的 |
|----|------|------|------------|------------|----------|
| DEP-001 | express | ライブラリ | 4.18.x | MIT | API サーバー基盤。認証・ユーザーAPI のルーティング・... |
| DEP-002 | jsonwebtoken | ライブラリ | 9.0.x | MIT | JWT の生成・検証。アクセストークン・リフレッシュトークン... |
| DEP-003 | ioredis | ライブラリ | 5.3.x | MIT | Redis クライアント。トークンストア・セッションストア |
| DEP-004 | bcrypt | ライブラリ | 5.1.x | MIT | パスワードハッシュ（REQ-002 準拠） |
| DEP-005 | joi | ライブラリ | 17.11.x | BSD-3-Clause | リクエストバリデーション。ログイン・ユーザー登録の入力検証 |
| DEP-006 | jest | ツール | 29.7.x | MIT | 単体テスト・結合テスト |

### DEP-001: express

**参照:** https://www.npmjs.com/package/express

### DEP-002: jsonwebtoken

**参照:** https://www.npmjs.com/package/jsonwebtoken

### DEP-003: ioredis

**参照:** https://www.npmjs.com/package/ioredis

### DEP-004: bcrypt

**参照:** https://www.npmjs.com/package/bcrypt

### DEP-005: joi

**参照:** https://www.npmjs.com/package/joi

### DEP-006: jest

**参照:** https://jestjs.io/

## 関連資料（エビデンス）

- [プロジェクト概要](../../../overview/project_summary/human/document.md)
- [実装計画](../../implementation_plan/human/document.md)
- [環境・インフラ](../../environment/human/document.md)

---

[プロジェクト概要に戻る](../../../overview/project_summary/human/document.md)