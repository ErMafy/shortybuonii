from datetime import datetime, timezone
from app.extensions import db


class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    voucher_amount_default = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    vouchers = db.relationship('Voucher', backref='store', lazy='dynamic')

    @property
    def prefix(self):
        prefixes = {
            'uomo': 'SSU',
            'woman': 'SSW',
            'intimissimi': 'SSI',
        }
        return prefixes.get(self.slug, 'SSX')

    def __repr__(self):
        return f'<Store {self.name}>'
