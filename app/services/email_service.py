import logging
from flask import current_app
from flask_mail import Message
from app.extensions import mail
from app.services.pdf_service import generate_voucher_pdf

logger = logging.getLogger(__name__)


def send_voucher_email(voucher, store):
    """Send voucher PDF via email. Returns (success: bool, error_message: str | None)."""
    if not voucher.email:
        return False, 'Nessun indirizzo email fornito'

    try:
        subject = f'Il tuo Buono Regalo Shorty Shop - {store.name}'
        body = (
            f'Ciao {voucher.first_name},\n\n'
            f'Ecco il tuo Buono Regalo di {store.name}!\n\n'
            f'Importo: € {voucher.amount:.2f}\n'
            f'Codice: {voucher.voucher_code}\n'
            f'Scadenza: {voucher.expires_at.strftime("%d/%m/%Y")}\n\n'
            f'In allegato trovi il PDF del tuo voucher.\n'
            f'Presentalo in negozio al momento dell\'acquisto.\n\n'
            f'Grazie e a presto!\n'
            f'Shorty Shop'
        )

        msg = Message(
            subject=subject,
            recipients=[voucher.email],
            body=body,
        )

        # Generate and attach PDF
        pdf_bytes = generate_voucher_pdf(voucher, store)
        msg.attach(
            filename=f'voucher_{voucher.voucher_code}.pdf',
            content_type='application/pdf',
            data=pdf_bytes,
        )

        mail.send(msg)
        logger.info(f'Email sent for voucher {voucher.voucher_code} to {voucher.email}')
        return True, None

    except Exception as e:
        logger.error(f'Email send failed for voucher {voucher.voucher_code}: {e}')
        return False, str(e)
