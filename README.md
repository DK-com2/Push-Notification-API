# Push Notification Token Registration API & Location Sharing API

FCMプッシュ通知システムと位置情報共有システムのバックエンドAPI

## 機能

### 🔔 Push Notification API
- FCMトークンの登録・更新
- PostgreSQLによるデータ永続化
- 完全なバリデーション機能
- UPSERT対応（同一ユーザー・プラットフォームの場合は更新）

### 📍 Location Sharing API
- JWT認証による位置情報の安全な管理
- 位置情報の一括アップロード（最大1000件）
- 期間指定での位置情報取得（最大30日間）
- ISO 8601タイムスタンプ対応
- 緯度・経度の厳密なバリデーション

## 技術スタック

- Python 3.x
- Flask 2.3.3
- PostgreSQL
- psycopg2-binary
- python-jose (JWT処理)
- supabase-py (認証)
- python-dateutil (日時処理)

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
# データベース設定
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=location_tracker
DATABASE_USER=username_here
DATABASE_PASSWORD=your_actual_password

# Flask設定
FLASK_ENV=development
FLASK_DEBUG=True

# Supabase設定（位置情報API用）
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# JWT設定
SECRET_KEY=your-secret-key-for-jwt-signing
```

### 3. PostgreSQLテーブルの確認

以下のテーブルが作成済みであることを確認してください：

#### Push Notification API用テーブル
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

#### Location Sharing API用テーブル
```sql
CREATE TABLE app_locations (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT chk_longitude CHECK (longitude >= -180 AND longitude <= 180)
);

CREATE INDEX idx_app_locations_user_id ON app_locations (user_id);
CREATE INDEX idx_app_locations_timestamp ON app_locations (timestamp DESC);
CREATE INDEX idx_app_locations_user_time ON app_locations (user_id, timestamp DESC);
```

## 起動方法

```bash
python app.py
```

サーバーは `http://localhost:5000` で起動します。

## API エンドポイント

### 🏠 基本情報

#### GET /
API情報とエンドポイント一覧を表示
```bash
curl http://localhost:5000/
```

#### GET /api/health
ヘルスチェック用エンドポイント
```bash
curl http://localhost:5000/api/health
```

---

### 🔔 Push Notification API

#### POST /api/register-token

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

---

### 📍 Location Sharing API

#### POST /points
位置情報を一括アップロードします。**JWT認証が必要です。**

**リクエスト例:**
```bash
curl -X POST http://localhost:5000/points \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "points": [
      {
        "latitude": 35.6895,
        "longitude": 139.6917,
        "timestamp": "2025-08-31T12:00:00Z"
      },
      {
        "latitude": 35.6762,
        "longitude": 139.7575,
        "timestamp": "2025-08-31T12:30:00Z"
      }
    ]
  }'
```

**レスポンス（成功）:**
```json
{
  "status": "success",
  "message": "2件の位置情報を保存しました",
  "saved_count": 2,
  "total_count": 2
}
```

#### GET /points
期間指定で位置情報を取得します。**JWT認証が必要です。**

**リクエスト例:**
```bash
curl "http://localhost:5000/points?start_time=2025-08-31T00:00:00Z&end_time=2025-08-31T23:59:59Z" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**レスポンス（成功）:**
```json
{
  "points": [
    {
      "latitude": 35.6895,
      "longitude": 139.6917,
      "timestamp": "2025-08-31T12:00:00Z"
    },
    {
      "latitude": 35.6762,
      "longitude": 139.7575,
      "timestamp": "2025-08-31T12:30:00Z"
    }
  ],
  "count": 2,
  "start_time": "2025-08-31T00:00:00Z",
  "end_time": "2025-08-31T23:59:59Z"
}

## バリデーション

### 🔔 Push Notification API

#### user_id
- 必須
- 1-100文字
- 英数字、アンダースコア、ハイフンのみ

#### device_token
- 必須
- 空文字列不可

#### platform
- 必須
- "android" または "ios" のみ

#### device_info
- オプション
- 有効なJSON形式

### 📍 Location Sharing API

#### 位置情報（points）
- 必須
- 配列形式
- 最大1000件まで

#### latitude（緯度）
- 必須
- 数値型
- -90 ～ 90 の範囲

#### longitude（経度）
- 必須
- 数値型
- -180 ～ 180 の範囲

#### timestamp
- 必須
- ISO 8601形式の文字列
- 例: "2025-08-31T12:00:00Z"

#### 期間指定（GET /points）
- start_time, end_time 両方必須
- ISO 8601形式
- 最大30日間の期間
- start_time < end_time

## JWT認証

Location Sharing APIでは、以下の形式でJWTトークンを送信してください：

```
Authorization: Bearer <JWT_TOKEN>
```

JWTトークンはSupabase Authenticationから取得するか、適切なペイロードで生成してください：
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1640995200
}
```

## エラーコード

### 共通エラーコード
- `VALIDATION_ERROR`: バリデーションエラー
- `INVALID_FORMAT`: リクエスト形式エラー
- `INTERNAL_SERVER_ERROR`: サーバー内部エラー

### Location Sharing API 固有エラーコード
- `UNAUTHORIZED`: JWT認証エラー
- `LATITUDE_OUT_OF_RANGE`: 緯度が範囲外
- `LONGITUDE_OUT_OF_RANGE`: 経度が範囲外
- `TIMESTAMP_INVALID_FORMAT`: タイムスタンプ形式エラー
- `POINTS_TOO_MANY`: 位置情報が1000件を超過
- `POINTS_EMPTY`: 位置情報が0件
- `MISSING_PARAMETERS`: 必須パラメータ不足

## ログ

- コンソール出力とファイル出力（`app.log`）
- リクエスト受信、バリデーション、データベース操作を記録

## テスト

APIの動作確認は以下の方法で行えます：

### 基本テスト（curl/PowerShell）
```bash
# 基本情報確認
curl http://localhost:5000/

# ヘルスチェック
curl http://localhost:5000/api/health
```

### APIテストツール推奨
- Postman
- Thunder Client（VS Code拡張）
- HTTPie

## プロジェクト構造

```
Push-Notification-API/
├── app.py                     # メインアプリケーション
├── config.py                  # 設定管理
├── database.py                # PostgreSQL接続設定
├── models/
│   └── device_token.py        # DeviceTokenモデル
├── routes/
│   ├── token_routes.py        # Push Notification API
│   └── location_routes.py     # Location Sharing API
├── utils/
│   ├── validators.py          # バリデーション関数
│   └── auth.py                # JWT認証
├── requirements.txt           # 依存パッケージ
├── .env.example              # 環境変数テンプレート
└── README.md                 # このファイル
```

## システム連携

このAPIは以下のシステムと連携します：

### Pathfinder Web
- 同じSupabase Authenticationを使用
- 同じJWT Secret Keyで認証
- 位置情報データを共有表示

### スマホアプリケーション
- Supabase認証でJWTトークン取得
- POST /pointsで位置情報をアップロード
- app_locationsテーブルにデータ保存

## API仕様書準拠

位置情報APIは以下の仕様に完全準拠しています：
- 一括アップロード上限: 1000件/リクエスト  
- 取得期間制限: 最大30日間
- タイムスタンプ: ISO 8601形式
- 認証: Supabase JWT Bearer Token
- バリデーション: 緯度(-90〜90)、経度(-180〜180)