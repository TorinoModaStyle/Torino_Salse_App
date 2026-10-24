import streamlit as st
import pandas as pd
import os, zipfile, io, arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def fix_arabic(t):
    return get_display(arabic_reshaper.reshape(str(t)))

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#718096'))
    canvas.drawRightString(letter[0] - 36, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

st.set_page_config(page_title="Torino Moda", page_icon="👔", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A365D;'>Torino Moda Style</h1>", unsafe_allow_html=True)

# القائمة المنسدلة لجميع الفروع الخمسة
branch = st.selectbox("🌍 اختر فرع العملة المطلوب العمل عليه:", [
    "فرع الإمارات (درهم إماراتي AED)", 
    "فرع عُمان (ريال عُماني OMR)",
    "فرع السعودية (ريال سعودي SAR)",
    "فرع البحرين (دينار بحريني BHD)",
    "فرع تنزانيا (شلن تنزاني TZS)"
])

# ضبط الإعدادات البرمجية ديناميكياً لكل فرع وعملة بناءً على الشروط المحددة
if "عُمان" in branch:
    curr, tax_rate, discount = "OMR", 1.05, 2
elif "السعودية" in branch:
    curr, tax_rate, discount = "SAR", 1.15, 20
elif "البحرين" in branch:
    curr, tax_rate, discount = "BHD", 1.10, 2
elif "تنزانيا" in branch:
    curr, tax_rate, discount = "TZS", 1.00, 10000
else:
    curr, tax_rate, discount = "AED", 1.05, 20

file_in = st.file_uploader("1️⃣ رفع ملف المبيعات (products.xlsx):", type=["xlsx"])
zip_in = st.file_uploader("2️⃣ اختياري: رفع مجلد الصور (Photo.zip):", type=["zip"])

if file_in is not None:
    st.info("جاري معالجة البيانات...")
    font_name = 'Helvetica'
    if os.path.exists("segoeuireg.ttf"):
        try:
            pdfmetrics.registerFont(TTFont('SegoeArabic', "segoeuireg.ttf"))
            font_name = 'SegoeArabic'
        except: pass

    photos = {}
    if zip_in is not None:
        try:
            with zipfile.ZipFile(zip_in, 'r') as archive:
                for f_info in archive.infolist():
                    if not f_info.is_dir():
                        photos[os.path.splitext(os.path.basename(f_info.filename))[0].strip()] = archive.read(f_info.filename)
        except: pass

    try:
        df = pd.read_excel(file_in, usecols="A:J")
        cols = ['date', 'name', 'ret_qty', 'sale_qty', 'ret_prc', 'sale_prc', 'base_name', 'base_prc', 'stock_name', 'stock_qty']
        df.columns = cols
        df['date'] = pd.to_datetime(df['date'])
        
        t_ar = f"تقرير أفضل مبيع المصفى ({curr})"

        for c in ['ret_qty', 'sale_qty', 'sale_prc', 'ret_prc']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        # حساب السعر المحدث بالضرب في نسبة الضريبة الخاصة بكل فرع ثم التقريب لعدد صحيح
        df['s_mod'] = (df['sale_prc'] * tax_rate).round()
        df['r_mod'] = (df['ret_prc'] * tax_rate).round()

        b_map = df.dropna(subset=['base_name', 'base_prc']).drop_duplicates('base_name').set_index('base_name')['base_prc'].to_dict()
        s_map = df.dropna(subset=['stock_name', 'stock_qty']).drop_duplicates('stock_name').set_index('stock_name')['stock_qty'].to_dict()

        df['b_act'] = df['name'].map(b_map)
        df = df.dropna(subset=['b_act'])

        df['ok_s'] = df.apply(lambda r: r['sale_qty'] if r['s_mod'] >= (r['b_act'] - discount) else 0, axis=1)
        df['ok_r'] = df.apply(lambda r: r['ret_qty'] if r['r_mod'] >= (r['b_act'] - discount) else 0, axis=1)

        agg = df.groupby('name').agg({'ok_s': 'sum', 'ok_r': 'sum'}).reset_index()
        agg['net'] = agg['ok_s'] - agg['ok_r']
        agg['stock'] = agg['name'].map(s_map).fillna(0)
        top30 = agg.sort_values(by='net', ascending=False).head(30)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=40, bottomMargin=40)
        story = []
        
        title_s = ParagraphStyle('T1', fontName='Helvetica-Bold', fontSize=24, alignment=1, spaceAfter=10)
        sub_s = ParagraphStyle('T2', fontName=font_name, fontSize=11, alignment=1, spaceAfter=20, textColor=colors.HexColor('#D69E2E'))
        cell_s = ParagraphStyle('C1', fontName=font_name, fontSize=9, alignment=1)
        hd_s = ParagraphStyle('H1', fontName=font_name, fontSize=9, alignment=1, textColor=colors.white)

        story.append(Paragraph("Torino Moda Style", title_s))
        story.append(Paragraph(fix_arabic(t_ar), sub_s))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1A365D'), spaceAfter=15))

        hds = [Paragraph("Photo", hd_s), Paragraph("Item", hd_s), Paragraph(fix_arabic("الصافي"), hd_s), Paragraph(fix_arabic("الرصيد"), hd_s)]
        c_w = [int(w) for w in "50 85 65 60".split()]
        
        rows = []
        for _, r in top30.iterrows():
            nm = str(r['name']).strip()
            img = Image(io.BytesIO(photos[nm]), width=45, height=45) if nm in photos else Paragraph("", cell_s)
            
            # [تم الإصلاح] تعديل صياغة المعلمات لاسم النمط ليصبح style بدلاً من cell_style لمنع ظهور خطأ التوقف
            rows.append([
                img, 
                Paragraph(fix_arabic(nm), cell_s), 
                Paragraph(str(int(r['net'])), style=cell_s), 
                Paragraph(str(int(r['stock'])), style=cell_s)
            ])

        ts = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0'))])

        for i in range(0, len(rows), 16):
            p_items = rows[i:i+16]
            l_data = p_items[:8]
            r_data = p_items[8:]
            while len(l_data) < 8: l_data.append([Paragraph("", cell_s)] * 4)
            while len(r_data) < 8: r_data.append([Paragraph("", cell_s)] * 4)
            
            t_left = Table([hds] + l_data, colWidths=c_w)
            t_left.setStyle(ts)
            t_right = Table([hds] + r_data, colWidths=c_w)
            t_right.setStyle(ts)
            
            m_w = [int(w) for w in "260 20 260".split()]
            master_table = Table([[t_left, Paragraph("", cell_s), t_right]], colWidths=m_w)
            
            master_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 15)]))
            story.append(master_table)
            
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buf.seek(0)
        st.success("🎉 تم توليد تقرير فرع " + curr + " بنجاح!")
        st.download_button(label="📥 تحميل التقرير بصيغة PDF", data=buf, file_name=f"Report_{curr}.pdf", mime="application/pdf")
    except Exception as err:
        st.error(f"خطأ: {err}")
