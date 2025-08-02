import re
import json

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