# API仕様

**タイプ:** 🔌 API仕様 | **ステータス:** 🔄 WIP | **バージョン:** 1.0.0
**作成者:** 山田太郎
**この doc_type の役割:** API の仕様（エンドポイント・リクエスト/レスポンス）を定義する。

## 背景

認証・ユーザー管理のAPI契約をOAuth 2.0準拠で定義する。
実装・検証・クライアント連携の単一の参照元とする。


## 目的

エンドポイント・メソッド・入出力概要を明文化し、要件IDと紐付ける。


### 関連ドキュメント

- [要件整理](../../requirements/human/document.md)
- [アーキテクチャ](../../architecture/human/document.md)

**ベースURL:** /api/v1

## エンドポイント一覧

| メソッド | パス | 説明 | 要件参照 |
|---------|------|------|----------|
| POST | /auth/login | メール・パスワードでログインし、アクセストークン・リフレッシュトークンを取得する | REQ-001, REQ-003 |
| POST | /auth/refresh | リフレッシュトークンで新しいアクセストークンを取得する（ローテーション） | - |
| POST | /auth/logout | ログアウト。リフレッシュトークンの無効化を行う | - |
| GET | /users | ユーザー一覧を取得する（ページネーション・フィルタ対応） | - |
| GET | /users/{id} | ユーザー詳細を取得する | - |

### POST /auth/login

メール・パスワードでログインし、アクセストークン・リフレッシュトークンを取得する

**リクエスト:** email (string), password (string)。REQ-001 準拠。
**レスポンス:** 200: access_token, refresh_token, expires_in。401: 認証失敗。429: ロック中（REQ-003）。
**要件参照:** REQ-001, REQ-003

### POST /auth/refresh

リフレッシュトークンで新しいアクセストークンを取得する（ローテーション）

**リクエスト:** refresh_token (string)
**レスポンス:** 200: access_token, refresh_token（新）, expires_in。401: トークン無効・期限切れ。

### POST /auth/logout

ログアウト。リフレッシュトークンの無効化を行う

**リクエスト:** refresh_token (string) 任意。Bearer でアクセストークンも受け取り無効化可能。
**レスポンス:** 204: 成功。401: 未認証。

### GET /users

ユーザー一覧を取得する（ページネーション・フィルタ対応）

**リクエスト:** なし。Query: page, limit, role 等
**レスポンス:** 200: users[], total。401: 未認証。403: 権限不足。

### GET /users/{id}

ユーザー詳細を取得する

**リクエスト:** なし。Path: id (uuid)
**レスポンス:** 200: user オブジェクト。404: 未存在。401/403。

## 関連資料（エビデンス）

- [要件整理](../../requirements/human/document.md)
- [アーキテクチャ](../../architecture/human/document.md)
- [データモデル](../../data_model/human/document.md)

---

[プロジェクト概要に戻る](../../../overview/project_summary/human/document.md)