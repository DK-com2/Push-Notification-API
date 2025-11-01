# Push Notification Token Registration API & Location Sharing API

FCMプッシュ通知システムと位置情報共有システムのバックエンドAPI

## 機能

### 🔔 Push Notification API
- **JWT認証によるセキュアなトークン登録**
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

# Supabase設定
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# JWT設定（重要: SupabaseプロジェクトのJWT Secretを設定）
# Supabase Dashboard > Project Settings > API > JWT Secret から取得
SUPABASE_JWT_SECRET=your-supabase-jwt-secret-here

# テスト設定（test_location_api.py 用）
API_BASE_URL=http://localhost:5000
TEST_PASSWORD=your-test-user-password-here
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

FCMトークンを登録・更新します。**JWT認証が必要です。**

**重要:** user_idはJWTトークンから自動的に取得されます。リクエストボディのuser_idは無視されます。

**リクエスト例（成功）:**
```bash
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
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

**リクエスト例（認証エラー）:**
```bash
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "test_token",
    "platform": "android"
  }'
```

**レスポンス（認証エラー）:**
```json
{
  "status": "error",
  "message": "認証が必要です",
  "error_code": "UNAUTHORIZED"
}
```

**リクエスト例（バリデーションエラー）:**
```bash
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "device_token": "test_token",
    "platform": "windows"
  }'
```

**レスポンス（バリデーションエラー）:**
```json
{
  "status": "error",
  "message": "platform: platformは['android', 'ios']のいずれかである必要があります",
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
- JWTトークンから自動取得（リクエストボディでの指定は不要）
- JWTの "sub" クレームから取得

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

**両方のAPI（Push Notification API と Location Sharing API）でJWT認証が必要です。**

### トークンの取得方法

#### 本番環境（推奨）
Supabase Authenticationでログインしてトークンを取得：

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
auth_response = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "password"
})
jwt_token = auth_response.session.access_token
```

#### 開発・テスト環境
`utils.auth.create_access_token()`でローカル生成も可能（SUPABASE_JWT_SECRETが必要）

### リクエストヘッダー

以下の形式でJWTトークンを送信してください：

```
Authorization: Bearer <JWT_TOKEN>
```

### JWTペイロード構造

Supabaseが発行するJWTには以下の情報が含まれます：
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1640995200,
  "iat": 1640991600,
  "role": "authenticated"
}
```

**重要:** APIは `sub`（ユーザーID）を使用してユーザーを識別します。

### JWT Secretの設定

`.env`ファイルに**SupabaseプロジェクトのJWT Secret**を設定してください：

```bash
SUPABASE_JWT_SECRET=your-supabase-jwt-secret-here
```

**取得方法:**
1. Supabase Dashboard にアクセス
2. Project Settings > API に移動
3. JWT Secret をコピー

## エラーコード

### 共通エラーコード
- `VALIDATION_ERROR`: バリデーションエラー
- `INVALID_FORMAT`: リクエスト形式エラー
- `INTERNAL_SERVER_ERROR`: サーバー内部エラー

### API固有エラーコード
- `UNAUTHORIZED`: JWT認証エラー（両API共通）
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

### Pythonスクリプトによるテスト（推奨）

`test_location_api.py` を使用して、Supabase認証を含む包括的なテストが可能です：

#### 1. 環境設定

`.env`ファイルに以下を追加：
```bash
API_BASE_URL=http://localhost:5000  # ローカルテスト用
TEST_PASSWORD=your-password-here     # Supabaseユーザーのパスワード
SUPABASE_JWT_SECRET=your-jwt-secret  # 必須
```

#### 2. テスト実行

```bash
python test_location_api.py
```

テスト方法を選択：
- **方法1: Supabase Authでログイン（推奨）**
  - 本番環境と同じ認証フロー
  - 実際のSupabaseユーザーでログイン
  - TEST_PASSWORDが必要

- **方法2: テスト用JWT生成（開発用）**
  - ローカルでJWTを生成
  - SUPABASE_JWT_SECRETで署名
  - パスワード不要

#### 3. テスト内容

**自動実行されるテスト:**
- ✅ FCMトークン登録API（JWT認証付き）
- ✅ 認証なしでアクセス → 401エラー確認
- ✅ 無効なJWTでアクセス → 401エラー確認

**成功時の出力例:**
```
🎯 合計: 3/3 テスト成功
🎉 すべてのテストが成功しました！
```

### 基本テスト（curl）
```bash
# 基本情報確認
curl http://localhost:5000/

# ヘルスチェック
curl http://localhost:5000/api/health

# FCMトークン登録（JWT認証付き）
curl -X POST http://localhost:5000/api/register-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"device_token": "test-token", "platform": "android"}'
```

### その他のAPIテストツール
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
│   ├── token_routes.py        # Push Notification API（JWT認証付き）
│   └── location_routes.py     # Location Sharing API（JWT認証付き）
├── utils/
│   ├── validators.py          # バリデーション関数
│   └── auth.py                # Supabase JWT認証
├── test_location_api.py       # APIテストスクリプト
├── debug_jwt.py               # JWTデバッグツール
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

## セキュリティ

### JWT認証によるアクセス制御
- すべてのAPIエンドポイント（/api/register-token, /points）でJWT認証が必須
- Supabase JWT Secretで署名されたトークンのみ受け付け
- user_idはJWTの`sub`クレームから自動取得（改ざん不可）

### ユーザーデータの保護
- ユーザーは自分のデータのみアクセス可能
- FCMトークン登録: JWTから取得したuser_idでのみ登録可能
- 位置情報: JWTから取得したuser_idでのみ読み書き可能
- 他のユーザーのuser_idを指定してもアクセス不可

### 推奨事項
- `.env`ファイルは絶対にコミットしない（`.gitignore`に追加済み）
- `SUPABASE_JWT_SECRET`は厳重に管理
- 本番環境では必ずHTTPS通信を使用
- 定期的なトークンの更新を推奨

## API仕様書準拠

位置情報APIは以下の仕様に完全準拠しています：
- 一括アップロード上限: 1000件/リクエスト
- 取得期間制限: 最大30日間
- タイムスタンプ: ISO 8601形式
- 認証: Supabase JWT Bearer Token
- バリデーション: 緯度(-90〜90)、経度(-180〜180)

## 変更履歴

### 2025-11-01
- **FCMトークン登録APIにJWT認証を追加**
  - JWT認証が必須に（認証なしは401エラー）
  - user_idはJWTから自動取得（セキュリティ強化）
  - リクエストボディのuser_idは不要に

- **Supabase JWT完全対応**
  - utils/auth.pyをSupabase JWT検証に対応
  - audience（aud）検証のスキップ対応
  - Supabase Authで発行されたトークンを正しく検証

- **バリデーション修正**
  - utils/validators.pyからuser_idバリデーションを削除
  - device_token, platform, device_infoのバリデーションは維持

- **テストツール追加**
  - test_location_api.py: 自動テストスクリプト
  - debug_jwt.py: JWTデバッグツール
  - Supabase Auth / ローカルJWT生成の両方に対応

- **ドキュメント更新**
  - README.mdを最新の実装に更新
  - JWT認証の詳細説明を追加
  - セキュリティセクションを追加