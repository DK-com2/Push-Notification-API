#!/usr/bin/env python3
"""
全ユーザーに位置情報リクエストを送信するスクリプト

使い方:
    python send_location_requests.py

説明:
    - データベースから全てのFCMトークンを取得
    - 全ユーザーに位置情報リクエストをFCM経由で送信
    - 送信結果をログに記録
"""

import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数読み込み
load_dotenv()

from database import db
from utils.fcm import send_location_requests_batch, initialize_firebase

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('fcm_batch_send.log'),
        logging.StreamHandler()
    ]
)


def get_all_device_tokens():
    """
    データベースから全てのデバイストークンを取得

    Returns:
        list: [{"token": str, "platform": str, "user_id": str}, ...]
    """
    cursor = db.get_cursor()
    if not cursor:
        logging.error("データベース接続に失敗しました")
        return []

    try:
        query = """
            SELECT user_id, device_token, platform
            FROM device_tokens
            ORDER BY updated_at DESC
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        tokens_list = []
        for row in rows:
            tokens_list.append({
                "user_id": row['user_id'],
                "token": row['device_token'],
                "platform": row['platform']
            })

        logging.info(f"デバイストークン取得: {len(tokens_list)}件")
        return tokens_list

    except Exception as e:
        logging.error(f"デバイストークン取得エラー: {str(e)}")
        return []

    finally:
        cursor.close()


def main():
    """
    メイン処理
    """
    print("=" * 70)
    print("📱 位置情報リクエスト一括送信スクリプト")
    print("=" * 70)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Firebase初期化
        print("🔥 Firebase Admin SDK初期化中...")
        initialize_firebase()
        print("✅ Firebase初期化完了")
        print()

        # デバイストークン取得
        print("📋 デバイストークン取得中...")
        tokens_list = get_all_device_tokens()

        if not tokens_list:
            print("⚠️  送信対象のデバイストークンがありません")
            return

        print(f"✅ {len(tokens_list)}件のデバイストークンを取得しました")
        print()

        # プラットフォーム別集計
        android_count = sum(1 for t in tokens_list if t['platform'] == 'android')
        ios_count = sum(1 for t in tokens_list if t['platform'] == 'ios')
        print(f"   - Android: {android_count}件")
        print(f"   - iOS: {ios_count}件")
        print()

        # 送信確認
        response = input(f"🚀 {len(tokens_list)}件のデバイスに送信しますか？ (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ キャンセルしました")
            return

        print()
        print("📤 FCMメッセージ送信中...")
        print("-" * 70)

        # 一括送信実行
        result = send_location_requests_batch(tokens_list)

        print("-" * 70)
        print()
        print("📊 送信結果サマリー")
        print("=" * 70)
        print(f"合計: {result['total']}件")
        print(f"✅ 成功: {result['success']}件")
        print(f"❌ 失敗: {result['failed']}件")
        print("=" * 70)
        print()

        # 失敗したトークンがあれば表示
        if result['failed'] > 0:
            print("⚠️  失敗したトークン:")
            for item in result['results']:
                if not item['success']:
                    user_id = item.get('user_id', 'unknown')
                    platform = item.get('platform', 'unknown')
                    error = item.get('error', 'unknown error')
                    print(f"   - user_id: {user_id}, platform: {platform}")
                    print(f"     エラー: {error}")
            print()

        # 成功率計算
        if result['total'] > 0:
            success_rate = (result['success'] / result['total']) * 100
            print(f"📈 成功率: {success_rate:.1f}%")
        print()

        print("🎉 処理完了")
        print(f"詳細ログ: fcm_batch_send.log")

    except KeyboardInterrupt:
        print()
        print("⚠️  ユーザーによって中断されました")
        sys.exit(1)

    except Exception as e:
        logging.error(f"予期しないエラー: {str(e)}", exc_info=True)
        print(f"❌ エラーが発生しました: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
