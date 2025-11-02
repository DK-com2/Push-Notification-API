"""
Firebase Cloud Messaging (FCM) 送信機能
位置情報リクエストをスマホアプリに送信
"""

import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

# Firebase Admin SDK初期化（モジュールレベルで1回のみ）
_firebase_app = None

def initialize_firebase():
    """
    Firebase Admin SDKを初期化
    既に初期化済みの場合はスキップ
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    try:
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if not credentials_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH が.envに設定されていません")

        # ファイルの存在確認
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Firebase秘密鍵ファイルが見つかりません: {credentials_path}")

        # Firebase Admin SDK初期化
        cred = credentials.Certificate(credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred)

        logging.info(f"Firebase Admin SDK初期化成功: {credentials_path}")
        return _firebase_app

    except Exception as e:
        logging.error(f"Firebase初期化エラー: {str(e)}")
        raise


def send_location_request(device_token: str, platform: str = "android") -> dict:
    """
    単一のデバイスに位置情報リクエストを送信

    Args:
        device_token: FCMデバイストークン
        platform: プラットフォーム ("android" or "ios")

    Returns:
        送信結果の辞書 {"success": bool, "message_id": str or None, "error": str or None}
    """
    try:
        # Firebase初期化確認
        initialize_firebase()

        # リクエストIDとタイムスタンプを生成
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # データメッセージ作成（Android/iOS共通）
        data_payload = {
            "type": "location_request",
            "request_id": request_id,
            "timestamp": timestamp,
            "message": "現在地を送信してください"
        }

        # プラットフォーム別の設定
        android_config = messaging.AndroidConfig(
            priority="high",
            data=data_payload
        )

        apns_config = messaging.APNSConfig(
            headers={
                "apns-priority": "10",
                "apns-push-type": "background"
            },
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    content_available=True,
                    custom_data=data_payload
                )
            )
        )

        # メッセージ作成
        message = messaging.Message(
            data=data_payload,
            token=device_token,
            android=android_config if platform == "android" else None,
            apns=apns_config if platform == "ios" else None
        )

        # FCMメッセージ送信（dry_runオプションでテスト可能）
        try:
            response = messaging.send(message, dry_run=False)
            logging.info(f"FCM送信成功: token={device_token[:20]}..., message_id={response}, request_id={request_id}")
        except Exception as send_error:
            # 送信時のエラーを詳細にログ
            logging.warning(f"FCM送信中のエラー: {str(send_error)}, token={device_token[:20]}...")
            raise

        return {
            "success": True,
            "message_id": response,
            "request_id": request_id,
            "timestamp": timestamp,
            "error": None
        }

    except firebase_admin.exceptions.FirebaseError as e:
        error_msg = f"FCM送信エラー: {str(e)}"
        logging.error(f"{error_msg}, token={device_token[:20]}...")
        return {
            "success": False,
            "message_id": None,
            "request_id": None,
            "timestamp": None,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"予期しないエラー: {str(e)}"
        logging.error(f"{error_msg}, token={device_token[:20]}...")
        return {
            "success": False,
            "message_id": None,
            "request_id": None,
            "timestamp": None,
            "error": error_msg
        }


def send_location_requests_batch_fast(tokens_list: list, batch_size: int = 500) -> dict:
    """
    複数のデバイスに高速一括送信（Multicast API使用）

    Args:
        tokens_list: [{"token": str, "platform": str, "user_id": str}, ...]
        batch_size: 1回の送信に含める最大トークン数（FCMの制限: 500）

    Returns:
        送信結果のサマリー
    """
    try:
        initialize_firebase()

        total = len(tokens_list)
        all_results = []

        # リクエストIDとタイムスタンプ生成
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        # データメッセージ
        data_payload = {
            "type": "location_request",
            "request_id": request_id,
            "timestamp": timestamp,
            "message": "現在地を送信してください"
        }

        # プラットフォーム別にグループ化
        android_tokens = [item for item in tokens_list if item.get('platform') == 'android']
        ios_tokens = [item for item in tokens_list if item.get('platform') == 'ios']

        logging.info(f"一括FCM送信開始: 合計={total}, Android={len(android_tokens)}, iOS={len(ios_tokens)}")

        # Android送信
        if android_tokens:
            print(f"\n📱 Android端末に送信中... ({len(android_tokens)}件)")
            android_results = _send_multicast_platform(android_tokens, data_payload, "android", batch_size)
            all_results.extend(android_results)

        # iOS送信
        if ios_tokens:
            print(f"\n🍎 iOS端末に送信中... ({len(ios_tokens)}件)")
            ios_results = _send_multicast_platform(ios_tokens, data_payload, "ios", batch_size)
            all_results.extend(ios_results)

        # サマリー作成
        success_count = sum(1 for r in all_results if r['success'])
        failed_count = total - success_count

        summary = {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "results": all_results
        }

        logging.info(f"一括FCM送信完了: 成功={success_count}/{total}, 失敗={failed_count}")
        return summary

    except Exception as e:
        logging.error(f"一括FCM送信エラー: {str(e)}")
        return {
            "total": len(tokens_list),
            "success": 0,
            "failed": len(tokens_list),
            "error": str(e),
            "results": []
        }


def _send_multicast_platform(tokens_data: list, data_payload: dict, platform: str, batch_size: int) -> list:
    """
    プラットフォーム別のMulticast送信

    Args:
        tokens_data: トークン情報のリスト
        data_payload: 送信データ
        platform: "android" or "ios"
        batch_size: バッチサイズ

    Returns:
        送信結果のリスト
    """
    results = []
    total_tokens = len(tokens_data)

    # バッチに分割して送信
    for i in range(0, total_tokens, batch_size):
        batch = tokens_data[i:i + batch_size]
        batch_tokens = [item['token'] for item in batch]

        print(f"  バッチ {i//batch_size + 1}: {len(batch)}件送信中...")

        try:
            # MulticastMessageを作成
            if platform == "android":
                multicast_message = messaging.MulticastMessage(
                    data=data_payload,
                    tokens=batch_tokens,
                    android=messaging.AndroidConfig(priority="high", data=data_payload)
                )
            else:  # iOS
                multicast_message = messaging.MulticastMessage(
                    data=data_payload,
                    tokens=batch_tokens,
                    apns=messaging.APNSConfig(
                        headers={"apns-priority": "10", "apns-push-type": "background"},
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(content_available=True, custom_data=data_payload)
                        )
                    )
                )

            # Multicast送信
            batch_response = messaging.send_multicast(multicast_message)

            # 結果を個別に記録
            for idx, response in enumerate(batch_response.responses):
                token_info = batch[idx]
                if response.success:
                    results.append({
                        "success": True,
                        "message_id": response.message_id,
                        "user_id": token_info['user_id'],
                        "platform": platform,
                        "error": None
                    })
                else:
                    results.append({
                        "success": False,
                        "message_id": None,
                        "user_id": token_info['user_id'],
                        "platform": platform,
                        "error": str(response.exception) if response.exception else "Unknown error"
                    })

            print(f"    ✅ 成功: {batch_response.success_count}/{len(batch)}, ❌ 失敗: {batch_response.failure_count}")

        except Exception as e:
            # バッチ全体が失敗
            logging.error(f"Multicast送信エラー: {str(e)}")
            for token_info in batch:
                results.append({
                    "success": False,
                    "message_id": None,
                    "user_id": token_info['user_id'],
                    "platform": platform,
                    "error": str(e)
                })
            print(f"    ❌ バッチ送信失敗: {str(e)[:50]}...")

    return results


def send_location_requests_batch(tokens_list: list) -> dict:
    """
    複数のデバイスに一括で位置情報リクエストを送信

    Args:
        tokens_list: [{"token": str, "platform": str, "user_id": str}, ...]

    Returns:
        送信結果のサマリー {"total": int, "success": int, "failed": int, "results": list}
    """
    try:
        # Firebase初期化確認
        initialize_firebase()

        total = len(tokens_list)
        success_count = 0
        failed_count = 0
        results = []

        logging.info(f"一括FCM送信開始: {total}件")

        for index, item in enumerate(tokens_list, 1):
            device_token = item.get("token")
            platform = item.get("platform", "android")
            user_id = item.get("user_id")

            # プログレス表示
            print(f"[{index}/{total}] 送信中... user_id={user_id[:8]}..., platform={platform}")

            try:
                # 送信実行
                result = send_location_request(device_token, platform)

                # 結果記録
                result["user_id"] = user_id
                result["platform"] = platform
                results.append(result)

                if result["success"]:
                    success_count += 1
                    print(f"  ✅ 成功: message_id={result.get('message_id', 'N/A')}")
                else:
                    failed_count += 1
                    print(f"  ❌ 失敗: {result.get('error', 'Unknown error')[:50]}...")

            except Exception as e:
                # 個別の送信エラーでも処理を継続
                failed_count += 1
                error_result = {
                    "success": False,
                    "message_id": None,
                    "request_id": None,
                    "timestamp": None,
                    "error": str(e),
                    "user_id": user_id,
                    "platform": platform
                }
                results.append(error_result)
                print(f"  ❌ 例外発生: {str(e)[:50]}...")
                logging.error(f"送信例外: user_id={user_id}, error={str(e)}")

        summary = {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "results": results
        }

        logging.info(f"一括FCM送信完了: 成功={success_count}/{total}, 失敗={failed_count}")

        return summary

    except Exception as e:
        logging.error(f"一括FCM送信エラー: {str(e)}")
        return {
            "total": len(tokens_list),
            "success": 0,
            "failed": len(tokens_list),
            "error": str(e),
            "results": []
        }


def check_firebase_initialized() -> bool:
    """
    Firebase Admin SDKが初期化済みかチェック

    Returns:
        初期化済みの場合True
    """
    return _firebase_app is not None
