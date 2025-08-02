# Push Notification Token Registration API

FCMプッシュ通知を使った位置情報取得システムのバックエンドAPI

## 機能

- FCMトークンの登録・更新
- PostgreSQLによるデータ永続化
- 完全なバリデーション機能
- UPSERT対応（同一ユーザー・プラットフォームの場合は更新）

## 技術スタック

- Python 3.x
- Flask 2.3.3
- PostgreSQL
- psycopg2-binary

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、適切な値を設定してください。

```bash
cp .env.example .env
```

`.env`ファイルを編集：
```
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=location_tracker
DATABASE_USER=username_here
DATABASE_PASSWORD=your_actual_password
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. PostgreSQLテーブルの確認

以下のテーブルが作成済みであることを確認してください：

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

## 起動方法

```bash
python app.py
```

サーバーは `http://localhost:5000` で起動します。

## API エンドポイント

### POST /api/register-token

FCMトークンを登録・更新します。

**リクエスト例（成功）:**
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

**レスポンス（成功）:**
```json
{
  "status": "success",
  "message": "トークンが登録されました"
}
```

**リクエスト例（エラー）:**
```bash
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "",
    "device_token": "test_token",
    "platform": "windows"
  }'
```

**レスポンス（エラー）:**
```json
{
  "status": "error",
  "message": "user_id: user_idは必須です; platform: platformは['android', 'ios']のいずれかである必要があります",
  "error_code": "VALIDATION_ERROR"
}
```

### GET /api/health

ヘルスチェック用エンドポイント

```bash
curl http://localhost:5000/api/health
```

### GET /

API情報を表示

```bash
curl http://localhost:5000/
```

## バリデーション

### user_id
- 必須
- 1-100文字
- 英数字、アンダースコア、ハイフンのみ

### device_token
- 必須
- 空文字列不可

### platform
- 必須
- "android" または "ios" のみ

### device_info
- オプション
- 有効なJSON形式

## エラーコード

- `VALIDATION_ERROR`: バリデーションエラー
- `INVALID_FORMAT`: リクエスト形式エラー
- `INTERNAL_SERVER_ERROR`: サーバー内部エラー

## ログ

- コンソール出力とファイル出力（`app.log`）
- リクエスト受信、バリデーション、データベース操作を記録

## プロジェクト構造

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
└── README.md          # このファイル
```