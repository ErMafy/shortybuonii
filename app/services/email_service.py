import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask import current_app
from app.services.pdf_service import generate_voucher_pdf

logger = logging.getLogger(__name__)


def send_voucher_email(voucher, store):
    """Send voucher PDF via email using smtplib with timeout. Returns (success, error)."""
    if not voucher.email:
        return False, 'Nessun indirizzo email fornito'

    try:
        cfg = current_app.config
        smtp_user = cfg.get('MAIL_USERNAME', '')
        smtp_pass = cfg.get('MAIL_PASSWORD', '')
        smtp_server = cfg.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = cfg.get('MAIL_PORT', 465)
        use_tls = cfg.get('MAIL_USE_TLS', False)
        use_ssl = cfg.get('MAIL_USE_SSL', True)
        timeout = cfg.get('MAIL_TIMEOUT', 15)

        if not smtp_user or not smtp_pass:
            return False, 'Credenziali email non configurate'

        # Build message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = voucher.email
        msg['Subject'] = f'Il tuo Buono Regalo Shorty Shop - {store.name}'

        body = (
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
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Attach PDF
        pdf_bytes = generate_voucher_pdf(voucher, store)
        pdf_part = MIMEApplication(pdf_bytes, _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment',
                            filename=f'voucher_{voucher.voucher_code}.pdf')
        msg.attach(pdf_part)

        # Send with timeout — use SSL (port 465) or STARTTLS (port 587)
        if smtp_port == 465 or use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
            if use_tls:
                server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()

        logger.info(f'Email sent for voucher {voucher.voucher_code} to {voucher.email}')
        return True, None

    except smtplib.SMTPAuthenticationError:
        err = 'Autenticazione SMTP fallita. Controlla EMAIL_USER e EMAIL_PASS.'
        logger.error(f'Email auth failed for {voucher.voucher_code}: {err}')
        return False, err
    except TimeoutError:
        err = 'Timeout connessione al server email.'
        logger.error(f'Email timeout for {voucher.voucher_code}')
        return False, err
    except Exception as e:
        logger.error(f'Email send failed for voucher {voucher.voucher_code}: {e}')
        return False, str(e)
