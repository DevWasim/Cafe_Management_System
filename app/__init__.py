from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

# Initialize CSRF Protection
csrf = CSRFProtect()

# Initialize Rate Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Logging Configuration
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Lumina Cafe Startup')
    
    # Even in debug, log to file for system logs view
    if app.debug:
         if not os.path.exists('logs'):
            os.mkdir('logs')
         file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
         file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
         file_handler.setLevel(logging.INFO)
         app.logger.addHandler(file_handler)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Enable CSRF Protection globally
    csrf.init_app(app)
    
    # Enable Rate Limiting
    limiter.init_app(app)

    from app.routes import main
    from app.admin import admin
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix='/admin')

    @app.context_processor
    def inject_cafe_settings():
        from app.models import CafeSetting
        setting = CafeSetting.query.first()
        # Create default if missing (handled in admin route but good safety here too, or just return None safe)
        if not setting:
            return dict(cafe_settings=None) 
        return dict(cafe_settings=setting)

    return app
