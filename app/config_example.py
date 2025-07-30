import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # ==================== NUOVE CONFIGURAZIONI JWT COOKIES ====================
    # Supporta sia headers che cookies
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    
    # Configurazioni Cookie httpOnly
    JWT_COOKIE_SECURE = False          # True in produzione con HTTPS
    JWT_COOKIE_CSRF_PROTECT = False    # False per semplicità iniziale
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_DOMAIN = None           # None = stesso dominio
    JWT_COOKIE_PATH = '/'              # Disponibile su tutto il sito
    
    # Opzionale: Cookie per refresh token
    JWT_REFRESH_COOKIE_NAME = 'refresh_token_cookie'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL')
        
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}