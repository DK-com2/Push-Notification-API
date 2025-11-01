#!/usr/bin/env python3
"""
Push Notification API & Location Sharing API テストスクリプト
FCMトークン登録のテスト（Supabase JWT認証対応）
"""

import requests
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from utils.auth import create_access_token

# 環境変数を読み込み
load_dotenv()

# 設定
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# テスト用ユーザー情報
TEST_EMAIL = "daichispeak2@gmail.com"
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "")  # .envに設定してください

print("=" * 70)
print("🧪 Push Notification API テスト - FCMトークン登録")
print("=" * 70)
print(f"API URL: {API_BASE_URL}")
print(f"Supabase URL: {SUPABASE_URL}")
print("=" * 70)
print()


def test_with_supabase_auth():
    """
    【方法1】Supabase Authでログインしてテスト（推奨）
    本番環境と同じ認証フロー
    """
    print("🔑 方法1: Supabase Authでログイン")
    print("-" * 70)

    if not TEST_PASSWORD:
        print("❌ エラー: TEST_PASSWORDが.envに設定されていません")
        print("   .envファイルに以下を追加してください:")
        print(f"   TEST_PASSWORD=your-actual-password")
        return None

    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Supabase Authでログイン
        print(f"📧 ログイン中: {TEST_EMAIL}")
        auth_response = supabase.auth.sign_in_with_password({
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })

        # JWTトークンを取得
        jwt_token = auth_response.session.access_token
        user_id = auth_response.user.id

        print(f"✅ ログイン成功")
        print(f"   User ID: {user_id}")
        print(f"   Email: {TEST_EMAIL}")
        print(f"   Token: {jwt_token[:50]}...")
        print(f"   ✨ このトークンはSupabaseが発行した本物のトークンです")
        print()

        return jwt_token, user_id

    except Exception as e:
        print(f"❌ ログインエラー: {str(e)}")
        print()
        print("⚠️  以下を確認してください:")
        print("   1. Supabaseでユーザーが作成されているか")
        print(f"   2. TEST_EMAIL ({TEST_EMAIL}) が正しいか")
        print("   3. TEST_PASSWORD が正しいか")
        print("   4. SUPABASE_URL と SUPABASE_KEY が.envに設定されているか")
        return None


def test_with_local_jwt():
    """
    【方法2】テスト用JWT生成（開発・テスト用）
    ローカルでJWTを生成（SUPABASE_JWT_SECRETが必要）
    """
    print("🔧 方法2: テスト用JWT生成（開発用）")
    print("-" * 70)

    try:
        test_user_id = "a711d1e3-11de-42b9-bc1f-f20b0571b5d7"
        test_email = "iowlb3e5aq@sute.jp"

        # JWTトークンを生成（Supabase JWT Secretを使用）
        jwt_token = create_access_token({
            "sub": test_user_id,
            "email": test_email
        })

        print(f"✅ テスト用JWTトークンを生成しました")
        print(f"   User ID: {test_user_id}")
        print(f"   Email: {test_email}")
        print(f"   Token: {jwt_token[:50]}...")
        print(f"   ⚠️  このトークンはローカル生成です（開発・テスト用）")
        print(f"   ✅ Supabase JWT Secretで署名されているため、APIで検証可能です")
        print()

        return jwt_token, test_user_id

    except ValueError as e:
        print(f"❌ エラー: {str(e)}")
        print()
        print("⚠️  .envファイルにSUPABASE_JWT_SECRETを設定してください")
        print("   Supabase Dashboard > Project Settings > API > JWT Secret")
        return None


def test_register_fcm_token(jwt_token, test_name="正常系"):
    """
    FCMトークン登録APIをテスト
    """
    print(f"📱 FCMトークン登録テスト - {test_name}")
    print("-" * 70)

    # テスト用FCMトークンデータ
    fcm_data = {
        "device_token": "test-fcm-token-12345-abcde-67890",
        "platform": "android",
        "device_info": {
            "model": "Pixel 7",
            "os_version": "Android 14",
            "app_version": "1.0.0"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }

    print(f"📤 リクエスト送信:")
    print(f"   URL: {API_BASE_URL}/api/register-token")
    print(f"   Platform: {fcm_data['platform']}")
    print(f"   Device Token: {fcm_data['device_token']}")
    print()

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/register-token",
            headers=headers,
            json=fcm_data,
            timeout=10
        )

        print(f"📥 レスポンス:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Body:")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        print()

        if response.status_code == 200:
            print("✅ FCMトークン登録成功！")
            print("   JWTから取得したuser_idでトークンが登録されました")
            return True
        else:
            print(f"❌ FCMトークン登録失敗 (Status: {response.status_code})")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {str(e)}")
        return False

    print()


def test_register_without_auth():
    """
    認証なしでFCMトークン登録を試みるテスト（エラーケース）
    """
    print("🚫 認証エラーテスト - JWTなし")
    print("-" * 70)

    fcm_data = {
        "device_token": "test-token-no-auth",
        "platform": "android"
    }

    headers = {
        "Content-Type": "application/json"
        # Authorization headerなし
    }

    print(f"📤 リクエスト送信（JWT認証なし）:")
    print(f"   URL: {API_BASE_URL}/api/register-token")
    print()

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/register-token",
            headers=headers,
            json=fcm_data,
            timeout=10
        )

        print(f"📥 レスポンス:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Body:")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        print()

        if response.status_code == 401:
            print("✅ 正しく401 Unauthorizedが返されました")
            print("   認証なしのアクセスが正しく拒否されています")
            return True
        else:
            print(f"❌ 期待: 401, 実際: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {str(e)}")
        return False

    print()


def test_register_with_invalid_jwt():
    """
    無効なJWTでFCMトークン登録を試みるテスト（エラーケース）
    """
    print("🚫 認証エラーテスト - 無効なJWT")
    print("-" * 70)

    fcm_data = {
        "device_token": "test-token-invalid-jwt",
        "platform": "android"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer invalid-jwt-token-12345"
    }

    print(f"📤 リクエスト送信（無効なJWT）:")
    print(f"   URL: {API_BASE_URL}/api/register-token")
    print()

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/register-token",
            headers=headers,
            json=fcm_data,
            timeout=10
        )

        print(f"📥 レスポンス:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Body:")
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
        print()

        if response.status_code == 401:
            print("✅ 正しく401 Unauthorizedが返されました")
            print("   無効なJWTが正しく拒否されています")
            return True
        else:
            print(f"❌ 期待: 401, 実際: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {str(e)}")
        return False

    print()


def main():
    """
    メインテスト実行
    """
    print("🎯 テスト方法を選択してください:")
    print("1. Supabase Authでログイン（推奨・本番環境と同じ）")
    print("2. テスト用JWT生成（開発用）")
    print()

    choice = input("選択 (1 or 2): ").strip()
    print()
    print("=" * 70)
    print()

    # 認証方法の選択
    if choice == "1":
        auth_result = test_with_supabase_auth()
    elif choice == "2":
        auth_result = test_with_local_jwt()
    else:
        print("❌ 無効な選択です")
        return

    if not auth_result:
        print("❌ 認証に失敗したためテストを中止します")
        return

    jwt_token, user_id = auth_result

    print("=" * 70)
    print()

    # テスト実行
    print("🧪 テスト開始")
    print("=" * 70)
    print()

    results = []

    # 1. 正常系テスト
    results.append(("FCMトークン登録（JWT認証付き）", test_register_fcm_token(jwt_token)))
    print("=" * 70)
    print()

    # 2. 認証なしテスト
    results.append(("認証なしでアクセス", test_register_without_auth()))
    print("=" * 70)
    print()

    # 3. 無効なJWTテスト
    results.append(("無効なJWTでアクセス", test_register_with_invalid_jwt()))
    print("=" * 70)
    print()

    # テスト結果サマリー
    print("📊 テスト結果サマリー")
    print("=" * 70)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for _, result in results if result)
    print(f"\n🎯 合計: {passed}/{total} テスト成功")

    if passed == total:
        print("🎉 すべてのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました")


if __name__ == "__main__":
    main()
