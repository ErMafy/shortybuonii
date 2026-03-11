from flask import Blueprint, render_template
from flask_login import login_required
from app.models.voucher import Voucher
from app.models.store import Store
from datetime import datetime, timezone

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    now = datetime.now(timezone.utc)

    total = Voucher.query.count()
    used = Voucher.query.filter_by(status='used').count()

    # Active: status == 'active' and not expired
    active = Voucher.query.filter(
        Voucher.status == 'active',
        Voucher.expires_at > now
    ).count()

    # Expired: status == 'active' but past expiration
    expired = Voucher.query.filter(
        Voucher.status == 'active',
        Voucher.expires_at <= now
    ).count()

    stores = Store.query.all()
    store_stats = []
    for store in stores:
        store_total = Voucher.query.filter_by(store_id=store.id).count()
        store_active = Voucher.query.filter(
            Voucher.store_id == store.id,
            Voucher.status == 'active',
            Voucher.expires_at > now
        ).count()
        store_used = Voucher.query.filter(
            Voucher.store_id == store.id,
            Voucher.status == 'used',
        ).count()
        store_stats.append({
            'name': store.name,
            'slug': store.slug,
            'total': store_total,
            'active': store_active,
            'used': store_used,
        })

    return render_template('dashboard.html',
                           total=total,
                           active=active,
                           used=used,
                           expired=expired,
                           store_stats=store_stats)
