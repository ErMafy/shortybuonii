import io
import qrcode
import base64
from flask import current_app


def generate_qr_code(redeem_token):
    """Generate QR code for a voucher redeem URL. Returns PNG bytes."""
    url = f"{current_app.config['APP_URL']}/redeem/{redeem_token}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()


def qr_to_base64(qr_bytes):
    """Convert QR code bytes to base64 string for embedding in HTML/PDF."""
    return base64.b64encode(qr_bytes).decode('utf-8')
