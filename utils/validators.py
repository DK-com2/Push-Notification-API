import re
import json
from datetime import datetime
from dateutil import parser
from typing import List, Dict, Any

class ValidationError(Exception):
    def __init__(self, message, error_code="VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

def validate_user_id(user_id):
    if not user_id:
        raise ValidationError("user_idは必須です")
    
    if not isinstance(user_id, str):
        raise ValidationError("user_idは文字列である必要があります")
    
    if len(user_id) < 1 or len(user_id) > 100:
        raise ValidationError("user_idは1-100文字である必要があります")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise ValidationError("user_idは英数字、アンダースコア、ハイフンのみ使用可能です")
    
    return True

def validate_device_token(device_token):
    if not device_token:
        raise ValidationError("device_tokenは必須です")
    
    if not isinstance(device_token, str):
        raise ValidationError("device_tokenは文字列である必要があります")
    
    if device_token.strip() == "":
        raise ValidationError("device_tokenは空文字列にできません")
    
    return True

def validate_platform(platform):
    if not platform:
        raise ValidationError("platformは必須です")
    
    if not isinstance(platform, str):
        raise ValidationError("platformは文字列である必要があります")
    
    valid_platforms = ["android", "ios"]
    if platform.lower() not in valid_platforms:
        raise ValidationError(f"platformは{valid_platforms}のいずれかである必要があります")
    
    return True

def validate_device_info(device_info):
    if device_info is None:
        return True
    
    if not isinstance(device_info, dict):
        raise ValidationError("device_infoはJSONオブジェクトである必要があります")
    
    try:
        json.dumps(device_info)
    except (TypeError, ValueError):
        raise ValidationError("device_infoは有効なJSON形式である必要があります")
    
    return True

def validate_register_token_request(data):
    errors = []
    
    try:
        validate_user_id(data.get('user_id'))
    except ValidationError as e:
        errors.append(f"user_id: {e.message}")
    
    try:
        validate_device_token(data.get('device_token'))
    except ValidationError as e:
        errors.append(f"device_token: {e.message}")
    
    try:
        validate_platform(data.get('platform'))
    except ValidationError as e:
        errors.append(f"platform: {e.message}")
    
    try:
        validate_device_info(data.get('device_info'))
    except ValidationError as e:
        errors.append(f"device_info: {e.message}")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return True

# 位置情報バリデーション関数

def validate_latitude(latitude):
    """緯度のバリデーション"""
    if latitude is None:
        raise ValidationError("緯度は必須です", "LATITUDE_REQUIRED")
    
    if not isinstance(latitude, (int, float)):
        raise ValidationError("緯度は数値である必要があります", "LATITUDE_INVALID_TYPE")
    
    if latitude < -90 or latitude > 90:
        raise ValidationError("緯度は-90から90の範囲である必要があります", "LATITUDE_OUT_OF_RANGE")
    
    return True

def validate_longitude(longitude):
    """経度のバリデーション"""
    if longitude is None:
        raise ValidationError("経度は必須です", "LONGITUDE_REQUIRED")
    
    if not isinstance(longitude, (int, float)):
        raise ValidationError("経度は数値である必要があります", "LONGITUDE_INVALID_TYPE")
    
    if longitude < -180 or longitude > 180:
        raise ValidationError("経度は-180から180の範囲である必要があります", "LONGITUDE_OUT_OF_RANGE")
    
    return True

def validate_timestamp(timestamp_str):
    """タイムスタンプのバリデーション（ISO 8601形式）"""
    if not timestamp_str:
        raise ValidationError("タイムスタンプは必須です", "TIMESTAMP_REQUIRED")
    
    if not isinstance(timestamp_str, str):
        raise ValidationError("タイムスタンプは文字列である必要があります", "TIMESTAMP_INVALID_TYPE")
    
    try:
        # ISO 8601形式の日時文字列をパース
        parsed_dt = parser.isoparse(timestamp_str)
        return parsed_dt
    except ValueError as e:
        raise ValidationError("タイムスタンプはISO 8601形式である必要があります", "TIMESTAMP_INVALID_FORMAT")

def validate_point(point_data):
    """単一の位置情報ポイントのバリデーション"""
    if not isinstance(point_data, dict):
        raise ValidationError("位置情報データはオブジェクトである必要があります", "POINT_INVALID_TYPE")
    
    errors = []
    
    try:
        validate_latitude(point_data.get('latitude'))
    except ValidationError as e:
        errors.append(f"latitude: {e.message}")
    
    try:
        validate_longitude(point_data.get('longitude'))
    except ValidationError as e:
        errors.append(f"longitude: {e.message}")
    
    try:
        timestamp = validate_timestamp(point_data.get('timestamp'))
        point_data['parsed_timestamp'] = timestamp  # パース済みの日時を保存
    except ValidationError as e:
        errors.append(f"timestamp: {e.message}")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return True

def validate_points_upload_request(data):
    """位置情報一括アップロードリクエストのバリデーション"""
    if not isinstance(data, dict):
        raise ValidationError("リクエストデータはJSONオブジェクトである必要があります", "REQUEST_INVALID_TYPE")
    
    points = data.get('points')
    if not points:
        raise ValidationError("pointsフィールドは必須です", "POINTS_REQUIRED")
    
    if not isinstance(points, list):
        raise ValidationError("pointsは配列である必要があります", "POINTS_INVALID_TYPE")
    
    if len(points) == 0:
        raise ValidationError("少なくとも1つの位置情報が必要です", "POINTS_EMPTY")
    
    if len(points) > 1000:
        raise ValidationError("一度にアップロードできる位置情報は最大1000件です", "POINTS_TOO_MANY")
    
    # 各ポイントをバリデーション
    for i, point in enumerate(points):
        try:
            validate_point(point)
        except ValidationError as e:
            raise ValidationError(f"points[{i}]: {e.message}", e.error_code)
    
    return True

def validate_points_get_request(start_time_str, end_time_str):
    """位置情報取得リクエストのバリデーション"""
    errors = []
    
    start_time = None
    end_time = None
    
    try:
        start_time = validate_timestamp(start_time_str)
    except ValidationError as e:
        errors.append(f"start_time: {e.message}")
    
    try:
        end_time = validate_timestamp(end_time_str)
    except ValidationError as e:
        errors.append(f"end_time: {e.message}")
    
    # 両方の日時が正常にパースできた場合の追加チェック
    if start_time and end_time:
        if start_time >= end_time:
            errors.append("start_timeはend_timeより前である必要があります")
        
        # 期間チェック（最大30日）
        time_diff = end_time - start_time
        if time_diff.days > 30:
            errors.append("取得期間は最大30日間です")
    
    if errors:
        raise ValidationError("; ".join(errors))
    
    return start_time, end_time