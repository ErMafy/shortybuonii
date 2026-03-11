import logging
import smtplib
import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from flask import current_app
from app.services.pdf_service import generate_voucher_pdf

logger = logging.getLogger(__name__)


def _build_email_body(voucher, store):
    return (
        f'Ciao {voucher.first_name},\n\n'
        f'Ecco il tuo Buono Regalo di {store.name}!\n\n'
        f'Importo: \u20ac {voucher.amount:.2f}\n'
        f'Codice: {voucher.voucher_code}\n'
        f'Scadenza: {voucher.expires_at.strftime("%d/%m/%Y")}\n\n'
        f'In allegato trovi il PDF del tuo voucher.\n'
        f'Presentalo in negozio al momento dell\'acquisto.\n\n'
        f'Grazie e a presto!\n'
        f'Shorty Shop'
    )


def _send_via_resend(voucher, store, pdf_bytes, api_key, from_email):
    """Send email via Resend HTTP API (works on Render free tier)."""
    subject = f'Il tuo Buono Regalo Shorty Shop - {store.name}'
    body = _build_email_body(voucher, store)

    payload = {
        'from': from_email,
        'to': [voucher.email],
        'subject': subject,
        'text': body,
        'attachments': [{
            'filename': f'voucher_{voucher.voucher_code}.pdf',
            'content': base64.b64encode(pdf_bytes).decode('utf-8'),
        }],
    }

    data = json.dumps(payload).encode('utf-8')
    req = Request(
        'https://api.resend.com/emails',
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        resp = urlopen(req, timeout=15)
        result = json.loads(resp.read())
        logger.info(f'Resend email sent for {voucher.voucher_code}: {result}')
        return True, None
    except HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        logger.error(f'Resend API error {e.code}: {err_body}')
        return False, f'Resend API error {e.code}: {err_body}'


def _send_via_smtp(voucher, store, pdf_bytes, cfg):
    """Send email via SMTP (works locally, blocked on Render free tier)."""
    smtp_user = cfg.get('MAIL_USERNAME', '')
    smtp_pass = cfg.get('MAIL_PASSWORD', '')
    smtp_server = cfg.get('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = cfg.get('MAIL_PORT', 465)
    use_tls = cfg.get('MAIL_USE_TLS', False)
    use_ssl = cfg.get('MAIL_USE_SSL', True)
    timeout = cfg.get('MAIL_TIMEOUT', 15)

    if not smtp_user or not smtp_pass:
        return False, 'Credenziali SMTP non configurate'

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = voucher.email
    msg['Subject'] = f'Il tuo Buono Regalo Shorty Shop - {store.name}'
    msg.attach(MIMEText(_build_email_body(voucher, store), 'plain', 'utf-8'))

    pdf_part = MIMEApplication(pdf_bytes, _subtype='pdf')
    pdf_part.add_header('Content-Disposition', 'attachment',
                        filename=f'voucher_{voucher.voucher_code}.pdf')
    msg.attach(pdf_part)

    if smtp_port == 465 or use_ssl:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout)
    else:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
        if use_tls:
            server.starttls()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    server.quit()
    return True, None


def send_voucher_email(voucher, store):
    """Send voucher PDF via email. Uses Resend API if configured, else SMTP."""
    if not voucher.email:
        return False, 'Nessun indirizzo email fornito'

    try:
        cfg = current_app.config
        pdf_bytes = generate_voucher_pdf(voucher, store)

        # Prefer Resend API (works on Render)
        resend_key = cfg.get('RESEND_API_KEY', '')
        if resend_key:
            from_email = cfg.get('RESEND_FROM', 'Shorty Shop <onboarding@resend.dev>')
            success, err = _send_via_resend(voucher, store, pdf_bytes, resend_key, from_email)
            if success:
                return True, None
            logger.warning(f'Resend failed, trying SMTP: {err}')

        # Fallback to SMTP
        return _send_via_smtp(voucher, store, pdf_bytes, cfg)

    except smtplib.SMTPAuthenticationError:
        err = 'Autenticazione SMTP fallita.'
        logger.error(f'Email auth failed for {voucher.voucher_code}: {err}')
        return False, err
    except (TimeoutError, OSError) as e:
        err = f'Connessione email fallita: {e}'
        logger.error(f'Email connection failed for {voucher.voucher_code}: {e}')
        return False, err
    except Exception as e:
        logger.error(f'Email send failed for voucher {voucher.voucher_code}: {e}')
        return False, str(e)
