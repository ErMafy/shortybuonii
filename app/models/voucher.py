import secrets
import string
from datetime import datetime, timezone
from app.extensions import db


class Voucher(db.Model):
    __tablename__ = 'vouchers'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    voucher_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    redeem_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, used, expired
    notes = db.Column(db.Text, nullable=True)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
    used_by_admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)

    created_by = db.relationship('Admin', foreign_keys=[created_by_admin_id], backref='created_vouchers')
    used_by = db.relationship('Admin', foreign_keys=[used_by_admin_id], backref='redeemed_vouchers')

    @property
    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    @property
    def effective_status(self):
        if self.status == 'used':
            return 'used'
        if self.is_expired:
            return 'expired'
        return 'active'

    @staticmethod
    def generate_voucher_code(store_prefix):
        chars = string.ascii_uppercase + string.digits
        while True:
            code = store_prefix + '-' + ''.join(secrets.choice(chars) for _ in range(6))
            if not Voucher.query.filter_by(voucher_code=code).first():
                return code

    @staticmethod
    def generate_redeem_token():
        while True:
            token = secrets.token_urlsafe(32)
            if not Voucher.query.filter_by(redeem_token=token).first():
                return token

    def __repr__(self):
        return f'<Voucher {self.voucher_code}>'
