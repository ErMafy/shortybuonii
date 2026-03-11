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

    # Email — accepts all common env var name variants
    MAIL_SERVER = os.environ.get('MAIL_SERVER', os.environ.get('EMAIL_SERVER', 'smtp.gmail.com'))
    MAIL_PORT = int(os.environ.get('MAIL_PORT', os.environ.get('EMAIL_PORT', 465)))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', os.environ.get('EMAIL_USE_TLS', '0')).lower() in ('1', 'true', 'yes')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', '1').lower() in ('1', 'true', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', os.environ.get('EMAIL_USER', ''))
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', os.environ.get('MAIL_PASS', os.environ.get('EMAIL_PASS', '')))
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', os.environ.get('EMAIL_USER', '')))
    MAIL_TIMEOUT = 10

    # Resend API (works on Render free tier where SMTP is blocked)
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    RESEND_FROM = os.environ.get('RESEND_FROM', 'Shorty Shop <onboarding@resend.dev>')

    # App
    APP_NAME = os.environ.get('APP_NAME', 'Shorty Shop Voucher Manager')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
