from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.voucher import Voucher
from datetime import datetime, timezone

redeem_bp = Blueprint('redeem', __name__)


@redeem_bp.route('/redeem/<redeem_token>')
@login_required
def redeem_page(redeem_token):
    voucher = Voucher.query.filter_by(redeem_token=redeem_token).first()

    if not voucher:
        return render_template('redeem.html', voucher=None, status='not_found')

    status = voucher.effective_status
    store = voucher.store

    return render_template('redeem.html',
                           voucher=voucher,
                           store=store,
                           status=status)


@redeem_bp.route('/redeem/<redeem_token>/confirm', methods=['POST'])
@login_required
def redeem_confirm(redeem_token):
    voucher = Voucher.query.filter_by(redeem_token=redeem_token).first()

    if not voucher:
        flash('Voucher non trovato.', 'error')
        return redirect(url_for('vouchers.voucher_list'))

    # Double-check server-side
    if voucher.status == 'used':
        flash('Questo voucher è già stato utilizzato.', 'error')
        return redirect(url_for('redeem.redeem_page', redeem_token=redeem_token))

    if voucher.is_expired:
        flash('Questo voucher è scaduto.', 'error')
        return redirect(url_for('redeem.redeem_page', redeem_token=redeem_token))

    # Mark as used
    voucher.status = 'used'
    voucher.used_at = datetime.now(timezone.utc)
    voucher.used_by_admin_id = current_user.id
    db.session.commit()

    flash(f'Voucher {voucher.voucher_code} segnato come utilizzato!', 'success')
    return redirect(url_for('redeem.redeem_page', redeem_token=redeem_token))


@redeem_bp.route('/verify', methods=['GET', 'POST'])
@login_required
def verify_manual():
    if request.method == 'POST':
        code = request.form.get('voucher_code', '').strip().upper()
        if not code:
            flash('Inserisci un codice voucher.', 'error')
            return render_template('verify.html')

        voucher = Voucher.query.filter_by(voucher_code=code).first()
        if not voucher:
            flash('Voucher non trovato.', 'error')
            return render_template('verify.html', search_code=code)

        return redirect(url_for('redeem.redeem_page', redeem_token=voucher.redeem_token))

    return render_template('verify.html')
