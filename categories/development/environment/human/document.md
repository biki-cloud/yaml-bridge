# 環境・インフラ

**タイプ:** 🖥 環境・インフラ | **ステータス:** 🔄 WIP | **バージョン:** 1.0.0
**作成者:** 山田太郎
**この doc_type の役割:** 環境・インフラの構成と手順を記述する。

## 環境一覧

| ID | 名前 | 種別 | URL | デプロイ先 |
|----|------|------|-----|------------|
| ENV-001 | ローカル開発 | ローカル | http://localhost:3000 | 開発者PC |
| ENV-002 | ステージング | ステージング | https://staging.user-mgmt.example.com | AWS ECS（Fargate）。ALB 経由。 |
| ENV-003 | 本番 | 本番 | https://api.user-mgmt.example.com | AWS ECS（Fargate）。マルチAZ。 |

### ENV-001: ローカル開発

**CI/CD:** なし。手動で npm run dev。

**シークレット方針:** .env で管理。.env は .gitignore。サンプルは .env.example を参照。

Docker Compose で DB・Redis を起動可能（docker-compose.dev.yml）

### ENV-002: ステージング

**CI/CD:** main へのマージで自動ビルド・デプロイ。GitHub Actions。

**シークレット方針:** AWS Secrets Manager で管理。CI からは OIDC で取得。

本番に近い構成。データはマスキング済みのコピーを週次で投入予定（U-003 で方針確定）

### ENV-003: 本番

**CI/CD:** リリースタグで手動トリガー。承認後にデプロイ。

**シークレット方針:** AWS Secrets Manager。ローテーションは 90 日。

段階的リリース（フィーチャーフラグ）を想定。ロールバック手順は runbook 参照。

## 関連資料（エビデンス）

- [プロジェクト概要](../../../overview/project_summary/human/document.md)
- [ランブック](../../runbook/human/document.md)
- [リリースログ](../../../overview/release_log/human/document.md)

---

[プロジェクト概要に戻る](../../../overview/project_summary/human/document.md)