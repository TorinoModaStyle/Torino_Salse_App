import streamlit as st
import pandas as pd
import numpy as np
import os, zipfile, io, arabic_reshaper
from bidi.algorithm import get_display
import openpyxl
from openpyxl.styles import PatternFill

# مكتبات الـ PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# إعدادات الصفحة الأساسية لتطبيق الجرد
st.set_page_config(
    page_title="Torino Moda Style - Analytics",
    page_icon="📊",
    layout="centered"
)

# دالة إصلاح اللغة العربية في التقارير والملفات
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

# --- عرض اللوغو واسم الشركة ونوع التقرير مباشرة بدون كلمة مرور ---
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    if os.path.exists("logo.jpg"):
        import base64
        with open("logo.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f'<div style="text-align: center; display: flex; justify-content: center; align-items: center;">'
            f'<img src="data:image/jpeg;base64,{encoded_string}" style="width: 90%; height: 90%; object-fit: contain;">'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ يرجى التأكد من تسمية ملف اللوغو logo.jpg ووضعه في المجلد الرئيسي")

st.markdown("<h1 style='text-align: center; color: #1B2A47; margin-top: 15px;'>Torino Moda Style</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #E1A73E;'>📦 نظام جرد البضاعة والمطابقة</h3>", unsafe_allow_html=True)

# ----------------------------------------------------
# الخطوة القادمة: سنضع هنا بقية كود الجرد البرمجي الفعلي
# ----------------------------------------------------

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
            # [نظام التأمين الحاسم ضد انقطاع الإنترنت وإغلاق الموقع]
            # إذا انقطع الإنترنت أو أُغلق الموقع، نقوم فوراً باستعادة آخر حالة جرد محفوظة من الملف المشترك
            if "local_scans" not in st.session_state:
                if os.path.exists("jard_backup.json"):
                    try:
                        with open("jard_backup.json", "r") as f:
                            # شحن المخزن المحلي بآخر قراءات مدمجة ومزامنة تم حفظها قبل الفصل
                            st.session_state.local_scans = json.load(f)
                    except:
                        st.session_state.local_scans = {}
                else:
                    st.session_state.local_scans = {}
                    
            if "jard_completed" not in st.session_state:
                st.session_state.jard_completed = False

            # ب. دالة مطورة فائقة السرعة تنزل الباركود فوراً في مخزن الجهاز الحالي ليظهر في الجدول أمام الموظف مباشرة
            def process_and_clear():
                raw_barcode = st.session_state.barcode_scan_key or st.session_state.barcode_manual_key
                if raw_barcode:
                    barcode = str(raw_barcode).strip()
                    b_len = len(barcode)
                    
                    if b_len in [6, 8, 10]:
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
                        
                        # التحديث فوري ومحلي فقط (يظهر في جدول هذا الموظف فوراً)
                        if barcode in st.session_state.local_scans:
                            st.session_state.local_scans[barcode]["qty"] += 1
                        else:
                            st.session_state.local_scans[barcode] = {
                                "code": b_code, "color": b_color, "size": b_size, "qty": 1
                            }
                            
                st.session_state.barcode_scan_key = ""
                st.session_state.barcode_manual_key = ""

            # زر المزامنة المطور: هو المسؤول الوحيد عن إرسال القراءات المحلية للملف وجلب قراءات الموظف الثاني ودمجها
            col_ref1, col_ref2 = st.columns(2)
            with col_ref2:
                if st.button("🔄 تحديث جدول الجرد الحي ومزامنة القراءات"):
                    # 1. جلب ما كتبه الموظف الآخر في الملف المشترك أولاً
                    file_scans = {}
                    if os.path.exists("jard_backup.json"):
                        try:
                            with open("jard_backup.json", "r") as f:
                                file_scans = json.load(f)
                        except:
                            file_scans = {}

                    # 2. دمج القراءات المحلية لهذا الجهاز مع القراءات القادمة من الملف المشترك (تراكمياً بدون مسح)
                    # ننسخ أولاً قراءات الملف كقاعدة للدمج
                    merged_scans = file_scans.copy()
                    
                    # نمر على كل الباركودات التي جردها هذا الموظف محلياً ونضيفها أو نزيد كميتها فوق قراءات الملف
                    for barcode, info in st.session_state.local_scans.items():
                        if barcode in merged_scans:
                            # إذا جرد الموظف الآخر نفس الباركود، نأخذ القيمة الأكبر أو نجمعهم؟ (الأصح في الجرد المشترك هو الجمع التراكمي)
                            # هنا نقوم بدمج الكمية المحلية مع كمية الموظف الآخر لكي لا يضيع جرد أي طرف
                            merged_scans[barcode]["qty"] = file_scans[barcode]["qty"] + info["qty"]
                        else:
                            merged_scans[barcode] = info

                    # 3. حفظ الناتج الكلي المدمج في الملف وفي ذاكرة الشاشة لكي يتحدث الجدول بالكامل
                    st.session_state.local_scans = merged_scans
                    with open("jard_backup.json", "w") as f:
                        json.dump(merged_scans, f)
                    
                    st.success("🔄 تمت مزامنة ودمج القراءات بين الجهازين بنجاح دون حذف أي بيانات!")
                    st.rerun()

            # ج. خيار احتياطي مدمج لتحديث قراءات الكاميرا الحية تلقائياً دون تعليق المتصفح
            enable_camera = st.checkbox("📸 تفعيل كاميرا الجوال كقارئ باركود احتياطي")
            if enable_camera:
                from streamlit_qrcode_scanner import qrcode_scanner
                scanned_code = qrcode_scanner(key="live_barcode_scanner")
                if scanned_code:
                    barcode = str(scanned_code).strip()
                    b_len = len(barcode)
                    # --- نظام قفل الكاميرا الذكي ومنع التكرار المستمر المستقر ---
                    if "last_recorded_barcode" not in st.session_state:
                        st.session_state.last_recorded_barcode = None
                    
                    # إذا كان الباركود الممسوح هو نفس آخر باركود تم تسجيله، يتم قفله وتجاهله فوراً
                    if barcode == st.session_state.last_recorded_barcode:
                        st.stop()  # إيقاف فوري لمنع تسجيل القراءة الثانية أو التكرار اللانهائي
                    
                    # حفظ الباركود الحالي كآخر باركود مسجل لمنع تكراره في الإطارات القادمة
                    st.session_state.last_recorded_barcode = barcode
                    # --- نهاية نظام التثبيت القاطع ---
         
                    if b_len in [6, 8, 10]:
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
                        
                    # التحديث فوري ومحلي فقط من الكاميرا ليظهر بالجدول أمام هذا الموظف فوراً
                    if barcode in st.session_state.local_scans:
                        st.session_state.local_scans[barcode]["qty"] += 1
                    else:
                        st.session_state.local_scans[barcode] = {"code": b_code, "color": b_color, "size": b_size, "qty": 1}
                    
                    st.success(f"🎯 تم التقاط الباركود بالكاميرا ونزوله بالجدول المحلي: {barcode}")
                    st.rerun()

            # ج. خانات الإدخال المحدثة والمربوطة بالتصفير الفوري التلقائي (on_change)
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("🤖 مسح تلقائي (ضع المؤشر هنا واستخدم القارئ):", key="barcode_scan_key", on_change=process_and_clear)
            with col2:
                st.text_input("✍️ إدخال يدوي (اكتب الباركود واضغط Enter):", key="barcode_manual_key", on_change=process_and_clear)

            # د. معالجة وتوليد الجدول المتكامل المكون من 9 أعمدة كاملة
            # نقوم ببناء قائمة البيانات الجديدة لمطابقتها وعرضها
            jard_data = []
            
            # تتبع المواد الأصلية التي تم فحصها من الإكسل
            matched_indices = set()
            
            # --- [تم الإصلاح الحاسم ومنع التكرار نهائياً عبر التجميع المسبق للقراءات] ---
            scanned_totals = {}
            for barcode, info in st.session_state.local_scans.items():
                b_code = str(info["code"]).strip().upper()
                b_color = str(info["color"]).strip().upper()
                b_size = str(info["size"]).strip().upper()
                qty = info["qty"]
                
                key = (b_code, b_color, b_size)
                if key in scanned_totals:
                    scanned_totals[key]["qty"] += qty
                else:
                    scanned_totals[key] = {"qty": qty, "barcode": barcode}

            matched_keys = set()
            jard_data = []

            # 1. المرور أولاً على ملف الإكسل الأصلي وإنزال الكميات المجمعة أمامه (سطر بسطر دون أي تكرار)
            for idx, row in df_inventory.iterrows():
                orig_code = str(row["كود المنتج"]).strip().upper()
                orig_color = str(row["اللون"]).strip().upper()
                orig_size = str(row["القياس"]).strip().upper()
                if orig_size.endswith(".0"):
                    orig_size = orig_size[:-2]
                orig_qty = int(row["الكمية"]) if not pd.isna(row["الكمية"]) else 0
                
                excel_key = (orig_code, orig_color, orig_size)
                
                scanned_qty = 0
                if excel_key in scanned_totals:
                    scanned_qty = scanned_totals[excel_key]["qty"]
                    matched_keys.add(excel_key)
                
                diff = scanned_qty - orig_qty
                jard_data.append({
                    "كود المنتج": orig_code, "اللون": orig_color, "القياس": orig_size, "الكمية": orig_qty,
                    "كود المنتج_جديد": orig_code if scanned_qty > 0 else "",
                    "اللون_جديد": orig_color if scanned_qty > 0 else "",
                    "القياس_جديد": orig_size if scanned_qty > 0 else "",
                    "الكمية_جديدة": scanned_qty,
                    "الفرق": diff
                })

            # 2. رصد وإضافة المواد الزائدة بالكامل (التي قُرأت بالباركود وغير موجودة نهائياً في الإكسل الأصلي)
            for excel_key, info in scanned_totals.items():
                if excel_key in matched_keys:
                    continue
                
                b_code, b_color, b_size = excel_key
                qty = info["qty"]
                
                jard_data.append({
                    "كود المنتج": "", "اللون": "", "القياس": "", "الكمية": 0,
                    "كود المنتج_جديد": b_code,
                    "اللون_جديد": b_color,
                    "القياس_جديد": b_size,
                    "الكمية_جديدة": qty,
                    "الفرق": qty
                })

            # تحويل البيانات إلى جدول pandas DataFrame النهائي المستقر
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

            st.write("---")
            st.markdown("### 🔍 بحث وتحديد موقع المادة في جدول الجرد")
            
            # 1. خانة البحث اليدوية (تقوم بالتصفية بناءً على طلبك في النقطة الرابعة فقط)
            search_query = st.text_input("💡 اكتب كود المنتج، اللون، أو القياس لتصفية الجدول عند الحاجة:", key="jard_search_input").strip().upper()
            
            # بناء الجدول الكامل المكون من كافة الأسطر بترتيبها الأصلي الثابت بالأسفل
            df_display = df_final_jard.copy()
            
            # 2. [التعديل الثالث الذكي والمعدل بدقة]: لوحة المتابعة البصرية الفورية للسطر الفعلي والوحيد للقطعة الممسوحة
            if "local_scans" in st.session_state and st.session_state.local_scans and not search_query:
                # جلب آخر باركود كامل تم مسحه (يحتوي على الكود واللون والمقاس)
                last_scanned_barcode = list(st.session_state.local_scans.keys())[-1]
                
                # تفكيك الباركود بدقة لاستخراج القيم الفردية ومطابقتها مع الجدول
                last_b_len = len(last_scanned_barcode)
                last_b_code = str(last_scanned_barcode)[0:6].strip().upper()
                last_b_color = "BLACK"
                last_b_size = "0"
                
                if last_b_len >= 8:
                    raw_col = color_mapping.get(last_scanned_barcode[6:8], "رمز لون غير معروف")
                    last_b_color = str(raw_col).strip().upper()
                if last_b_len == 10:
                    last_b_size = last_scanned_barcode[8:10].strip()
                    if last_b_size.startswith("0") and len(last_b_size) > 1:
                        last_b_size = last_b_size[1:]
                
                # جلب السطر الفعلي الدقيق والوحيد الذي يطابق الكود واللون والقياس معاً (سطر واحد فقط)
                df_focus = df_final_jard[
                    ((df_final_jard["كود المنتج"] == last_b_code) & (df_final_jard["اللون"] == last_b_color) & (df_final_jard["القياس"] == last_b_size)) |
                    ((df_final_jard["كود المنتج_جديد"] == last_b_code) & (df_final_jard["اللون_جديد"] == last_b_color) & (df_final_jard["القياس_جديد"] == last_b_size))
                ]
                
                if not df_focus.empty:
                    st.markdown("🎯 **بيانات القطعة الممسوحة حالياً (تحديث فوري للسطر الحالي فقط):**")
                    # عرض السطر المنفرد المختار
                    st.dataframe(df_focus.style.apply(style_jard_rows, axis=1), use_container_width=True)
                    st.markdown("<p style='color: #718096; font-size: 13px; margin-top: -10px;'>💡 تم إبراز السطر الفعلي لهذه القطعة فقط في الأعلى لسهولة التحقق الحركي، مع بقاء الجدول العام بالأسفل كاملاً.</p>", unsafe_allow_html=True)
                    st.write("---")

            # 3. التصفية تحدث للجدول الأساسي بالأسفل فقط وفقط إذا قام الموظف بالبحث يدوياً
            if search_query:
                df_display = df_final_jard[
                    df_final_jard["كود المنتج"].astype(str).str.contains(search_query, na=False) |
                    df_final_jard["اللون"].astype(str).str.contains(search_query, na=False) |
                    df_final_jard["القياس"].astype(str).str.contains(search_query, na=False)
                ]

            # 4. عرض الجدول القياسي الكامل بكافة أسطره الـ 5640 وبترتيبه الأصلي الثابت دون أي تصفية عند القراءة الآلية
            st.write(f"📊 **جدول مقارنة الجرد الحي العام (إجمالي الأسطر: {len(df_display)}):**")
            st.dataframe(df_display.style.apply(style_jard_rows, axis=1), use_container_width=True)

            # --- [التعديل المطور]: لوحة التصحيح العامة لكافة أنواع القراءات (قارئ، يدوي، كاميرا) ---
            st.write("---")
            with st.form("inventory_manual_correction"):
                st.markdown("### 🛠️ لوحة التحكم وتصحيح القراءات العامة")
                st.write("إذا تم تسجيل قراءة بالخطأ (عبر القارئ، الإدخال اليدوي، أو الكاميرا)، أدخل الباركود هنا لتعديله أو حذفه:")
                
                fix_barcode = st.text_input("📝 أدخل الباركود الكامل للقطعة المراد تصحيحها:").strip().upper()
                fix_action = st.radio("⚡ نوع الإجراء المطلوب:", ["تعديل الكمية المقروءة بالكامل", "حذف قراءات هذا الباركود نهائياً"], horizontal=True)
                fix_qty = st.number_input("🔢 الكمية الصحيحة الفعلية الصادرة:", min_value=1, value=1, step=1)
                
                submit_fix = st.form_submit_button("💾 تطبيق التصحيح فوراً وتحديث ملف الأمان")
                
                if submit_fix:
                    if not fix_barcode:
                        st.error("الرجاء إدخال الباركود المراد تصحيحه أولاً!")
                    else:
                        import os, json
                        # استخدام المخزن المحلي المطور لضمان تعديل القراءات الحية فوراً
                        current_scans = st.session_state.local_scans
                        
                        if fix_barcode not in current_scans:
                            st.warning(f"الباركود '{fix_barcode}' غير موجود في قراءات الجرد الحالية الممسوحة.")
                        else:
                            if fix_action == "تعديل الكمية المقروءة بالكامل":
                                current_scans[fix_barcode]["qty"] = fix_qty
                                st.success(f"✅ تم تصحيح كمية الباركود {fix_barcode} إلى {fix_qty} في النظام بنجاح!")
                            elif fix_action == "حذف قراءات هذا الباركود نهائياً":
                                del current_scans[fix_barcode]
                                st.success(f"🗑️ تم حذف الباركود {fix_barcode} نهائياً من الجرد!")
                            
                            # حفظ التعديلات في جلسة العمل وفي ملف النسخة الاحتياطية لضمان المزامنة
                            st.session_state.local_scans = current_scans
                            with open("jard_backup.json", "w") as f:
                                json.dump(current_scans, f)
                                
                            st.session_state.last_recorded_barcode = None    
                            st.rerun()

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
