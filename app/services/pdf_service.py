import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from app.services.qr_service import generate_qr_code


def generate_voucher_pdf(voucher, store):
    """Generate a professional PDF voucher. Returns PDF bytes."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    brand_color = HexColor('#1a1a2e')
    accent_color = HexColor('#e94560')
    light_gray = HexColor('#f5f5f5')

    title_style = ParagraphStyle(
        'VoucherTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=brand_color,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )

    subtitle_style = ParagraphStyle(
        'VoucherSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=10 * mm,
    )

    heading_style = ParagraphStyle(
        'VoucherHeading',
        parent=styles['Normal'],
        fontSize=12,
        textColor=brand_color,
        fontName='Helvetica-Bold',
        spaceAfter=3 * mm,
    )

    value_style = ParagraphStyle(
        'VoucherValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#333333'),
        spaceAfter=2 * mm,
    )

    amount_style = ParagraphStyle(
        'VoucherAmount',
        parent=styles['Title'],
        fontSize=36,
        textColor=accent_color,
        alignment=TA_CENTER,
        spaceAfter=8 * mm,
        fontName='Helvetica-Bold',
    )

    code_style = ParagraphStyle(
        'VoucherCode',
        parent=styles['Normal'],
        fontSize=18,
        textColor=brand_color,
        alignment=TA_CENTER,
        fontName='Courier-Bold',
        spaceAfter=6 * mm,
    )

    footer_style = ParagraphStyle(
        'VoucherFooter',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#999999'),
        alignment=TA_CENTER,
        spaceAfter=2 * mm,
    )

    elements = []

    # Header
    elements.append(Paragraph('SHORTY SHOP', title_style))
    elements.append(Paragraph(f'{store.name}', subtitle_style))
    elements.append(Spacer(1, 4 * mm))

    # Divider line
    divider_data = [['', '', '']]
    divider_table = Table(divider_data, colWidths=[doc.width])
    divider_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1, accent_color),
    ]))
    elements.append(divider_table)
    elements.append(Spacer(1, 8 * mm))

    # BUONO REGALO title
    elements.append(Paragraph('BUONO REGALO', ParagraphStyle(
        'GiftTitle', parent=styles['Normal'], fontSize=16,
        textColor=HexColor('#666666'), alignment=TA_CENTER,
        spaceAfter=4 * mm, fontName='Helvetica',
    )))

    # Amount
    amount_str = f'\u20ac {voucher.amount:.2f}'
    elements.append(Paragraph(amount_str, amount_style))
    elements.append(Spacer(1, 4 * mm))

    # Voucher Code
    elements.append(Paragraph(f'Codice: {voucher.voucher_code}', code_style))
    elements.append(Spacer(1, 6 * mm))

    # QR Code
    qr_bytes = generate_qr_code(voucher.redeem_token)
    qr_image = Image(io.BytesIO(qr_bytes), width=45 * mm, height=45 * mm)
    qr_table = Table([[qr_image]], colWidths=[doc.width])
    qr_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    elements.append(qr_table)
    elements.append(Spacer(1, 8 * mm))

    # Client info
    elements.append(Paragraph('Intestato a:', heading_style))
    elements.append(Paragraph(f'{voucher.first_name} {voucher.last_name}', value_style))
    elements.append(Spacer(1, 4 * mm))

    # Details table
    created_str = voucher.created_at.strftime('%d/%m/%Y') if voucher.created_at else '-'
    expires_str = voucher.expires_at.strftime('%d/%m/%Y') if voucher.expires_at else '-'

    detail_data = [
        ['Negozio:', store.name],
        ['Data Emissione:', created_str],
        ['Data Scadenza:', expires_str],
    ]
    detail_table = Table(detail_data, colWidths=[4.5 * cm, 10 * cm])
    detail_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), brand_color),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#dddddd')),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 10 * mm))

    # Divider
    elements.append(divider_table)
    elements.append(Spacer(1, 6 * mm))

    # Conditions
    elements.append(Paragraph('Condizioni d\'uso:', ParagraphStyle(
        'CondTitle', parent=styles['Normal'], fontSize=9,
        textColor=brand_color, fontName='Helvetica-Bold',
        spaceAfter=2 * mm,
    )))

    conditions = [
        'Questo buono regalo \u00e8 valido fino alla data di scadenza indicata.',
        'Il buono pu\u00f2 essere utilizzato una sola volta.',
        'Non \u00e8 convertibile in denaro e non \u00e8 cedibile.',
        'Valido esclusivamente presso il negozio indicato.',
        'Presentare questo voucher al momento dell\'acquisto.',
    ]
    for c in conditions:
        elements.append(Paragraph(f'\u2022 {c}', ParagraphStyle(
            'Condition', parent=styles['Normal'], fontSize=8,
            textColor=HexColor('#777777'), spaceAfter=1 * mm, leftIndent=5 * mm,
        )))

    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph('Shorty Shop \u2014 Il tuo stile, la tua scelta.', footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
