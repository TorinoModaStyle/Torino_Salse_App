import streamlit as st
import pandas as pd
import numpy as np
import os, zipfile, io, arabic_reshaper
from bidi.algorithm import get_display

# مكتبات الـ PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# إعدادات الصفحة الأساسية لتطبيق المبيعات
st.set_page_config(
    page_title="Torino Moda Style - Analytics",
    page_icon="📊",
    layout="centered"
)

# دالة إصلاح اللغة العربية في التقارير
def fix_arabic(t):
    return get_display(arabic_reshaper.reshape(str(t)))

# دالة إضافة أرقام الصفحات للـ PDF
def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#718096'))
    page_width, page_height = letter
    canvas.drawRightString(page_width - 36, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

# ----------------------------------------------------
# بقية كود المبيعات وعرض الجداول والبيانات تبدأ من هنا مباشرة...
# ----------------------------------------------------

# عرض اللوغو بخلفيته البيضاء داخل إطار مستطيل متناسق لواجهة المبيعات
col_sales_logo1, col_sales_logo2, col_sales_logo3 = st.columns([1, 2, 1])
with col_sales_logo2:
    if os.path.exists("logo.jpg"):
        import base64
        with open("logo.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        # نفس الإطار المستطيل الأبيض المحمي والمحتوي بالكامل على الشعار لتوحيد الواجهتين
        st.markdown(
            f'<div style="text-align: center; display: flex; justify-content: center; align-items: center; background-color: #FFFFFF; width: 100%; max-width: 420px; height: 160px; margin: 0 auto; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); overflow: hidden;">'
            f'<img src="data:image/jpeg;base64,{encoded_string}" style="width: 90%; height: 90%; object-fit: contain;">'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ يرجى التأكد من تسمية ملف اللوغو logo.jpg ووضعه في المجلد الرئيسي")

st.markdown("<h1 style='text-align: center; color: #1A365D; margin-top: 15px;'>Torino Moda Style</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #D69E2E;'>نظام تحليل المبيعات الذكي وتوليد التقارير المصورة تلقائياً</h4>", unsafe_allow_html=True)

st.write("---")

branch = st.selectbox("🌍 اختر فرع العملة المطلوب العمل عليه:", [
    "فرع الإمارات (درهم إماراتي AED)", 
    "فرع عُمان (ريال عُماني OMR)",
    "فرع السعودية (ريال سعودي SAR)",
    "فرع البحرين (دينار بحريني BHD)",
    "فرع تنزانيا (شلن تنزاني TZS)",
    "فرع الكويت (دينار كويتي KWD)"
])

if "عُمان" in branch:
    curr, tax_rate, discount = "OMR", 1.05, 2
    country_ar, country_en = "سلطنة عُمان", "Sultanate of Oman"
elif "السعودية" in branch:
    curr, tax_rate, discount = "SAR", 1.15, 20
    country_ar, country_en = "المملكة العربية السعودية", "Kingdom of Saudi Arabia"
elif "البحرين" in branch:
    curr, tax_rate, discount = "BHD", 1.10, 2
    country_ar, country_en = "مملكة البحرين", "Kingdom of Bahrain"
elif "تنزانيا" in branch:
    curr, tax_rate, discount = "TZS", 1.00, 10000
    country_ar, country_en = "جمهورية تنزانيا الاتحادية", "United Republic of Tanzania"
elif "الكويت" in branch:
    curr, tax_rate, discount = "KWD", 1.00, 2
    country_ar, country_en = "دولة الكويت", "State of Kuwait"
else:
    curr, tax_rate, discount = "AED", 1.05, 20
    country_ar, country_en = "دولة الإمارات العربية المتحدة", "United Arab Emirates"

uploaded_file = st.file_uploader("1️⃣ رفع ملف المبيعات (products.xlsx):", type=["xlsx"])
uploaded_zip = st.file_uploader("2️⃣ اختياري: رفع مجلد الصور (Photo.zip):", type=["zip"])

if uploaded_file is not None:
    st.info("جاري معالجة البيانات وتوليد التقرير... برجاء الانتظار ثواني")
    font_name = 'Helvetica'
    if os.path.exists("segoeuireg.ttf"):
        try:
            pdfmetrics.registerFont(TTFont('SegoeArabic', "segoeuireg.ttf"))
            font_name = 'SegoeArabic'
        except: pass

    photos = {}
    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip, 'r') as archive:
                for file_info in archive.infolist():
                    if not file_info.is_dir():
                        filename = os.path.basename(file_info.filename)
                        name_without_ext, _ = os.path.splitext(filename)
                        photos[name_without_ext.strip()] = archive.read(file_info.filename)
        except: pass

    df = pd.read_excel(uploaded_file, usecols="A:J")
    c1, c2, c3, c4, c5 = 'col1', 'col2', 'col3', 'col4', 'col5'
    c6, c7, r_c8, c9, c10 = 'col6', 'col7', 'col8', 'col9', 'col10'
    df.columns = [c1, c2, c3, c4, c5, c6, c7, r_c8, c9, c10]
    df[c1] = pd.to_datetime(df[c1])
    
    min_date, max_date = df[c1].min(), df[c1].max()
    months_diff = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month)
    if max_date.day >= min_date.day: months_diff += 1
    if months_diff <= 0: months_diff = 1
    
    if months_diff >= 12:
        report_title_ar = f"تقرير أفضل مبيع السنوي المصفى - {country_ar}"
        report_title_en = f"Top Selling Performance Report - Annual ({country_en})"
    elif months_diff == 1:
        report_title_ar = f"تقرير أفضل مبيع لشهر واحد المصفى - {country_ar}"
        report_title_en = f"Top Selling Performance Report - 1 Month ({country_en})"
    else:
        report_title_ar = f"تقرير أفضل مبيع آخر {months_diff} شهور المصفى - {country_ar}"
        report_title_en = f"Top Selling Performance Report - Last {months_diff} Months ({country_en})"

    for col in [c3, c4, c6, c5]:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if curr == "OMR":
        df['سعر المبيع المحدث'] = (df[c6] * tax_rate * 2).round() / 2
        df['سعر المرتجع المحدث'] = (df[c5] * tax_rate * 2).round() / 2
    elif curr in ["BHD", "KWD"]:
        df['سعر المبيع المحدث'] = (df[c6] * tax_rate).round(1)
        df['سعر المرتجع المحدث'] = (df[c5] * tax_rate).round(1)
    else:
        df['سعر المبيع المحدث'] = (df[c6] * tax_rate).round()
        df['سعر المرتجع المحدث'] = (df[c5] * tax_rate).round()

    base_price_map = df.dropna(subset=[c7, r_c8]).drop_duplicates(subset=[c7]).set_index(c7)[r_c8].to_dict()
    stock_map = df.dropna(subset=[c9, c10]).drop_duplicates(subset=[c9]).set_index(c9)[c10].to_dict()

    df['السعر الأساسي الفعلي'] = df[c2].map(base_price_map)
    df = df.dropna(subset=['السعر الأساسي الفعلي'])

    df['مبيع_مقبول'] = df.apply(lambda r: r[c4] if r['سعر المبيع المحدث'] >= (r['السعر الأساسي الفعلي'] - discount) else 0, axis=1)
    df['مرتجع_مقبول'] = df.apply(lambda r: r[c3] if r['سعر المرتجع المحدث'] >= (r['السعر الأساسي الفعلي'] - discount) else 0, axis=1)

    agg_df = df.groupby(c2).agg({'مبيع_مقبول': 'sum', 'مرتجع_مقبول': 'sum'}).reset_index()
    agg_df['صافي المبيعات'] = agg_df['مبيع_مقبول'] - agg_df['مرتجع_مقبول']
    agg_df['رصيد المادة'] = agg_df[c2].map(stock_map).fillna(0)

    top_30 = agg_df.sort_values(by='صافي المبيعات', ascending=False).head(30)

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=25, bottomMargin=25)
    story = []
    
    title_s = ParagraphStyle('CompTitle', fontName='Helvetica-Bold', fontSize=24, leading=28, alignment=1, spaceAfter=6, textColor=colors.HexColor('#1A365D'))
    sub_s = ParagraphStyle('SubTitle', fontName=font_name, fontSize=10, leading=14, alignment=1, spaceAfter=12, textColor=colors.HexColor('#D69E2E'))
    section_s = ParagraphStyle('SecTitle', fontName=font_name, fontSize=11, alignment=1, spaceBefore=2, spaceAfter=8, textColor=colors.HexColor('#2B6CB0'))
    cell_s = ParagraphStyle('Cell', fontName=font_name, fontSize=9, leading=12, alignment=1)
    hd_s = ParagraphStyle('HeaderCell', fontName=font_name, fontSize=9, leading=11, alignment=1, textColor=colors.white)

    story.append(Paragraph("Torino Moda Style", title_s))
    story.append(Paragraph(f"{fix_arabic(report_title_ar)} / {report_title_en}", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A365D'), spaceAfter=10))
    story.append(Paragraph(fix_arabic("قائمة أفضل 30 مادة مع الصور والرصيد الحالي (Top 30 Net Performance, Stock & Photos)"), section_s))

    hds = [
        Paragraph(f"{fix_arabic('الصورة')}<br/><font size='7'>(Photo)</font>", hd_s), 
        Paragraph(f"{fix_arabic('المادة')}<br/><font size='7'>(Item)</font>", hd_s), 
        Paragraph(f"{fix_arabic('إجمالي الصافي')}<br/><font size='7'>(Net Sales)</font>", hd_s), 
        Paragraph(f"{fix_arabic('الرصيد الحالي')}<br/><font size='7'>(Current Stock)</font>", hd_s)
    ]
    
    col_widths = [int(w) for w in "50 85 65 60".split()]
    
    rows = []
    for idx, row in top_30.iterrows():
        mat_name = str(row[c2]).strip()
        img = Image(io.BytesIO(photos[mat_name]), width=48, height=48) if mat_name in photos else Paragraph("", cell_s)
        rows.append([
            img, 
            Paragraph(fix_arabic(mat_name), cell_s), 
            Paragraph(str(int(row['صافي المبيعات'])), style=cell_s), 
            Paragraph(str(int(row['رصيد المادة'])), style=cell_s)
        ])

    ts = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), 
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8)
    ])

    for i in range(0, len(rows), 16):
        p_items = rows[i:i+16]
        l_data = p_items[:8]
        r_data = p_items[8:]
        
        if len(l_data) > 0 or len(r_data) > 0:
            t_left = Table([hds] + l_data, colWidths=col_widths) if len(l_data) > 0 else Paragraph("", cell_s)
            if len(l_data) > 0: t_left.setStyle(ts)
            
            t_right = Table([hds] + r_data, colWidths=col_widths) if len(r_data) > 0 else Paragraph("", cell_s)
            if len(r_data) > 0: t_right.setStyle(ts)
            
            master_widths = [int(w) for w in "260 20 260".split()]
            master_table = Table([[t_left, Paragraph("", cell_s), t_right]], colWidths=master_widths)
            
            master_style = TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 10)])
            master_table.setStyle(master_style)
            story.append(master_table)
        
    # [تم الإصلاح الحاسم] تم استعادة أمر بناء التقرير وإغلاق تدفق بايتات مستند الـ PDF بنجاح ليعرضه المتصفح فوراً وبأعلى جودة
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    pdf_buffer.seek(0)
    
    st.success(f"🎉 تم توليد تقرير {country_ar} بنجاح ومطابق تماماً للنظام المحاسبي!")
    st.download_button(label="📥 تحميل التقرير بصيغة PDF", data=pdf_buffer, file_name=f"Report_{curr}.pdf", mime="application/pdf")
