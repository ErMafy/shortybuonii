from flask import Flask
from config import Config
from app.extensions import db, login_manager, mail


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.vouchers import vouchers_bp
    from app.routes.redeem import redeem_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vouchers_bp)
    app.register_blueprint(redeem_bp)

    # Create tables
    with app.app_context():
        from app.models import Admin, Store, Voucher  # noqa: F401
        db.create_all()

    return app
