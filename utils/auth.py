from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Supabase JWT Secret（本番環境ではSupabaseプロジェクトのJWT Secretを使用）
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    テスト用JWTアクセストークンを作成

    注意: この関数は開発・テスト用です。
    本番環境ではSupabase Authが発行したトークンを使用してください。
    """
    if not SUPABASE_JWT_SECRET:
        raise ValueError("SUPABASE_JWT_SECRET が設定されていません")

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SUPABASE_JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """
    Supabase発行のJWTトークンを検証してユーザー情報を取得

    Args:
        token: Supabase Authが発行したJWTトークン

    Returns:
        ユーザー情報の辞書 {"user_id": str, "email": str} または None
    """
    if not SUPABASE_JWT_SECRET:
        logging.error("SUPABASE_JWT_SECRET が設定されていません")
        return None

    try:
        # Supabase JWT Secretで検証
        # audience検証を無効化（Supabaseの'authenticated'を受け入れるため）
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False}  # audienceの検証をスキップ
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            logging.warning("JWTペイロードに'sub'が含まれていません")
            return None

        # Supabaseのトークンには通常emailも含まれる
        email = payload.get("email")

        return {"user_id": user_id, "email": email}
    except JWTError as e:
        logging.warning(f"JWT検証エラー: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"トークン検証中の予期しないエラー: {str(e)}")
        return None