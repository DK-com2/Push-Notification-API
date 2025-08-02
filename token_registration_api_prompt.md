# Claude Code用 トークン登録API開発プロンプト

## プロジェクト概要

FCMプッシュ通知を使った位置情報取得システムのバックエンドAPI開発プロジェクトです。
今回は**トークン登録API**のみを実装します。

## 技術スタック

- **言語**: Python
- **フレームワーク**: Flask
- **データベース**: PostgreSQL
- **外部サービス**: Firebase Cloud Messaging (FCM)

## 既存環境情報

### PostgreSQL環境
- **データベース名**: `location_tracker`
- **ユーザー**: `dkcom` (Superuser権限)
- **サーバー**: Ubuntu上で稼働中

### 作成済みテーブル構造

```sql
CREATE TABLE device_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    device_token TEXT NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('android', 'ios')),
    device_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_user_platform UNIQUE (user_id, platform)
);
```

### テーブル詳細説明

| カラム名 | データ型 | 制約 | 説明 |
|---------|---------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 主キー（自動採番） |
| user_id | VARCHAR(100) | NOT NULL | ユーザー識別子 |
| device_token | TEXT | NOT NULL | FCMプッシュ通知トークン |
| platform | VARCHAR(20) | NOT NULL, CHECK | デバイスOS（android/ios） |
| device_info | JSONB | - | デバイス詳細情報 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW | 更新日時 |

**重要な制約**: `CONSTRAINT uk_user_platform UNIQUE (user_id, platform)` により、同一ユーザーが同一プラットフォームで重複登録できません。

## 実装要件

### API仕様

- **エンドポイント**: `POST /api/register-token`
- **機能**: スマホアプリから送信されたFCMトークンをPostgreSQLに登録・更新

### リクエスト形式

```json
{
  "user_id": "user123",
  "device_token": "fGQ2bPbqR6K8mNvP5tLw3XyZ1AbCdEf_example_token",
  "platform": "android",
  "device_info": {
    "model": "Pixel 7",
    "os_version": "14.0",
    "app_version": "1.0.0"
  }
}
```

### レスポンス形式

**成功時**:
```json
{
  "status": "success",
  "message": "トークンが登録されました"
}
```

**エラー時**:
```json
{
  "status": "error",
  "message": "エラーの詳細メッセージ",
  "error_code": "VALIDATION_ERROR"
}
```

## 実装してほしい機能

### 1. プロジェクト基本構造

```
location_tracker/
├── app.py              # メインアプリケーション
├── config.py           # 設定管理
├── database.py         # PostgreSQL接続設定
├── models/
│   └── device_token.py # DeviceTokenモデル
├── routes/
│   └── token_routes.py # トークン関連API
├── utils/
│   └── validators.py   # バリデーション関数
├── requirements.txt    # 依存パッケージ
├── .env.example       # 環境変数テンプレート
└── README.md          # 使用方法
```

### 2. 入力データバリデーション

- **user_id**: 
  - 必須
  - 英数字とアンダースコア、ハイフンのみ許可
  - 1-100文字
- **device_token**: 
  - 必須
  - 空文字NG
  - FCMトークン形式
- **platform**: 
  - 必須
  - "android" または "ios" のみ
- **device_info**: 
  - オプション
  - JSON形式であること

### 3. UPSERT機能

- 既存レコード（同一user_id + platform）がある場合: **更新**
- 新規の場合: **新規作成**
- PostgreSQLの `ON CONFLICT` 句を使用

### 4. エラーハンドリング

- **400 Bad Request**: バリデーションエラー
- **500 Internal Server Error**: データベースエラー
- **適切なエラーメッセージ**: 何が間違っているかを明確に

### 5. ログ出力

- リクエスト受信ログ
- バリデーションエラーログ
- データベース操作ログ
- 成功/失敗ログ

### 6. 設定管理

環境変数で以下を管理:
```
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=location_tracker
DATABASE_USER=dkcom
DATABASE_PASSWORD=your_password
FLASK_ENV=development
FLASK_DEBUG=True
```

## 期待する成果物

1. **動作するFlaskアプリケーション**
2. **PostgreSQL接続とCRUD操作**
3. **完全なバリデーション機能**
4. **エラーハンドリング**
5. **テスト用のcurlコマンド例**
6. **起動・テスト手順のドキュメント**

## テスト例

成功ケース:
```bash
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "device_token": "fGQ2bPbqR6K8mNvP5tLw3XyZ1AbCdEf_test_token",
    "platform": "android",
    "device_info": {"model": "Pixel 7", "os_version": "14.0"}
  }'
```

エラーケース:
```bash
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "",
    "device_token": "test_token",
    "platform": "windows"
  }'
```

## 実装お願い

上記の要件に基づいて、完全に動作するトークン登録APIを実装してください。
特に、UPSERT機能とバリデーションは重要な機能です。

コードの品質、エラーハンドリング、ログ出力を重視してください。