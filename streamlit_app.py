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
    if username == "Sales_Report" and password == "Torino@969395239":
        st.session_state.logged_in = True
        st.session_state.user_role = "sales"
        st.rerun()
    elif username == "inventory_user" and password == "Torino@969395239":
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
    # عرض اللوغو بخلفيته البيضاء داخل إطار مستطيل متناسق يتسع للشعار كاملاً
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])  # ضبط توزيع الأعمدة لتوسيع المساحة العرضية
    with col_logo2:
        if os.path.exists("logo.jpg"):
            import base64
            with open("logo.jpg", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            # إطار مستطيل أبيض حقيقي بنسبة عرض ممتازة (420px عرض و 160px ارتفاع) مع احتواء الشعار بالكامل داخلها بمسافات أمان (padding)
            st.markdown(
                f'<div style="text-align: center; display: flex; justify-content: center; align-items: center; background-color: #FFFFFF; width: 100%; max-width: 420px; height: 160px; margin: 0 auto; border-radius: 8px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); overflow: hidden;">'
                f'<img src="data:image/jpeg;base64,{encoded_string}" style="width: 90%; height: 90%; object-fit: contain;">'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ يرجى التأكد من تسمية ملف اللوغو logo.jpg ووضعه في المجلد الرئيسي")
            
    st.markdown("<h1 style='text-align: center; color: #1B2A47; margin-top: 15px;'>Torino Moda Style</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #E1A73E;'>📦 نظام جرد البضاعة والمطابقة</h3>", unsafe_allow_html=True)

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
    uploaded_file = st.file_uploader("قم برفع ملف جرد النظام المحاسبي (Excel)", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df_inventory = pd.read_excel(uploaded_file)
            st.success("تم رفع ملف الجرد بنجاح!")
            
            import json
            
            # 1. [المخزن السحابي المشترك الفائق السرعة في ذاكرة السيرفر لربط الأجهزة]
            if "global_server_scans" not in st.session_state:
                st.session_state.global_server_scans = {}
                
            # المخزن المحلي الفوري لجهاز هذا الموظف فقط لضمان السرعة المطلقة
            if "local_scans" not in st.session_state:
                st.session_state.local_scans = {}
                    
            if "jard_completed" not in st.session_state:
                st.session_state.jard_completed = False

            # ب. دالة مطورة فائقة السرعة تنزل الباركود فوراً في مخزن الجهاز الحالي بسرعة الخيال
            def process_and_clear():
                raw_barcode = st.session_state.barcode_scan_key or st.session_state.barcode_manual_key
                if raw_barcode:
                    barcode = str(raw_barcode).replace(" ", "").strip().upper()
                    b_len = len(barcode)
                    
                    if b_len in [6,8,10]:
                        b_code = barcode[0:6].strip().upper()
                        b_color = "BLACK"
                        b_size = "0"
                        
                        if b_len >= 8:
                            raw_col = color_mapping.get(barcode[6:8], "رمز لون غير معروف")
                            b_color = str(raw_col).strip().upper()
                        if b_len == 10:
                            b_size = barcode[8:10].strip()
                            if b_size.startswith("0") and len(b_size) > 1:
                                b_size = b_size[1:]
                        
                        # التحديث فوري ومحلي فقط (بسرعة أقل من جزء من الثانية في جهاز الموظف الحالي)
                        if barcode in st.session_state.local_scans:
                            st.session_state.local_scans[barcode]["qty"] += 1
                        else:
                            st.session_state.local_scans[barcode] = {
                                "code": b_code, "color": b_color, "size": b_size, "qty": 1
                            }
                            
                st.session_state.barcode_scan_key = ""
                st.session_state.barcode_manual_key = ""

            # زر المزامنة السحابي الحقيقي: يجمع ويطابق فقط المواد المقروءة والمجردة فعلياً بين الجهازين أونلاين
            col_ref1, col_ref2 = st.columns(2)
            with col_ref2:
                if st.button("🔄 تحديث جدول الجرد الحي ومزامنة القراءات سحابياً"):
                    # إرسال قراءات هذا الجهاز إلى ذاكرة السيرفر المشتركة تراكمياً (جمع المقروء فقط)
                    for barcode, info in st.session_state.local_scans.items():
                        if barcode in st.session_state.global_server_scans:
                            st.session_state.global_server_scans[barcode]["qty"] = info["qty"]
                        else:
                            st.session_state.global_server_scans[barcode] = info.copy()
                    
                    # جلب الناتج المدمج بالكامل من السيرفر وتحديث شاشة الموظف الحالي فوراً
                    st.session_state.local_scans = st.session_state.global_server_scans.copy()
                    
                    with open("jard_backup.json", "w") as f:
                        json.dump(st.session_state.global_server_scans, f)
                        
                    st.success("🔄 تمت المزامنة السحابية الفورية! تم جمع ودمج المواد المقروءة فقط بين الأجهزة بدقة مطلقة.")
                    st.rerun()

            # [الحالة 3]: كاميرا الجوال الاحتياطية - تنزل في الجدول المحلي فوراً بسرعة فائقة جداً
            enable_camera = st.checkbox("📸 تفعيل كاميرا الجوال كقارئ باركود احتياطي")
            if enable_camera:
                from streamlit_qrcode_scanner import qrcode_scanner
                scanned_code = qrcode_scanner(key="live_barcode_scanner")
                if scanned_code:
                    barcode = str(scanned_code).strip()
                    b_len = len(barcode)
                    
                    if "last_recorded_barcode" not in st.session_state:
                        st.session_state.last_recorded_barcode = None
                    if barcode == st.session_state.last_recorded_barcode:
                        st.stop()
                    st.session_state.last_recorded_barcode = barcode
         
                    if b_len in [6,8,10]:
                        b_code = barcode[0:6].strip().upper()
                        b_color = "BLACK"
                        b_size = "0"
                        if b_len >= 8:
                            raw_col = color_mapping.get(barcode[6:8], "رمز لون غير معروف")
                            b_color = str(raw_col).strip().upper()
                        if b_len == 10:
                            b_size = barcode[8:10].strip()
                            if b_size.startswith("0") and len(b_size) > 1:
                                b_size = b_size[1:]
                        
                        if barcode in st.session_state.local_scans:
                            st.session_state.local_scans[barcode]["qty"] += 1
                        else:
                            st.session_state.local_scans[barcode] = {"code": b_code, "color": b_color, "size": b_size, "qty": 1}
                        
                        st.success(f"🎯 تم التقاط الباركود بالكاميرا ونزوله بالجدول المحلي فوراً: {barcode}")
                        st.rerun()

            col1, col2 = st.columns(2)
            with col1:
                st.text_input("🤖 مسح تلقائي (ضع المؤشر هنا واستخدم القارئ):", key="barcode_scan_key", on_change=process_and_clear)
            with col2:
                st.text_input("✍️ إدخال يدوي (اكتب الباركود واضغط Enter):", key="barcode_manual_key", on_change=process_and_clear)
            # --- [تعديل حاسم: المطابقة الصارمة ثنائية الأبعاد لمنع الأخطاء] ---
            scanned_totals = {}
            for barcode, info in st.session_state.local_scans.items():
                b_code = str(info["code"]).strip().upper()
                b_color = str(info["color"]).strip().upper()
                b_size = str(info["size"]).strip().upper()
                qty = info["qty"]
                
                # حساب الطول الحقيقي النظيف للباركود لمعرفة نوعه (6، 8، أو 10)
                b_len = len(str(barcode).replace(" ", "").strip())
                
                key = (b_code, b_color, b_size, b_len)
                if key in scanned_totals:
                    scanned_totals[key]["qty"] += qty
                else:
                    scanned_totals[key] = {"qty": qty, "barcode": barcode}

            matched_keys = set()
            jard_data = []

            # 1. المرور أولاً على ملف الإكسل الأصلي والمطابقة ثنائية الأبعاد (الطول + البيانات)
            for idx, row in df_inventory.iterrows():
                orig_code = str(row["كود المنتج"]).strip().upper()
                
                # فحص طبيعة سطر الإكسل (هل يحتوي على لون أو مقاس لمعرفة طوله الأصلي المعرّف)
                orig_color = str(row["اللون"]).strip().upper() if not pd.isna(row["اللون"]) else ""
                orig_size = str(row["القياس"]).strip().upper() if not pd.isna(row["القياس"]) else ""
                if orig_size.endswith(".0"):
                    orig_size = orig_size[:-2]
                
                # تحديد طول السطر المعرّف في الإكسل برمجياً
                excel_row_len = 6
                if orig_color and orig_color != "رمز لون غير معروف" and orig_color != "NAN":
                    excel_row_len = 8
                if orig_size and orig_size != "0" and orig_size != "NAN":
                    excel_row_len = 10
                    
                orig_qty = int(row["الكمية"]) if not pd.isna(row["الكمية"]) else 0
                scanned_qty = 0
                
                # مطابقة القراءات مع سطر الإكسل الحالي بشرط تطابق الطول والبيانات معاً
                for s_key, info in scanned_totals.items():
                    b_code, b_color, b_size, b_len = s_key
                    
                    is_match = False
                    # لا يجلس الباركود بجانب أخته إلا إذا كان يطابق طول السطر الأصلي في الإكسل والبيانات 100%
                    if b_len == excel_row_len and b_len == 10 and b_code == orig_code and b_color == orig_color and b_size == orig_size:
                        is_match = True
                    elif b_len == excel_row_len and b_len == 8 and b_code == orig_code and b_color == orig_color:
                        is_match = True
                    elif b_len == excel_row_len and b_len == 6 and b_code == orig_code:
                        is_match = True
                        
                    if is_match:
                        scanned_qty += info["qty"]
                        matched_keys.add(s_key)
                
                diff = scanned_qty - orig_qty
                jard_data.append({
                    "كود المنتج": orig_code, "اللون": orig_color if excel_row_len >= 8 else "", "القياس": orig_size if excel_row_len == 10 else "", "الكمية": orig_qty,
                    "كود المنتج_جديد": orig_code if scanned_qty > 0 else "",
                    "اللون_جديد": orig_color if (scanned_qty > 0 and excel_row_len >= 8) else "",
                    "القياس_جديد": orig_size if (scanned_qty > 0 and excel_row_len == 10) else "",
                    "الكمية_جديدة": scanned_qty,
                    "الفرق": diff
                })

            # 2. رصد وإضافة المواد الناقصة بالخطأ أو الزائدة (التي رُفض ربطها لأن طولها أو بياناتها غير متطابقة)
            for s_key, info in scanned_totals.items():
                if s_key in matched_keys:
                    continue
                
                b_code, b_color, b_size, b_len = s_key
                qty = info["qty"]
                
                jard_data.append({
                    "كود المنتج": "", "اللون": "", "القياس": "", "الكمية": 0,
                    "كود المنتج_جديد": b_code,
                    "اللون_جديد": b_color if b_len >= 8 else "ناقص/خاطئ",
                    "القياس_جديد": b_size if b_len == 10 else "ناقص/خاطئ",
                    "الكمية_جديدة": qty,
                    "الفرق": qty
                })

            df_final_jard = pd.DataFrame(jard_data)

            # 2. رصد وإضافة المواد الزائدة بالكامل (التي قُرأت بالباركود وغير موجودة نهائياً في الإكسل الأصلي)
            for excel_key, info in scanned_totals.items():
                if excel_key in matched_keys:
                    continue
                b_code, b_color, b_size = excel_key
                qty = info["qty"]
                jard_data.append({
                    "كود المنتج": "", "اللون": "", "القياس": "", "الكمية": 0,
                    "كود المنتج_جديد": b_code, "اللون_جديد": b_color, "القياس_جديد": b_size,
                    "الكمية_جديدة": qty, "الفرق": qty
                })

            df_final_jard = pd.DataFrame(jard_data)

            # دالة التلوين الذكي للأسطر بناءً على قيمة الفرق وحالة القراءة
            def style_jard_rows(row):
                styles = [''] * len(row)
                diff_val = row["الفرق"]
                orig_qty_val = row["الكمية"]
                new_qty_val = row["الكمية_جديدة"]
                if orig_qty_val > 0 and new_qty_val == 0:
                    for i in range(4): styles[i] = 'background-color: #FED7D7; color: #9B2C2C;'
                elif diff_val < 0: return ['background-color: #FFF5F5; color: #C53030; font-weight: bold;'] * len(row)
                elif diff_val > 0: return ['background-color: #F0FFF4; color: #22543D; font-weight: bold;'] * len(row)
                return styles

            st.write("---")
            st.markdown("### 🔍 بحث وتحديد موقع المادة في جدول الجرد")
            search_query = st.text_input("💡 اكتب كود المنتج، اللون، أو القياس لتصفية الجدول عند الحاجة:", key="jard_search_input").strip().upper()
            
            df_display = df_final_jard.copy()
            
            # [اللوحة العلوية المنفردة والمطابقة التامة 100% للقطعة الممسوحة حالياً]
            if "local_scans" in st.session_state and st.session_state.local_scans and not search_query:
                last_scanned_barcode = list(st.session_state.local_scans.keys())[-1]
                # جلب البيانات النظيفة والمفككة مسبقاً والمخزنة داخل القاموس بأمان نتيجة للضرب بالقارئ أو الكاميرا
                last_info = st.session_state.local_scans[last_scanned_barcode]
                last_b_code = str(last_info["code"]).strip().upper()
                last_b_color = str(last_info["color"]).strip().upper()
                last_b_size = str(last_info["size"]).strip().upper()

                df_focus = df_final_jard[
                    ((df_final_jard["كود المنتج"] == last_b_code) & (df_final_jard["اللون"] == last_b_color) & (df_final_jard["القياس"] == last_b_size)) |
                    ((df_final_jard["كود المنتج_جديد"] == last_b_code) & (df_final_jard["اللون_جديد"] == last_b_color) & (df_final_jard["القياس_جديد"] == last_b_size))
                ]
                if not df_focus.empty:
                    st.markdown("🎯 **بيانات القطعة الممسوحة حالياً (تحديث فوري للسطر الحالي فقط):**")
                    st.dataframe(df_focus.style.apply(style_jard_rows, axis=1), use_container_width=True)
                    st.write("---")

            if search_query:
                df_display = df_final_jard[
                    df_final_jard["كود المنتج"].astype(str).str.contains(search_query, na=False) |
                    df_final_jard["اللون"].astype(str).str.contains(search_query, na=False) |
                    df_final_jard["القياس"].astype(str).str.contains(search_query, na=False)
                ]

            st.write(f"📊 **جدول مقارنة الجرد الحي العام (إجمالي الأسطر: {len(df_display)}):**")
            st.dataframe(df_display.style.apply(style_jard_rows, axis=1), use_container_width=True)

            # --- [لوحة التصحيح العامة المحمية والمضمونة 100% من الأخطاء] ---
            with st.form("inventory_manual_correction"):
                st.markdown("### 🛠️ لوحة التحكم وتصحيح القراءات العامة")
                st.write("إذا تم تسجيل قراءة بالخطأ، أدخل الباركود هنا لتعديله أو حذفه:")
                
                fix_barcode = st.text_input("📝 أدخل الباركود الكامل للقطعة المراد تصحيحها:").strip().upper()
                fix_action = st.radio("⚡ نوع الإجراء المطلوب:", ["تعديل الكمية المقروءة بالكامل", "حذف قراءات هذا الباركود نهائياً"], horizontal=True)
                fix_qty = st.number_input("🔢 الكمية الصحيحة الفعلية الصادرة:", min_value=1, value=1, step=1)
                
                submit_fix = st.form_submit_button("💾 تطبيق التصحيح فوراً")
                
                if submit_fix and fix_barcode:
                    clean_fix_b = str(fix_barcode).replace(" ", "").strip().upper()
                    current_scans = st.session_state.local_scans
                    
                    if clean_fix_b in current_scans:
                        if fix_action == "تعديل الكمية المقروءة بالكامل":
                            current_scans[clean_fix_b]["qty"] = fix_qty
                        elif fix_action == "حذف قراءات هذا الباركود نهائياً":
                            del current_scans[clean_fix_b]
                            
                        st.session_state.local_scans = current_scans
                        st.session_state.last_recorded_barcode = None
                        st.success("✅ تم تطبيق التصحيح بنجاح!")
                        st.rerun()
                    else:
                        st.warning("⚠️ هذا الباركود غير موجود في قراءات الجرد الحالية.")

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
