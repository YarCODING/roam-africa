import io
import os
import qrcode

from django.conf import settings
from django.contrib.staticfiles import finders
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_REGULAR_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Inter_24pt-Regular.ttf')
FONT_BOLD_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Inter_24pt-Bold.ttf')
FONT_UNBOUNDED_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Unbounded-Bold.ttf')

font_main = 'Helvetica'
font_bold = 'Helvetica-Bold'
font_logo = 'Helvetica-Bold'

if os.path.exists(FONT_REGULAR_PATH):
    pdfmetrics.registerFont(TTFont('Inter', FONT_REGULAR_PATH))
    font_main = 'Inter'

if os.path.exists(FONT_BOLD_PATH):
    pdfmetrics.registerFont(TTFont('Inter-Bold', FONT_BOLD_PATH))
    font_bold = 'Inter-Bold'

if os.path.exists(FONT_UNBOUNDED_PATH):
    pdfmetrics.registerFont(TTFont('Unbounded-Bold', FONT_UNBOUNDED_PATH))
    font_logo = 'Unbounded-Bold'


COLOR_TEXT_MAIN = colors.HexColor('#1C1917')
COLOR_PRIMARY = colors.HexColor('#9E472A')
COLOR_SECONDARY = colors.HexColor('#2D4030')
COLOR_BG_HEADER = colors.HexColor('#F4EFEA')
COLOR_BORDER = colors.HexColor('#E7E5E4')
COLOR_MUTED = colors.HexColor('#78716C')


def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=0
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1C1917", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_booking_ticket_pdf(booking):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    story = []

    style_logo_title = ParagraphStyle('LogoTitle', fontName=font_logo, fontSize=15, leading=18, textColor=COLOR_PRIMARY)
    style_logo_sub = ParagraphStyle('LogoSub', fontName=font_main, fontSize=8, leading=10, textColor=COLOR_MUTED)

    style_ticket_num = ParagraphStyle('TicketNum', fontName=font_bold, fontSize=14, leading=16, alignment=2, textColor=COLOR_SECONDARY)
    style_ticket_status = ParagraphStyle('TicketStatus', fontName=font_bold, fontSize=9, leading=11, alignment=2, textColor=COLOR_PRIMARY)

    style_table_header = ParagraphStyle('TableHeader', fontName=font_bold, fontSize=10, leading=12, textColor=COLOR_SECONDARY)
    style_label = ParagraphStyle('Label', fontName=font_bold, fontSize=9, leading=12, textColor=COLOR_MUTED)
    style_value = ParagraphStyle('Value', fontName=font_main, fontSize=9, leading=12, textColor=COLOR_TEXT_MAIN)
    style_value_bold = ParagraphStyle('ValueBold', fontName=font_bold, fontSize=9, leading=12, textColor=COLOR_TEXT_MAIN)
    style_price = ParagraphStyle('Price', fontName=font_bold, fontSize=11, leading=13, textColor=COLOR_PRIMARY)

    style_note = ParagraphStyle('Note', fontName=font_main, fontSize=8, leading=11, textColor=COLOR_MUTED)

    logo_path = finders.find('images/logo.png')
    logo_img = Image(logo_path, width=1.5*cm, height=1.5*cm)

    brand_block = Table([[
        logo_img,
        [
            Paragraph("Roam Africa", style_logo_title),
            Paragraph("Туристичне агентство • Ваш провідник Африкою", style_logo_sub)
        ]
    ]], colWidths=[1.6*cm, 8.4*cm])
    brand_block.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))

    verify_url = f"{settings.BASE_URL}/bookings/{booking.id}/verify/"
    qr_img = Image(generate_qr_code(verify_url), width=2.2*cm, height=2.2*cm)

    ticket_info = [
        Paragraph(f"КВИТОК № {booking.id}", style_ticket_num),
        Paragraph(f"Статус: {booking.get_status_display()}", style_ticket_status)
    ]

    header_table = Table([[brand_block, ticket_info, qr_img]], colWidths=[10*cm, 5.5*cm, 2.5*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_PRIMARY, spaceBefore=0, spaceAfter=15))

    tour = booking.tour_date.tour
    tour_date = booking.tour_date

    tour_table_data = [
        [Paragraph("ДЕТАЛІ ТУРУ", style_table_header), ""],
        [Paragraph("Назва туру", style_label), Paragraph(tour.title, style_value_bold)],
        [Paragraph("Країна", style_label), Paragraph(tour.country.name if hasattr(tour, 'country') else "—", style_value)],
        [Paragraph("Дати поїздки", style_label), Paragraph(f"{tour_date.start_date.strftime('%d.%m.%Y')} — {tour_date.end_date.strftime('%d.%m.%Y')}", style_value_bold)],
        [Paragraph("Тривалість", style_label), Paragraph(f"{tour.duration_days} днів", style_value)],
        [Paragraph("Складність", style_label), Paragraph(tour.get_difficulty_display(), style_value)],
    ]

    table_tour = Table(tour_table_data, colWidths=[4.5*cm, 13.5*cm])
    table_tour.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_BG_HEADER),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(table_tour)
    story.append(Spacer(1, 0.8 * cm))

    booking_table_data = [
        [Paragraph("ІНФОРМАЦІЯ ПРО ЗАМОВЛЕННЯ", style_table_header), ""],
        [Paragraph("Замовник", style_label), Paragraph(booking.customer_name, style_value_bold)],
        [Paragraph("Телефон", style_label), Paragraph(booking.customer_phone, style_value)],
        [Paragraph("Email", style_label), Paragraph(booking.customer_email, style_value)],
        [Paragraph("Кількість осіб", style_label), Paragraph(f"{booking.persons_count} осіб", style_value)],
        [Paragraph("Загальна вартість", style_label), Paragraph(f"{booking.total_price}", style_price)],
    ]

    if booking.comment:
        booking_table_data.append([Paragraph("Коментар", style_label), Paragraph(booking.comment, style_value)])

    table_booking = Table(booking_table_data, colWidths=[4.5*cm, 13.5*cm])
    table_booking.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_BG_HEADER),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(table_booking)
    story.append(Spacer(1, 1.2 * cm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("<b>Важливо:</b> Пред'явіть цей квиток та документ, що посвідчує особу, під час реєстрації на тур.", style_note))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf