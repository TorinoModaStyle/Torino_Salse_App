# install: pandas openpyxl reportlab arabic-reshaper python-bidi pillow
import streamlit as st
import pandas as pd
import os
import zipfile
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

def fix_arabic(text):
    if not isinstance(text, str):
        text = str(text)
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#718096'))
    page_num = canvas.getPageNumber()
    page_width, page_height = letter
    canvas.drawRightString(page_width - 36, 20, f"Page {page_num}")
    canvas.restoreState()

st.set_page_config(page_title="Torino Moda Style - Analytics", page_icon="👔", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A365D;'>Torino Moda Style</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #D69E2E;'>نظام تحليل المبيعات الذكي وتوليد التقارير المصورة تلقائياً</h4>", unsafe_allow_html=True)
st.write("---")

uploaded_file = st.file_uploader("1️⃣ قم برفع ملف المبيعات (products.xlsx):", type=["xlsx"])
uploaded_zip = st.file_uploader("2️⃣ اختياري: قم برفع مجلد الصور مضغوطاً بصيغة (Photo.zip) لإظهار صور المنتجات:", type=["zip"])

if uploaded_file is not None:
    st.info("جاري معالجة البيانات وتوليد التقرير السحابي القياسي... برجاء الانتظار ثواني")
    
    # محاولة قراءة الخط العربي الافتراضي المتوفر في خوادم لينكس لحل مشكلة المربعات للأبد
    font_name = 'Helvetica'
    for possible_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/X11/TTF/DejaVuSans.ttf"
    ]:
        if os.path.exists(possible_path):
            try:
                pdfmetrics.registerFont(TTFont('CloudArabic', possible_path))
                font_name = 'CloudArabic'
                break
            except:
                pass

    extracted_photos = {}
    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip, 'r') as archive:
                for file_info in archive.infolist():
                    if not file_info.is_dir():
                        filename = os.path.basename(file_info.filename)
                        name_without_ext, _ = os.path.splitext(filename)
                        extracted_photos[name_without_ext.strip()] = archive.read(file_info.filename)
        except Exception as e:
            st.warning(f"تنبيه: فشل قراءة ملف الصور المضغوط: {e}")

    try:
        df = pd.read_excel(uploaded_file, usecols="A:J")
        df.columns = ['تاريخ الفاتورة', 'اسم المادة', 'كمية المرتجع', 'كمية المبيع', 
                      'سعر المرتجع', 'سعر المبيع', 'اسم المادة الأساسي', 'السعر الأساسي',
                      'مادة الرصيد', 'رصيد المادة']
        
        df['تاريخ الفاتورة'] = pd.to_datetime(df['تاريخ الفاتورة'])
        min_date = df['تاريخ الفاتورة'].min()
        max_date = df['تاريخ الفاتورة'].max()
        months_diff = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month)
        if max_date.day >= min_date.day: months_diff += 1
        if months_diff <= 0: months_diff = 1
        
        if months_diff >= 12:
            report_title_ar, report_title_en = "تقرير أفضل مبيع السنوي المصفى", "Top Selling Performance Report - Annual"
        elif months_diff == 1:
            report_title_ar, report_title_en = "تقرير أفضل مبيع لشهر واحد المصفى", "Top Selling Performance Report - 1 Month"
        else:
            report_title_ar, report_title_en = f"تقرير أفضل مبيع آخر {months_diff} شهور المصفى", f"Top Selling Performance Report - Last {months_diff} Months"

        df['كمية المبيع'] = pd.to_numeric(df['كمية المبيع'], errors='coerce').fillna(0)
        df['كمية المرتجع'] = pd.to_numeric(df['كمية المرتجع'], errors='coerce').fillna(0)
        df['سعر المبيع'] = pd.to_numeric(df['سعر المبيع'], errors='coerce').fillna(0)
        df['سعر المرتجع'] = pd.to_numeric(df['سعر المرتجع'], errors='coerce').fillna(0)

        df['سعر المبيع المحدث'] = (df['سعر المبيع'] * 1.05).round()
        df['سعر المرتجع المحدث'] = (df['سعر المرتجع'] * 1.05).round()

        base_price_map = df.dropna(subset=['اسم المادة الأساسي', 'السعر الأساسي']).drop_duplicates(subset=['اسم المادة الأساسي']).set_index('اسم المادة الأساسي')['السعر الأساسي'].to_dict()
        stock_map = df.dropna(subset=['مادة الرصيد', 'رصيد المادة']).drop_duplicates(subset=['مادة الرصيد']).set_index('مادة الرصيد')['رصيد المادة'].to_dict()

        df['السعر الأساسي الفعلي'] = df['اسم المادة'].map(base_price_map)
        df = df.dropna(subset=['السعر الأساسي الفعلي'])

        df['مبيع_مقبول'] = df.apply(lambda r: r['كمية المبيع'] if r['سعر المبيع المحدث'] >= (r['السعر الأساسي الفعلي'] - 20) else 0, axis=1)
        df['مرتجع_مقبول'] = df.apply(lambda r: r['كمية المرتجع'] if r['سعر المرتجع المحدث'] >= (r['السعر الأساسي الفعلي'] - 20) else 0, axis=1)

        agg_df = df.groupby('اسم المادة').agg({'مبيع_مقبول': 'sum', 'مرتجع_مقبول': 'sum'}).reset_index()
        agg_df['صافي المبيعات'] = agg_df['مبيع_مقبول'] - agg_df['مرتجع_مقبول']
        agg_df['السعر الأساسي'] = agg_df['اسم المادة'].map(base_price_map)
        agg_df['رصيد المادة'] = agg_df['اسم المادة'].map(stock_map).fillna(0)

        top_30 = agg_df.sort_values(by='صافي المبيعات', ascending=False).head(30)

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=40, bottomMargin=40)
        story = []
        
        title_style = ParagraphStyle('CompTitle', fontName='Helvetica-Bold', fontSize=26, leading=32, alignment=1, spaceAfter=12, textColor=colors.HexColor('#1A365D'))
        subtitle_style = ParagraphStyle('SubTitle', fontName=font_name, fontSize=11, leading=15, alignment=1, spaceAfter=25, textColor=colors.HexColor('#D69E2E'))
        section_style = ParagraphStyle('SecTitle', fontName=font_name, fontSize=13, alignment=1, spaceBefore=5, spaceAfter=15, textColor=colors.HexColor('#2B6CB0'))
        cell_style = ParagraphStyle('Cell', fontName=font_name, fontSize=9, leading=12, alignment=1)
        header_style = ParagraphStyle('HeaderCell', fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1, textColor=colors.white)

        story.append(Paragraph("Torino Moda Style", title_style))
        story.append(Paragraph(f"{fix_arabic(report_title_ar)} / {report_title_en}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1A365D'), spaceAfter=15))
        story.append(Paragraph(fix_arabic("قائمة أفضل 30 مادة مع الصور والرصيد الحالي (Top 30 Net Performance, Stock & Photos)"), section_style))

        # ترويسة الجدول المعدل بدون الأعمدة الثلاثة الملغاة
        summary_headers = [
            Paragraph("Photo", header_style),
            Paragraph("Item", header_style),
            Paragraph(f"{fix_arabic('صافي المبيعات')}<br/><font size='7'>(Net Sales)</font>", header_style),
            Paragraph(f"{fix_arabic('الرصيد الحالي')}<br/><font size='7'>(Current Stock)</font>", header_style)
        ]
        
        # أبعاد العرض لكل عمود في النصف الواحد من الصفحة
        col_widths = [55, 95, 60, 60]
        
        all_rows_data = []
        for idx, row in top_30.iterrows():
            mat_name = str(row['اسم المادة']).strip()
            img_flowable = Paragraph("", cell_style)
            
            if mat_name in extracted_photos:
                try:
                    img_data = io.BytesIO(extracted_photos[mat_name])
                    img_flowable = Image(img_data, width=45, height=45)
                except:
                    pass
            
            row_cells = [
                img_flowable,
                Paragraph(fix_arabic(mat_name), cell_style),
                Paragraph(str(int(row['صافي المبيعات'])), cell_style),
                Paragraph(str(int(row['رصيد المادة'])), cell_style)
            ]
            all_rows_data.append(row_cells)

        # تقسيم الجدول تلقائياً لعمودين منفصلين متجاورين بحد أقصى 8 عناصر لكل صفحة في الجانب الواحد
        rows_per_page_side = 8
        total_items = len(all_rows_data)
        
        for i in range(0, total_items, rows_per_page_side * 2):
            page_items = all_rows_data[i:i + (rows_per_page_side * 2)]
            
            left_side_data = page_items[:rows_per_page_side]
            right_side_data = page_items[rows_per_page_side:]
            
            # النصف الأيسر
            left_table_content = [summary_headers] + left_side_data
            left_table = Table(left_table_content, colWidths=col_widths)
            left_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            # النصف الأيمن
            if right_side_data:
                right_table_content = [summary_headers] + right_side_data
                right_table = Table(right_table_content, colWidths=col_widths)
                right_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
