from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.voucher import Voucher
from app.models.store import Store
from app.services.qr_service import generate_qr_code, qr_to_base64
from app.services.pdf_service import generate_voucher_pdf
from app.services.email_service import send_voucher_email
from datetime import datetime, timezone
import io

vouchers_bp = Blueprint('vouchers', __name__)


@vouchers_bp.route('/vouchers')
@login_required
def voucher_list():
    # Query params for filtering
    search = request.args.get('search', '').strip()
    store_filter = request.args.get('store', '')
    status_filter = request.args.get('status', '')

    query = Voucher.query

    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                Voucher.first_name.ilike(like),
                Voucher.last_name.ilike(like),
                Voucher.voucher_code.ilike(like),
                Voucher.email.ilike(like),
            )
        )

    if store_filter:
        query = query.filter_by(store_id=int(store_filter))

    now = datetime.now(timezone.utc)

    if status_filter == 'active':
        query = query.filter(Voucher.status == 'active', Voucher.expires_at > now)
    elif status_filter == 'used':
        query = query.filter(Voucher.status == 'used')
    elif status_filter == 'expired':
        query = query.filter(Voucher.status == 'active', Voucher.expires_at <= now)

    vouchers = query.order_by(Voucher.created_at.desc()).all()
    stores = Store.query.order_by(Store.name).all()

    return render_template('vouchers.html',
                           vouchers=vouchers,
                           stores=stores,
                           search=search,
                           store_filter=store_filter,
                           status_filter=status_filter)


@vouchers_bp.route('/vouchers/new', methods=['GET', 'POST'])
@login_required
def voucher_new():
    stores = Store.query.order_by(Store.name).all()

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        store_id = request.form.get('store_id', '')
        amount = request.form.get('amount', '')
        expires_at = request.form.get('expires_at', '')
        notes = request.form.get('notes', '').strip() or None
        send_email = request.form.get('send_email') == '1'

        # Validation
        errors = []
        if not first_name:
            errors.append('Il nome è obbligatorio.')
        if not last_name:
            errors.append('Il cognome è obbligatorio.')
        if not store_id:
            errors.append('Seleziona un negozio.')
        if not amount:
            errors.append('L\'importo è obbligatorio.')
        if not expires_at:
            errors.append('La data di scadenza è obbligatoria.')

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                errors.append('L\'importo deve essere maggiore di zero.')
        except (ValueError, TypeError):
            errors.append('Importo non valido.')
            amount_val = 0

        try:
            expires_dt = datetime.strptime(expires_at, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            errors.append('Data di scadenza non valida.')
            expires_dt = None

        store = Store.query.get(int(store_id)) if store_id.isdigit() else None
        if not store:
            errors.append('Negozio non trovato.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('voucher_new.html', stores=stores)

        # Create voucher
        voucher = Voucher(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            voucher_code=Voucher.generate_voucher_code(store.prefix),
            redeem_token=Voucher.generate_redeem_token(),
            amount=amount_val,
            store_id=store.id,
            expires_at=expires_dt,
            notes=notes,
            created_by_admin_id=current_user.id,
        )
        db.session.add(voucher)
        db.session.commit()

        # Send email if requested
        email_msg = ''
        if send_email and voucher.email:
            success, err = send_voucher_email(voucher, store)
            if success:
                email_msg = 'Email inviata con successo.'
            else:
                email_msg = f'Voucher creato ma invio email fallito: {err}'
                flash(email_msg, 'warning')

        flash(f'Voucher {voucher.voucher_code} creato con successo! {email_msg}', 'success')
        return redirect(url_for('vouchers.voucher_detail', voucher_code=voucher.voucher_code))

    return render_template('voucher_new.html', stores=stores)


@vouchers_bp.route('/voucher/<voucher_code>')
@login_required
def voucher_detail(voucher_code):
    voucher = Voucher.query.filter_by(voucher_code=voucher_code).first_or_404()
    store = Store.query.get(voucher.store_id)

    qr_bytes = generate_qr_code(voucher.redeem_token)
    qr_b64 = qr_to_base64(qr_bytes)

    return render_template('voucher_detail.html',
                           voucher=voucher,
                           store=store,
                           qr_b64=qr_b64)


@vouchers_bp.route('/voucher/<voucher_code>/pdf')
@login_required
def voucher_pdf(voucher_code):
    voucher = Voucher.query.filter_by(voucher_code=voucher_code).first_or_404()
    store = Store.query.get(voucher.store_id)

    pdf_bytes = generate_voucher_pdf(voucher, store)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'voucher_{voucher.voucher_code}.pdf',
    )


@vouchers_bp.route('/voucher/<voucher_code>/send-email', methods=['POST'])
@login_required
def voucher_send_email(voucher_code):
    voucher = Voucher.query.filter_by(voucher_code=voucher_code).first_or_404()
    store = Store.query.get(voucher.store_id)

    if not voucher.email:
        flash('Nessun indirizzo email associato a questo voucher.', 'error')
        return redirect(url_for('vouchers.voucher_detail', voucher_code=voucher_code))

    success, err = send_voucher_email(voucher, store)
    if success:
        flash('Email inviata con successo!', 'success')
    else:
        flash(f'Invio email fallito: {err}', 'error')

    return redirect(url_for('vouchers.voucher_detail', voucher_code=voucher_code))
