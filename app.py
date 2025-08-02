from flask import Flask
import logging
from config import Config
from routes.token_routes import token_bp
from database import db

def create_app():
    app = Flask(__name__)
    config = Config()
    
    app.config['DEBUG'] = config.FLASK_DEBUG
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    
    app.register_blueprint(token_bp)
    
    @app.teardown_appcontext
    def close_db(error):
        if error:
            db.rollback()
        db.disconnect()
    
    @app.route('/', methods=['GET'])
    def root():
        return {
            "message": "Push Notification Token Registration API",
            "status": "running",
            "endpoints": {
                "register_token": "POST /api/register-token",
                "health_check": "GET /api/health"
            }
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    config = Config()
    
    logging.info("Push Notification Token Registration API を起動しています...")
    logging.info(f"デバッグモード: {config.FLASK_DEBUG}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.FLASK_DEBUG
    )