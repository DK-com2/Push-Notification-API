import psycopg2
import psycopg2.extras
import logging
from config import Config

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
        
    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=self.config.DATABASE_HOST,
                port=self.config.DATABASE_PORT,
                database=self.config.DATABASE_NAME,
                user=self.config.DATABASE_USER,
                password=self.config.DATABASE_PASSWORD
            )
            logging.info("データベース接続が成功しました")
            return True
        except psycopg2.Error as e:
            logging.error(f"データベース接続エラー: {e}")
            return False
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("データベース接続を切断しました")
    
    def get_cursor(self):
        if not self.connection or self.connection.closed:
            if not self.connect():
                return None
        return self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    def commit(self):
        if self.connection:
            self.connection.commit()
    
    def rollback(self):
        if self.connection:
            self.connection.rollback()

db = Database()