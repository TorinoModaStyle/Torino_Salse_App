# install: pandas openpyxl reportlab arabic-reshaper python-bidi pillow requests streamlit
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

# 1️⃣ دالة معالجة وتصحيح نصوص اللغة العربية لعناصر التقرير
def fix_arabic(text):
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if any("\u0600" <= char <= "\u06FF" for char in text):
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    return text

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
    
    # 🌟 2️⃣ تسجيل الخطوط المحلية المتوفرة في خوادم لينكس السحابية لضمان قراءة العربية وتنسيق الجدول
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
        df['السعر الأساسي الفعلي'] = df['اسم المادة'].map(base_price_map)
        df = df.dropna(subset=['السعر الأساسي الفعلي'])

        # 3️⃣ 📊 بناء جدول PDF منسق بمسافات واضحة وعرض متناسق وثابت
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []

        title_style_ar = ParagraphStyle('TitleAr', fontName=font_name, fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#1A365D'))
        title_style_en = ParagraphStyle('TitleEn', fontName='Helvetica-Bold', fontSize=13, leading=16, alignment=1, textColor=colors.HexColor('#718096'))
        cell_style_ar = ParagraphStyle('CellAr', fontName=font_name, fontSize=9, leading=12, alignment=2)
        cell_style_en = ParagraphStyle('CellEn', fontName='Helvetica', fontSize=9, leading=12, alignment=0)

        story.append(Paragraph(fix_arabic(report_title_ar), title_style_ar))
        story.append(Paragraph(report_title_en, title_style_en))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=10, spaceAfter=15))

        summary_df = df.groupby('اسم المادة').agg({'كمية المبيع': 'sum', 'سعر المبيع المحدث': 'max'}).reset_index()
        summary_df = summary_df.sort_values(by='كمية المبيع', ascending=False).head(20)

        headers = [
            Paragraph(fix_arabic("صورة المنتج"), cell_style_ar),
            Paragraph(fix_arabic("السعر المحدث"), cell_style_ar),
            Paragraph(fix_arabic("الكمية المباعة"), cell_style_ar),
            Paragraph(fix_arabic("اسم المادة"), cell_style_ar)
        ]
        table_data = [headers]

        for _, row in summary_df.iterrows():
            item_name = str(row['اسم المادة']).strip()
            img_flowable = Paragraph(fix_arabic("لا توجد صورة"), cell_style_ar)
            if item_name in extracted_photos:
                try:
                    img_data = io.BytesIO(extracted_photos[item_name])
                    img_flowable = Image(img_data, width=45, height=45)
                except:
                    pass

            row_cells = [
                img_flowable,
                Paragraph(f"{row['سعر المبيع المحدث']:,}", cell_style_en),
                Paragraph(f"{row['كمية المبيع']:,}", cell_style_en),
                Paragraph(fix_arabic(item_name), cell_style_ar)
            ]
            table_data.append(row_cells)

        # تحسين شكل عرض الجداول وتعيين أبعاد ثابتة يدويًا بشكل مخفي لضمان التنسيق الفخم ومظهر الشركات
        report_table = Table(table_data, colWidths=[80, 100, 100, 260])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        
        story.append(report_table)
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        pdf_bytes = buffer.getvalue()
        
        st.success("🎉 تم إنتاج ملف التقرير بنجاح ومواءمة الاتجاهات!")
        st.download_button(
            label="📥 تحميل التقرير التفاعلي المصور بصيغة PDF",
            data=pdf_bytes,
            file_name="Torino_Moda_Best_Seller_Report.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة الجداول البرمجية لـ PDF: {e}")
