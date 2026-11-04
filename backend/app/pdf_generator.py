import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

# Регистрируем шрифт DejaVu
FONT_PATH = r"D:\projects\estimate-generator\backend\app\DejaVuSans.ttf"

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
    print(f"✓ Шрифт DejaVu загружен: {FONT_PATH}")
else:
    print(f"⚠ Шрифт не найден: {FONT_PATH}")

def generate_pdf(business, estimate):
    items_data = json.loads(estimate.items_data) if isinstance(estimate.items_data, str) else estimate.items_data
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    estimate_id_short = str(estimate.id)[:8] if estimate.id else "N/A"
    
    os.makedirs("output", exist_ok=True)
    path = f"output/estimate_{estimate.id}.pdf"
    
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='DejaVuNormal', fontName='DejaVu', fontSize=11, leading=14))
    styles.add(ParagraphStyle(name='DejaVuBold', fontName='DejaVu', fontSize=11, leading=14))
    styles.add(ParagraphStyle(name='DejaVuLarge', fontName='DejaVu', fontSize=16, leading=20))
    styles.add(ParagraphStyle(name='DejaVuHuge', fontName='DejaVu', fontSize=24, leading=30))
    styles.add(ParagraphStyle(name='DejaVuSmall', fontName='DejaVu', fontSize=9, leading=12))
    styles.add(ParagraphStyle(name='DejaVuTotal', fontName='DejaVu', fontSize=14, leading=18, textColor=colors.white))
    styles.add(ParagraphStyle(name='DejaVuTotalRight', fontName='DejaVu', fontSize=14, leading=18, textColor=colors.white, alignment=TA_RIGHT))
    
    elements = []
    
    # Заголовок
    business_name = Paragraph(f"<b>{business.name}</b>", styles['DejaVuHuge'])
    elements.append(business_name)
    
    if business.phone:
        phone = Paragraph(f"Тел: {business.phone}", styles['DejaVuSmall'])
        elements.append(phone)
        elements.append(Spacer(1, 5*mm))
    
    elements.append(Spacer(1, 5*mm))
    
    # Дата и время
    date_text = Paragraph(f"Дата и время создания: {now}", styles['DejaVuSmall'])
    date_text.hAlign = TA_RIGHT
    elements.append(date_text)
    elements.append(Spacer(1, 5*mm))
    
    # Информация о клиенте + Объект работ
    client_info = [
        [Paragraph(f"<b>Клиент:</b> {estimate.client_name}", styles['DejaVuNormal'])],
        [Paragraph(f"<b>Телефон:</b> {estimate.client_phone or 'Не указан'}", styles['DejaVuNormal'])],
    ]
    
    # ← ДОБАВЛЯЕМ ОБЪЕКТ РАБОТ (только если заполнен)
    if estimate.work_object:
        client_info.append([Paragraph(f"<b>Объект работ:</b> {estimate.work_object}", styles['DejaVuNormal'])])
    
    client_info.append([Paragraph(f"<b>Номер сметы:</b> #{estimate_id_short}", styles['DejaVuNormal'])])
    
    client_table = Table(client_info, colWidths=[120*mm])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LINEABOVE', (0, 0), (0, -1), 4, colors.HexColor('#2563eb')),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 8*mm))
    
    # Заголовок таблицы
    elements.append(Paragraph("<b>Перечень услуг</b>", styles['DejaVuLarge']))
    elements.append(Spacer(1, 5*mm))
    
    # Таблица услуг
    table_data = [[
        Paragraph('<b>Наименование</b>', styles['DejaVuNormal']),
        Paragraph('<b>Кол-во</b>', styles['DejaVuNormal']),
        Paragraph('<b>Цена</b>', styles['DejaVuNormal']),
        Paragraph('<b>Сумма</b>', styles['DejaVuNormal'])
    ]]
    
    for idx, item in enumerate(items_data, 1):
        qty_int = int(float(item['qty']))
        table_data.append([
            Paragraph(f"{idx}. {item['name']}", styles['DejaVuNormal']),
            str(qty_int),
            f"{item['price']:.2f} ₽",
            f"{item['subtotal']:.2f} ₽"
        ])
    
    # Итоговая строка
    table_data.append([
        '',
        '',
        Paragraph('ИТОГО: ', styles['DejaVuTotal']),
        Paragraph(f'{estimate.total:.2f} ₽', styles['DejaVuTotalRight'])
    ])
    
    table = Table(table_data, colWidths=[70*mm, 20*mm, 30*mm, 35*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        ('FONTNAME', (0, 1), (-1, -2), 'DejaVu'),
        ('FONTSIZE', (0, 1), (-1, -2), 11),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 8),
        ('TOPPADDING', (0, 1), (-1, -2), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#ffffff')),
        ('BACKGROUND', (0, 2), (-1, -2), colors.HexColor('#f8fafc')),
        
        ('WORDWRAP', (0, 1), (0, -2), 'CJK'),
        
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('ALIGN', (2, -1), (3, -1), 'RIGHT'),
        
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#1e40af')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15*mm))
    
    # Подписи
    sig_table = Table([
        ['Подпись исполнителя', 'Подпись клиента'],
        ['___________________', '___________________']
    ], colWidths=[70*mm, 70*mm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(sig_table)
    
    elements.append(Spacer(1, 15*mm))
    
    # Футер
    footer = Paragraph("Смета действительна в течение 14 дней с даты составления.<br/>Документ сформирован автоматически системой &quot;Генератор смет&quot;", styles['DejaVuSmall'])
    footer.hAlign = TA_RIGHT
    elements.append(footer)
    
    doc.build(elements)
    
    return path