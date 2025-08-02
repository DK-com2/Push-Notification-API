import logging
import json
from datetime import datetime
from database import db
import psycopg2

class DeviceToken:
    def __init__(self, user_id=None, device_token=None, platform=None, device_info=None):
        self.user_id = user_id
        self.device_token = device_token
        self.platform = platform
        self.device_info = device_info
    
    def save(self):
        cursor = db.get_cursor()
        if not cursor:
            raise Exception("データベース接続に失敗しました")
        
        try:
            device_info_json = json.dumps(self.device_info) if self.device_info else None
            
            query = """
                INSERT INTO device_tokens (user_id, device_token, platform, device_info, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, platform)
                DO UPDATE SET
                    device_token = EXCLUDED.device_token,
                    device_info = EXCLUDED.device_info,
                    updated_at = EXCLUDED.updated_at
                RETURNING id, created_at, updated_at
            """
            
            now = datetime.now()
            cursor.execute(query, (
                self.user_id,
                self.device_token,
                self.platform,
                device_info_json,
                now,
                now
            ))
            
            result = cursor.fetchone()
            db.commit()
            
            logging.info(f"トークン保存成功: user_id={self.user_id}, platform={self.platform}")
            return {
                'id': result['id'],
                'created_at': result['created_at'],
                'updated_at': result['updated_at']
            }
            
        except psycopg2.Error as e:
            db.rollback()
            logging.error(f"トークン保存エラー: {e}")
            raise Exception(f"データベースエラー: {e}")
        finally:
            cursor.close()
    
    @staticmethod
    def get_by_user_and_platform(user_id, platform):
        cursor = db.get_cursor()
        if not cursor:
            return None
        
        try:
            query = """
                SELECT id, user_id, device_token, platform, device_info, created_at, updated_at
                FROM device_tokens
                WHERE user_id = %s AND platform = %s
            """
            
            cursor.execute(query, (user_id, platform))
            result = cursor.fetchone()
            
            if result:
                device_info = json.loads(result['device_info']) if result['device_info'] else None
                return {
                    'id': result['id'],
                    'user_id': result['user_id'],
                    'device_token': result['device_token'],
                    'platform': result['platform'],
                    'device_info': device_info,
                    'created_at': result['created_at'],
                    'updated_at': result['updated_at']
                }
            return None
            
        except psycopg2.Error as e:
            logging.error(f"トークン取得エラー: {e}")
            return None
        finally:
            cursor.close()