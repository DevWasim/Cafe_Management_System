import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cafe.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Auto-logout after 24 hours
    
    # For production, also enable:
    # SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS (enable in production)
    
    # CSRF Protection
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire (better UX)
    WTF_CSRF_ENABLED = True  # Enable CSRF protection
