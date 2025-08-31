from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from utils.validators import ValidationError, validate_points_upload_request, validate_points_get_request
from utils.auth import verify_token
from database import db

location_bp = Blueprint('location', __name__)

def get_current_user():
    """Authorization headerからJWTトークンを取得してユーザー情報を返す"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    return verify_token(token)

@location_bp.route('/points', methods=['POST'])
def upload_points():
    """位置情報を一括アップロードする"""
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
        logging.info(f"位置情報アップロード開始: user_id={user_id}")
        
        # リクエストデータの検証
        if not request.is_json:
            logging.warning("リクエストがJSON形式ではありません")
            return jsonify({
                "status": "error",
                "message": "リクエストはJSON形式である必要があります",
                "error_code": "INVALID_FORMAT"
            }), 400
        
        data = request.get_json()
        
        # バリデーション
        validate_points_upload_request(data)
        points = data['points']
        
        # データベースに保存
        cursor = db.get_cursor()
        if not cursor:
            raise Exception("データベース接続に失敗しました")
        
        insert_query = """
            INSERT INTO app_locations (user_id, latitude, longitude, timestamp)
            VALUES (%s, %s, %s, %s)
        """
        
        saved_count = 0
        for point in points:
            try:
                cursor.execute(insert_query, (
                    user_id,
                    point['latitude'],
                    point['longitude'],
                    point['parsed_timestamp']
                ))
                saved_count += 1
            except Exception as e:
                logging.error(f"位置情報の保存に失敗: {e}")
                # 個別のポイント保存失敗は警告レベルで記録し、処理を継続
                continue
        
        db.commit()
        cursor.close()
        
        logging.info(f"位置情報アップロード完了: user_id={user_id}, 保存件数={saved_count}/{len(points)}")
        
        return jsonify({
            "status": "success",
            "message": f"{saved_count}件の位置情報を保存しました",
            "saved_count": saved_count,
            "total_count": len(points)
        }), 201
        
    except ValidationError as e:
        logging.warning(f"バリデーションエラー: {e.message}")
        return jsonify({
            "status": "error",
            "message": e.message,
            "error_code": e.error_code
        }), 400
        
    except Exception as e:
        logging.error(f"サーバーエラー: {str(e)}")
        db.rollback()
        return jsonify({
            "status": "error",
            "message": "内部サーバーエラーが発生しました",
            "error_code": "INTERNAL_SERVER_ERROR"
        }), 500

@location_bp.route('/points', methods=['GET'])
def get_points():
    """指定範囲の位置情報を取得する"""
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
        
        # クエリパラメータの取得
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        if not start_time_str or not end_time_str:
            return jsonify({
                "status": "error",
                "message": "start_timeとend_timeパラメータは必須です",
                "error_code": "MISSING_PARAMETERS"
            }), 400
        
        # バリデーション
        start_time, end_time = validate_points_get_request(start_time_str, end_time_str)
        
        logging.info(f"位置情報取得: user_id={user_id}, 期間={start_time} - {end_time}")
        
        # データベースから取得
        cursor = db.get_cursor()
        if not cursor:
            raise Exception("データベース接続に失敗しました")
        
        query = """
            SELECT latitude, longitude, timestamp
            FROM app_locations
            WHERE user_id = %s 
            AND timestamp >= %s 
            AND timestamp < %s
            ORDER BY timestamp ASC
        """
        
        cursor.execute(query, (user_id, start_time, end_time))
        rows = cursor.fetchall()
        
        # レスポンス用のデータ形式に変換
        points = []
        for row in rows:
            points.append({
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "timestamp": row['timestamp'].isoformat()
            })
        
        cursor.close()
        
        logging.info(f"位置情報取得完了: user_id={user_id}, 取得件数={len(points)}")
        
        return jsonify({
            "points": points,
            "count": len(points),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
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