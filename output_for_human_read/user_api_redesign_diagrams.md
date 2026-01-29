# ユーザー情報取得API改修 - Mermaid図

## 変更サマリー

As-Is（現状）から To-Be（改修後）への変更の概要です。

```mermaid
flowchart LR
    subgraph AsIs["📦 現状 As-Is"]
        A1[既存の実装]
    end

    subgraph Changes["🔄 変更内容"]
        C0["➕ fields パラメータ"]
        C1["➕ page, per_page パラメータ"]
        C2["✏️ レスポンス構造 ⚠️"]
        C3["➕ _links フィールド"]
        C4["⚠️ include パラメータの旧形式"]
    end

    subgraph ToBe["🎯 改修後 To-Be"]
        B1[改修された実装]
    end

    AsIs --> Changes
    Changes --> ToBe

    style C2 fill:#ffcdd2,stroke:#c62828
    style AsIs fill:#fff3e0
    style ToBe fill:#e8f5e9
```

## 移行フロー

移行ステップとロールバック手順です。

```mermaid
flowchart TD
    Start([🚀 移行開始])
    Step1["1. v2エンドポイントを新規作成し、並行稼働開始"]
    Start --> Step1
    Rollback1[/"🔙 v2エンドポイントを削除"/]
    Step1 -.-> Rollback1
    Step2["2. クライアントを順次v2に移行（フィーチャーフラグ使用）"]
    Step1 --> Step2
    Rollback2[/"🔙 フィーチャーフラグをOFFにしてv1に戻す"/]
    Step2 -.-> Rollback2
    Step3["3. v1エンドポイントを非推奨化（Deprecation警..."]
    Step2 --> Step3
    Rollback3[/"🔙 警告ヘッダーを削除"/]
    Step3 -.-> Rollback3
    Step4["4. 移行完了後、v1エンドポイントを削除"]
    Step3 --> Step4
    Rollback4[/"🔙 v1エンドポイントを復活"/]
    Step4 -.-> Rollback4
    End([✅ 移行完了])
    Step4 --> End

    style Start fill:#e1f5fe
    style End fill:#c8e6c9
```

## 影響範囲

この改修が影響するシステムの範囲です。

```mermaid
flowchart TB
    API((ユーザー情報取得API))

    subgraph Clients["👥 クライアント"]
        CL0["Web フロントエンド（React）"]
        CL1["モバイルアプリ（iOS/Android）"]
        CL2["管理画面"]
    end
    Clients --> API

    subgraph DB["🗄️ データベース"]
        DB0[("users テーブル")]
        DB1[("posts テーブル")]
        DB2[("followers テーブル")]
    end
    API --> DB

    subgraph Deps["🔗 依存サービス"]
        DEP0[["認証サービス"]]
        DEP1[["キャッシュサービス（Redis）"]]
    end
    API <--> Deps

    style API fill:#bbdefb,stroke:#1976d2
    style Clients fill:#fff9c4
    style DB fill:#c8e6c9
    style Deps fill:#f3e5f5
```

## リスクマトリクス

深刻度と発生確率に基づくリスクの分布です。

```mermaid
quadrantChart
    title リスクマトリクス
    x-axis 発生確率 低 --> 高
    y-axis 深刻度 低 --> 高
    quadrant-1 要対策
    quadrant-2 監視
    quadrant-3 許容
    quadrant-4 注意
    "既存クライアントが破壊的...": [0.50, 0.62]
    "ページネーション導入によ...": [0.83, 0.38]
    "キャッシュ戦略の見直しが必要": [0.50, 0.38]
```

## APIフロー

APIリクエスト/レスポンスの流れです。

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API
    participant D as Database

    C->>+A: GET /api/v1/users/{user_id}
    A->>A: 認証・バリデーション
    A->>+D: データ取得
    D-->>-A: 結果
    A-->>-C: レスポンス

    alt エラー時
    A-->>C: エラーレスポンス
    end
```
