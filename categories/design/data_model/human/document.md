# データモデル

**タイプ:** 📊 データモデル | **ステータス:** 🔄 WIP | **バージョン:** 1.0.0
**作成者:** 山田太郎
**この doc_type の役割:** エンティティとその関係を定義し、要件・アーキテクチャと整合させる。

## 背景

認証・ユーザー管理に必要なエンティティを定義し、
要件・アーキテクチャと整合させる。DB変更のトレースに利用する。


## 目的

エンティティ・属性・リレーションを明文化し、実装・マイグレーションの根拠とする。


### 関連ドキュメント

- [要件整理](../../requirements/human/document.md)
- [アーキテクチャ](../../architecture/human/document.md)

## エンティティ一覧

| ID | 名前 | 説明 |
|----|------|------|
| E-001 | users | ユーザー master。認証情報・プロファイルの親 |
| E-002 | refresh_tokens | リフレッシュトークン（ローテーション用）。使用済みは無効フラグ |
| E-003 | user_profiles | ユーザーの表示用プロファイル（名前・表示設定等） |

### E-001: users

ユーザー master。認証情報・プロファイルの親

| 属性 | 型 | PK | NULL |
|------|-----|----|------|
| id | uuid | ✓ | - |
| email | string | - | - |
| password_hash | string | - | - |
| role | string | - | - |
| created_at | timestamp | - | - |
| updated_at | timestamp | - | - |

**関連:**
- one_to_many → E-002 1ユーザーに対し複数リフレッシュトークン（有効分）
- one_to_one → E-003 ユーザーとプロファイルは1:1

### E-002: refresh_tokens

リフレッシュトークン（ローテーション用）。使用済みは無効フラグ

| 属性 | 型 | PK | NULL |
|------|-----|----|------|
| id | uuid | ✓ | - |
| user_id | uuid | - | - |
| token_hash | string | - | - |
| revoked | boolean | - | - |
| expires_at | timestamp | - | - |

**関連:**
- one_to_many → E-001 users への多対一

### E-003: user_profiles

ユーザーの表示用プロファイル（名前・表示設定等）

| 属性 | 型 | PK | NULL |
|------|-----|----|------|
| user_id | uuid | ✓ | - |
| display_name | string | - | ✓ |
| updated_at | timestamp | - | - |

**関連:**
- one_to_one → E-001 users と1:1

## 関連資料（エビデンス）

- [要件整理](../../requirements/human/document.md)
- [アーキテクチャ](../../architecture/human/document.md)

---

[プロジェクト概要に戻る](../../../overview/project_summary/human/document.md)