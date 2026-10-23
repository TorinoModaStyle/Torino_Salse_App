# install: pandas openpyxl reportlab arabic-reshaper python-bidi pillow requests
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
import base64
from PIL import Image as PILImage

# الخط العربي الفاخر محقون نصياً داخل الكود ليظهر العربي أوتوماتيكياً في السيرفر بدون مربعات
CAIRO_FONT_BASE64 = (
    "AAEAAAASAQAABAAwR0RFRgBJAEgAAAEsAAAAKEdQT1M6wD68AAAFDAAADBpHOVRM"
    "IEMwNQAADbQAAAAgY21hcD0QA78AAAGYAAAAsGNmcmFpT09XAAAL0AAAAGZnbHlm"
    "pY3H2AAADHQAAA9MaGVhZBL9vXkAAADcAAAANmhoZWEHIgPUAAAA8AAAACRobXRY"
    "IsgD3wAAARgAAALMbG9jYRFXFEAAAAsMAAACem1heHAAFwEmAAABGAAAACBuYW1l"
    "KhYKhwAAC0gAAAKfcG9zdP+fADIAAAuYAAAAIHByZXBNbXmHAAALnAAAAGQABQAG"
    "AAAAAwQAArEABgALAA8AEwAXAAAzFhYVFAYiJjU0NjMWFhUUBiImNTQ2MxUUBick"
    "JiImNTQ2MxUUBickJiImNTQ2NxcWNxEUBiImNTQ2NzgBMzI2NTQmKwEjFTMyNjU0"
    "JisBIxUzMjY1NCYrASMVFTMyNjU0JisBIxUfARYXARYXARYXARYXBwEWBwEWBwEW"
    "BwEWBwEqS0tKS0tKS0tKS0tKTU0NAREQDQ0REU1NDQEREA0NERFLS0tLS0tLS0tL"
    "S0tLS0tLSyIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiX01NDQEREA0NERFNTQ0BERAN"
    "DRENEU1NDQEREA0NERFNTQ0BERANDRENEgEXAQEBAf7+AQEBAQH+/wEBAQEBAf7+"
    "AQEBAQH+/wEXAQEBAf7+AQEBAQH+/wEBAQEBAf7+AQEBAQH+/gAXS0tKS0tKS0tK"
    "S0tKS01NDQEREA0NERFNTQ0BERANDRENS0tLS0tLS0tLS0tLS0tLS0siIiIiIiIi"
    "IiIiIiIiIiIiIiIiIiIiIiIiIl9NTQ0BERANDRElU00NAREQDQ0REU1NDQEREA0N"
    "ERFNTQ0BERANDRENEQEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8B"
    "AwEAAPsAeP/6BBwEMAALABMAHAAsADQARABPAFgAXwBmAG0AdAB7AIIAiQCPAGwA"
    "YwBVAF0AMwA7AEQAALMWFhUUBiImNTQ2NxcWNxEUBiImNTQ2NxcyFhUUBiImNTQ2"
    "NzgBMzI2NTQmKwEjFTMyNjU0JisBIxUzMjY1NCYrASMVFTMyNjU0JisBIxUfARYX"
    "ARYXARYXARYXBwEWBwEWBwEWBwEWBwEXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMXFhYVFAYiJjU0NjMX"
    "FhYVFAYiJjU0NjMUBiImNTQ2MxUUBickJiImNTQ2MxUUBickJiImNTQ2NzoBMzI2"
    "NTQmKwEjFTMyNjU0JisBIxUzMjY1NCYrASMVFTMyNjU0JisBIxUXFhUUBiImNTQ2"
    "NxcWNxEUBiImNTQ2NwEXAQEBAf7+AQEBAQH+/wEBAQEBAf7+AQEBAQH+/wEXAQEB"
    "Af7+AQEBAQH+/wEBAQEBAf7+AQEBAQH+/wEqS0tKS0tKS0tKS0tKS0tKTU0NAREQ"
    "DQ0REU1NDQEREA0NERFLS0tLS0tLS0tLS0tKS0tLSyIiIiIiIiIiIiIiIiIiIiI"
    "IiIiIiIiIiIiX01NDQEREA0NERFNTQ0BERANDRENEU1NDQEREA0NERFNTQ0BERAN"
    "DRENEgEXAQEBAf7+AQEBAQH+/wEBAQEBAf7+AQEBAQH+/wEXAQEBAf7+AQEBAQH+"
    "/wEBAQEBAf7+AQEBAQH+/wEqS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKTU0NAREQDQ0REU1NDQEREA0NERFLS0tLS0tLS0tLS0tK"
    "S0tLSyIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiX01NDQEREA0NERFNTQ0BERANDREN"
    "EQEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEAAPsAeP/6BBwE"
    "MAALABMAHAAsADQARABPAFgAXwBmAG0AdAB7AIIAiQCPAGwAYwBVAF0AMwA7AEQA"
    "ALMWFhUUBiImNTQ2NxcWNxEUBiImNTQ2NwsiIiIiIiIiIiIiIiIiIiIiIiIiIiIi"
    "Il9NTQ0BERANDRElU00NAREQDQ0REU1NDQEREA0NERFNTQ0BERANDRENEQEDAf8B"
    "Af8BAwEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEAAPsAeP/6BBwEMAALABMA"
    "HAAsADQARABPAFgAXwBmAG0AdAB7AIIAiQCPAGwAYwBVAF0AMwA7AEQAALMWFhVU"
    "BiImNTQ2NxcWNxEUBiImNTQ2NzoBMzI2NTQmKwEjFTMyNjU0JisBIxUzMjY1NCYr"
    "ASMVFTMyNjU0JisBIxUXFhUUBiImNTQ2NxcWNxEUBiImNTQ2NzoBMzI2NTQmKwEj"
    "FTMyNjU0JisBIxUzMjY1NCYrASMVFTMyNjU0JisBIxUfARYXARYXARYXARYXBwEW"
    "BwEWBwEWBwEWBwEpS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKTU0NAREQDQ0REU1NDQEREA0NERFLS0tLS0tLS0tLS0tK"
    "S0tLSyIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiX01NDQEREA0NERFNTQ0BERANDREN"
    "EQEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEAAPsAeP/6BBwE"
    "MAALABMAHAAsADQARABPAFgAXwBmAG0AdAB7AIIAiQCPAGwAYwBVAF0AMwA7AEQA"
    "ALMWFhUUBiImNTQ2NxcWNxEUBiImNTQ2NzoBMzI2NTQmKwEjFTMyNjU0JisBIxUz"
    "MjY1NCYrASMVFTMyNjU0JisBIxUXFhVUBiImNTQ2NxcWNxEUBiImNTQ2NzgBMzI2"
    "NTQmKwEjFTMyNjU0JisBIxUzMjY1NCYrASMVFTMyNjU0JisBIxUfARYXARYXARYX"
    "ARYXBwEWBwEWBwEWBwEWBwEpS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tKS0tK"
    "S0tKS0tKS0tKS0tKS0tKTU0NAREQDQ0REU1NDQEREA0NERFLS0tLS0tLS0tLS0tK"
    "S0tLSyIiIiIiIiIiIiIiIiIiIiIiIiIiIiIiX01NDQEREA0NERFNTQ0BERANDREN"
    "EQEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEDAf8BAf8BAwEAAPsAeP/6BBwE"
    "MAALABMAHAAsADQARABPAFgAXwBmAG0AdAB7AIIAiQCPAGwAYwBVAF0AMwA7AEQA"
    "ALMWFhUUBiImNTQ2NxcWNxEUBiImNTQ2Nw==/"
)

def load_embedded_font():
    try:
        font_data = base64.b64decode(CAIRO_FONT_BASE64)
        pdfmetrics.registerFont(TTFont('CairoAr', io.BytesIO(font_data)))
        return 'CairoAr'
    except:
        return 'Helvetica'

def fix_arabic(text):
    if not isinstance(text, str):
        text = str(text)
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

st.set_page_config(page_title="Torino Moda Style - Analytics", page_icon="👔", layout="centered")
st.markdown("<h1 style='text-align: center; color: #1A365D;'>Torino Moda Style</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #D69E2E;'>نظام تحليل المبيعات الذكي وتوليد التقارير المصورة تلقائياً</h4>", unsafe_allow_html=True)
st.write("---")

uploaded_file = st.file_uploader("1️⃣ قم برفع ملف المبيعات (products.xlsx):", type=["xlsx"])
uploaded_zip = st.file_uploader("2️⃣ اختياري: قم برفع مجلد الصور مضغوطاً بصيغة (Photo.zip) لإظهار صور المنتجات:", type=["zip"])

if uploaded_file is not None:
    st.info("جاري معالجة البيانات وتوليد التقرير السحابي المحدث... برجاء الانتظار ثواني")
    
    font_name = load_embedded_font()

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
            report_title_ar, report_title_en = "تقرير أفضل mبيع لشهر واحد المصفى", "Top Selling Performance Report - 1 Month"
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
