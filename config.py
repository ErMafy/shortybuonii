import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # Render uses postgres:// but SQLAlchemy requires postgresql://
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///shorty.db')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER = os.environ.get('EMAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '1') == '1'
    MAIL_USERNAME = os.environ.get('EMAIL_USER', '')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS', '')
    MAIL_DEFAULT_SENDER = os.environ.get('EMAIL_USER', '')

    # App
    APP_NAME = os.environ.get('APP_NAME', 'Shorty Shop Voucher Manager')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
