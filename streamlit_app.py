import streamlit as st
import pandas as pd
import numpy as np
import os, zipfile, io, arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==========================================
# 1. نظام إدارة الجلسة والتحقق من الموظفين
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

def check_login(username, password):
    if username == "Aeman" and password == "Aeman2002":
        st.session_state.logged_in = True
        st.session_state.user_role = "sales"
        st.rerun()
    elif username == "Majd" and password == "Majd1995":
        st.session_state.logged_in = True
        st.session_state.user_role = "inventory"
        st.rerun()
    else:
        st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

def fix_arabic(t):
    return get_display(arabic_reshaper.reshape(str(t)))

def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#718096'))
    page_width, page_height = letter
    canvas.drawRightString(page_width - 36, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()

st.set_page_config(page_title="Torino Moda Style - Analytics", page_icon="👔", layout="centered")

# ==========================================
# 2. واجهة تسجيل الدخول وحظر الوصول
# ==========================================
if not st.session_state.logged_in:
    st.subheader("تسجيل الدخول للنظام")
    user_input = st.text_input("اسم المستخدم")
    pass_input = st.text_input("كلمة المرور", type="password")
    
    if st.button("دخول"):
        check_login(user_input, pass_input)
    st.stop()

# ==========================================
# 3. توجيه الموظفين حسب الصلاحية
# ==========================================
if st.session_state.user_role == "inventory":
    st.markdown("<h1 style='text-align: center; color: #1B2A47;'>Torino Moda Style</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #E1A73E;'>📦 نظام جرد البضاعة والمطابقة</h3>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("قم برفع ملف جرد النظام المحاسبي (Excel)", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df_inventory = pd.read_excel(uploaded_file)
            st.success("تم رفع ملف الجرد بنجاح!")
                        # أ. إنشاء مخزن ذكي صامت لحفظ الباركودات الممسوحة وعددها الفعلي
            import json
            # جلب البيانات المخزنة واكتشاف التحديثات الحية للموظف الآخر تلقائياً
            if os.path.exists("jard_backup.json"):
                try:
                    with open("jard_backup.json", "r") as f:
                        st.session_state.scanned_barcodes = json.load(f)
                except:
                    if "scanned_barcodes" not in st.session_state:
                        st.session_state.scanned_barcodes = {}
            else:
                if "scanned_barcodes" not in st.session_state:
                    st.session_state.scanned_barcodes = {}
                    
            if "jard_completed" not in st.session_state:
                st.session_state.jard_completed = False

            # ب. دالة مطورة ومسرعة تحفظ نسخة احتياطية فورية ضد انقطاع الإنترنت
            # ب. دالة مطورة ومسرعة تدمج وتزامن قراءات الموظفين معاً حياً بدون تداخل
            def process_and_clear():
                raw_barcode = st.session_state.barcode_scan_key or st.session_state.barcode_manual_key
                if raw_barcode:
                    barcode = str(raw_barcode).strip()
                    b_len = len(barcode)
                    
                    if b_len in [6, 8, 10]:
                        b_code = barcode[0:6]
                        b_color = "Black"
                        b_size = "0"
                        
                        if b_len >= 8:
                            b_color = color_mapping.get(barcode[6:8], "رمز لون غير معروف")
                        if b_len == 10:
                            b_size = barcode[8:10]
                            if b_size.startswith("0") and len(b_size) > 1:
                                b_size = b_size[1:]
                        
                        # قراءة آخر ما مسحه الموظف الآخر من السيرفر قبل الإضافة لمنع التداخل
                        current_scans = {}
                        if os.path.exists("jard_backup.json"):
                            try:
                                with open("jard_backup.json", "r") as f:
                                    current_scans = json.load(f)
                            except:
                                current_scans = st.session_state.scanned_barcodes
                        else:
                            current_scans = st.session_state.scanned_barcodes
                        
                        # دمج القطعة الجديدة مع القائمة المشتركة الحية
                        if barcode in current_scans:
                            current_scans[barcode]["qty"] += 1
                        else:
                            current_scans[barcode] = {
                                "code": b_code, "color": b_color, "size": b_size, "qty": 1
                            }
                        
                        # تحديث الذاكرة المحلية والملف الاحتياطي فوراً ليراه الموظف الآخر
                        st.session_state.scanned_barcodes = current_scans
                        with open("jard_backup.json", "w") as f:
                            json.dump(current_scans, f)
                            
                st.session_state.barcode_scan_key = ""
                st.session_state.barcode_manual_key = ""

            # ج. خيار احتياطي لتفعيل كاميرا الهاتف كقارئ باركود حي ومباشر
            enable_camera = st.checkbox("📸 تفعيل كاميرا الجوال كقارئ باركود احتياطي")
            
            if enable_camera:
                from streamlit_qrcode_scanner import qrcode_scanner
                scanned_code = qrcode_scanner(key="live_barcode_scanner")
                
                if scanned_code:
                    barcode = str(scanned_code).strip()
                    st.success(f"🎯 تم التقاط باركود حي بنجاح: {barcode}")
                    
                    b_len = len(barcode)
                    if b_len in [6, 8, 10]:
                        b_code = barcode[0:6]
                        b_color = "Black"
                        b_size = "0"
                        
                        if b_len >= 8:
                            b_color = "Black"
                        if b_len == 10:
                            b_size = barcode[8:10]
                            if b_size.startswith("0") and len(b_size) > 1:
                                b_size = b_size[1:]
                                
                    if barcode in st.session_state.scanned_barcodes:
                        st.session_state.scanned_barcodes[barcode]["qty"] += 1
                    else:
                        st.session_state.scanned_barcodes[barcode] = {
                            "code": b_code, "color": b_color, "size": b_size, "qty": 1
                        }
                    
                    # حفظ نسخة صلبة فورية لحماية بضاعة الكاميرا ضد انقطاع الشبكة والتعليق
                    with open("jard_backup.json", "w") as f:
                        json.dump(st.session_state.scanned_barcodes, f)

            # ج. خانات الإدخال المحدثة والمربوطة بالتصفير الفوري التلقائي (on_change)
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("🤖 مسح تلقائي (ضع المؤشر هنا واستخدم القارئ):", key="barcode_scan_key", on_change=process_and_clear)
            with col2:
                st.text_input("✍️ إدخال يدوي (اكتب الباركود واضغط Enter):", key="barcode_manual_key", on_change=process_and_clear)

            # د. معالجة وتوليد الجدول المتكامل المكون من 9 أعمدة كاملة
            # نقوم ببناء قائمة البيانات الجديدة لمطابقتها وعرضها
            jard_data = []
            
            # قاموس رموز الألوان للترجمة العكسية أثناء بناء الجدول
            color_mapping = {
                "01": "Black", "02": "Silver", "03": "Gold", "04": "Beige", "05": "Navy",
                "06": "Gray", "07": "Red", "08": "Blue", "09": "Fuchia", "10": "White",
                "11": "Champagne", "12": "Brown", "13": "Camel", "14": "Green", "15": "Orange",
                "16": "Phosphoric", "17": "Light golden", "18": "Khaki", "19": "Maroon", "20": "Bronze",
                "21": "Pink", "22": "Purple", "23": "Light Beige", "24": "OLIVE", "25": "Yellow",
                "26": "Rainbow", "27": "Platinum", "28": "Dark Brown", "29": "Copper", "30": "Bronette",
                "31": "Espresso", "32": "Red Brown", "33": "Off White", "34": "Coffee", "35": "Dark Green",
                "36": "Nude", "37": "Tan", "38": "Pewter", "39": "Light Green", "40": "MUD",
                "41": "Light Gray", "42": "Apricot", "43": "Dark Pink", "44": "Light Black", "45": "Army Green",
                "46": "Cream", "47": "Peach", "48": "F.Green", "49": "CORAL", "50": "Dark Navy",
                "51": "Dark Grey", "52": "L.Blue", "53": "Rose Gold", "54": "Wine", "55": "Dark Gold",
                "56": "Sky Blue", "57": "Light Purple", "58": "Antique Gold", "59": "Antique Silver", "60": "Cuticolor",
                "61": "D-Black", "62": "D-Coffee", "63": "D-Maroon", "64": "D-Purple", "65": "L-Brown",
                "66": "L-Pink", "67": "L-Yellow", "68": "Silvery Grey", "69": "Turquoise", "70": "Yellow Brown",
                "71": "Stone", "72": "S.BLACK", "73": "D.Red", "74": "Black/White", "75": "Almond",
                "76": "K-serpentine", "77": "D.Beige", "78": "D.Pink", "79": "TIFFANY", "80": "L.KHAKI",
                "81": "D.KHAKI", "82": "GUN", "83": "multicolour", "84": "WHITE/BLACK", "85": "BLACK/CAMEL",
                "86": "CAMEL/BLACK", "87": "WHITE/CAMEL", "88": "D- BLUE", "89": "GRNNY", "90": "LEOPARD",
                "91": "L.GREY", "92": "L.COFFEE", "93": "COLOURFULL", "94": "TIGER", "95": "ZEBRA"
            }

            # تتبع المواد الأصلية التي تم فحصها من الإكسل
            matched_indices = set()
            
            # 1. المرور أولاً على ملف الإكسل الأصلي وبناء المقارنات والأعمدة (A إلى I)
            for idx, row in df_inventory.iterrows():
                orig_code = str(row["كود المنتج"]).strip()
                orig_color = str(row["اللون"]).strip()
                orig_size = str(row["القياس"]).strip()
                if orig_size.endswith(".0"):
                    orig_size = orig_size[:-2]
                orig_qty = int(row["الكمية"]) if not pd.isna(row["الكمية"]) else 0
                
                # جلب الكمية الممسوحة فوراً وبسرعة فائقة من المخزن المطور
                scanned_qty = 0
                for barcode, info in st.session_state.scanned_barcodes.items():
                    b_len = len(barcode)
                    b_code = info["code"]
                    b_color = info["color"]
                    b_size = info["size"]
                    
                    is_match = False
                    if b_len == 6 and b_code == orig_code:
                        is_match = True
                    elif b_len == 8 and b_code == orig_code and b_color.lower() == orig_color.lower():
                        is_match = True
                    elif b_len == 10 and b_code == orig_code and b_color.lower() == orig_color.lower() and b_size == orig_size:
                        is_match = True
                        
                    if is_match:
                        scanned_qty += info["qty"]
                        matched_indices.add(barcode)
                
                diff = scanned_qty - orig_qty
                jard_data.append({
                    "كود المنتج": orig_code, "اللون": orig_color, "القياس": orig_size, "الكمية": orig_qty,
                    "كود المنتج_جديد": orig_code if scanned_qty > 0 else "",
                    "اللون_جديد": orig_color if scanned_qty > 0 else "",
                    "القياس_جديد": orig_size if scanned_qty > 0 else "",
                    "الكمية_جديدة": scanned_qty,
                    "الفرق": diff
                })

                # حفظ الفهارس التي تمت مطابقتها
                for barcode in st.session_state.scanned_barcodes:
                    b_len = len(barcode)
                    if b_len in [6, 8, 10] and barcode[0:6] == orig_code:
                        matched_indices.add(barcode)

             # 2. رصد وإضافة المواد الزائدة بالكامل (الممسوحة وغير موجودة في الإكسل) لتتوافق مع السرعة الجديدة
            for barcode, info in st.session_state.scanned_barcodes.items():
                if barcode in matched_indices:
                    continue
                
                b_len = len(barcode)
                b_code = info["code"]
                b_color = info["color"]
                b_size = info["size"]
                qty = info["qty"]
                
                jard_data.append({
                    "كود المنتج": "", "اللون": "", "القياس": "", "الكمية": 0,
                    "كود المنتج_جديد": b_code,
                    "اللون_جديد": b_color,
                    "القياس_جديد": b_size,
                    "الكمية_جديدة": qty,
                    "الفرق": qty
                })

            # تحويل البيانات إلى جدول pandas DataFrame النهائي
            df_final_jard = pd.DataFrame(jard_data)

            # 3. دالة التلوين الذكي للأسطر بناءً على قيمة الفرق وحالة القراءة
            def style_jard_rows(row):
                styles = [''] * len(row)
                diff_val = row["الفرق"]
                orig_qty_val = row["الكمية"]
                new_qty_val = row["الكمية_جديدة"]
                
                # حالة المادة المطلوبة ولم يقرأها الموظف إطلاقاً (عجز كامل)
                if orig_qty_val > 0 and new_qty_val == 0:
                    # تلوين الأعمدة الأصلية على اليمين باللون الأحمر الداكن
                    for i in range(4):
                        styles[i] = 'background-color: #FED7D7; color: #9B2C2C;'
                # حالة النقص (الكمية المقروءة أقل من المطلوبة)
                elif diff_val < 0:
                    return ['background-color: #FFF5F5; color: #C53030; font-weight: bold;'] * len(row)
                # حالة الزيادة أو البضاعة الزائدة بالكامل
                elif diff_val > 0:
                    return ['background-color: #F0FFF4; color: #22543D; font-weight: bold;'] * len(row)
                
                return styles

            # عرض الجدول الملون المكون من 9 أعمدة بشكل تفاعلي حي
            st.write("📊 **جدول مقارنة الجرد الحي (9 أعمدة):**")
            st.dataframe(df_final_jard.style.apply(style_jard_rows, axis=1), use_container_width=True)

            st.write("---")
            # 1. زر إبلاغ البرنامج بانتهاء عملية الجرد بالكامل
            if not st.session_state.jard_completed:
                if st.button("🏁 تأكيد إنهاء الجرد وإصدار التقرير الملون النهائي"):
                    st.session_state.jard_completed = True
                    st.rerun()

            # 2. في حال الضغط على زر الإنهاء، يتم توليد ملف الإكسل وتوفير زر التحميل
            if st.session_state.jard_completed:
                st.success("🎉 تم إنهاء الجرد بنجاح! جاري تحضير ملف التقرير الملون الحقيقي...")
                
                # إنشاء ملف الإكسل وتنسيقه بالألوان داخل الذاكرة
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final_jard.to_excel(writer, index=False, sheet_name='تقرير الجرد الملون')
                    
                    # الوصول لتنسيقات الخلايا عبر openpyxl لتلوين الملف المفرغ
                    workbook = writer.book
                    worksheet = writer.sheets['تقرير الجرد الملون']
                    
                    # تعريف الألوان المستعملة للتصدير (أحمر خفيف وأخضر خفيف)
                    from openpyxl.styles import PatternFill
                    red_fill = PatternFill(start_color="FFD2D2", end_color="FFD2D2", fill_type="solid")
                    green_fill = PatternFill(start_color="D2F8D2", end_color="D2F8D2", fill_type="solid")
                    
                    # المرور على الأسطر لتلوين الإكسل بناءً على قيمة الفرق (العمود التاسع والأخير)
                    for r_idx, row_data in enumerate(jard_data, start=2):
                        diff_val = row_data["الفرق"]
                        orig_qty = row_data["الكمية"]
                        new_qty = row_data["الكمية_جديدة"]
                        
                        # حالة عجز كامل (تلوين أول 4 أعمدة بالأحمر)
                        if orig_qty > 0 and new_qty == 0:
                            for c_idx in range(1, 5):
                                worksheet.cell(row=r_idx, column=c_idx).fill = red_fill
                        # حالة نقص (تلوين السطر كاملاً بالأحمر)
                        elif diff_val < 0:
                            for c_idx in range(1, 10):
                                worksheet.cell(row=r_idx, column=c_idx).fill = red_fill
                        # حالة زيادة (تلوين السطر كاملاً بالأخضر)
                        elif diff_val > 0:
                            for c_idx in range(1, 10):
                                worksheet.cell(row=r_idx, column=c_idx).fill = green_fill
                                
                excel_data = output.getvalue()
                
                # عرض كبسة تحميل ملف الإكسل الملون والجاهز للموظف
                st.download_button(
                    label="📥 تحميل تقرير الجرد الملون (Excel)",
                    data=excel_data,
                    file_name="Torino_Final_Jard_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                if st.button("🔄 إعادة فتح الجرد للمسح مجدداً"):
                    st.session_state.scanned_barcodes = {}
                    if os.path.exists("jard_backup.json"):
                        os.remove("jard_backup.json")
                    st.session_state.jard_completed = False
                    st.rerun()

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الجرد: {e}")

    st.stop()

st.markdown("<h1 style='text-align: center; color: #1A365D;'>Torino Moda Style</h1>", unsafe_allow_html=True)
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
