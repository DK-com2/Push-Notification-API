from flask import Blueprint, request, jsonify
import logging
from utils.validators import validate_register_token_request, ValidationError
from utils.auth import verify_token
from models.device_token import DeviceToken

token_bp = Blueprint('token', __name__)

def get_current_user():
    """Authorization headerからJWTトークンを取得してユーザー情報を返す"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    return verify_token(token)

@token_bp.route('/api/register-token', methods=['POST'])
def register_token():
    try:
        # 認証チェック
        current_user = get_current_user()
        if not current_user:
            logging.warning("認証に失敗しました")
            return jsonify({
                "status": "error",
                "message": "認証が必要です",
                "error_code": "UNAUTHORIZED"
            }), 401

        user_id = current_user['user_id']

        if not request.is_json:
            logging.warning("リクエストがJSON形式ではありません")
            return jsonify({
                "status": "error",
                "message": "リクエストはJSON形式である必要があります",
                "error_code": "INVALID_FORMAT"
            }), 400

        data = request.get_json()
        logging.info(f"トークン登録リクエスト受信: user_id={user_id}, platform={data.get('platform')}")

        validate_register_token_request(data)

        device_token = DeviceToken(
            user_id=user_id,
            device_token=data['device_token'],
            platform=data['platform'].lower(),
            device_info=data.get('device_info')
        )

        result = device_token.save()

        logging.info(f"トークン登録成功: user_id={user_id}, platform={data['platform']}")
        return jsonify({
            "status": "success",
            "message": "トークンが登録されました"
        }), 200
        
    except ValidationError as e:
        logging.warning(f"バリデーションエラー: {e.message}")
        return jsonify({
            "status": "error",
            "message": e.message,
            "error_code": e.error_code
        }), 400
        
    except Exception as e:
        logging.error(f"サーバーエラー: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "内部サーバーエラーが発生しました",
            "error_code": "INTERNAL_SERVER_ERROR"
        }), 500

@token_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "success",
        "message": "サービスは正常に動作しています"
    }), 200