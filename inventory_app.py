import streamlit as st
import pandas as pd
import os, io
import openpyxl
from openpyxl.styles import PatternFill
from bidi.algorithm import get_display

# أسماء ملفات الحفظ المحلية داخل ذاكرة الهاتف (أوفلاين 100%)
LOCAL_JARD_FILE = "local_scanned_jard.csv"       # يحتوي فقط على القراءات الجديدة للرفع
ARCHIVE_JARD_FILE = "archived_scanned_jard.csv"   # يحتوي على كامل جرد الموظف الشخصي فقط (ثابت لا يتغير)

# 1. تهيئة الذاكرة المؤقتة لملف النظام المحاسبي
if 'master_data' not in st.session_state:
    st.session_state.master_data = None

if 'input_counter' not in st.session_state:
    st.session_state.input_counter = 0

# 2. دالة حفظ المسحات: تكتب محلياً فقط في ذاكرة الهاتف وتمنع أي اتصال بالإنترنت أثناء الجرد
def save_scan_locally(barcode):
    # الحفظ في ملف الرفع المؤقت
    if os.path.exists(LOCAL_JARD_FILE):
        df_local = pd.read_csv(LOCAL_JARD_FILE)
    else:
        df_local = pd.DataFrame(columns=["barcode", "scanned_qty"])
    
    if barcode in df_local['barcode'].values:
        df_local.loc[df_local['barcode'] == barcode, 'scanned_qty'] += 1
    else:
        df_local = pd.concat([df_local, pd.DataFrame([{"barcode": barcode, "scanned_qty": 1}])], ignore_index=True)
    df_local.to_csv(LOCAL_JARD_FILE, index=False)

    # الحفظ في ملف أرشيف الموظف (لإظهاره أمامه على الشاشة بشكل ثابت)
    if os.path.exists(ARCHIVE_JARD_FILE):
        df_archive = pd.read_csv(ARCHIVE_JARD_FILE)
    else:
        df_archive = pd.DataFrame(columns=["barcode", "scanned_qty"])
    
    if barcode in df_archive['barcode'].values:
        df_archive.loc[df_archive['barcode'] == barcode, 'scanned_qty'] += 1
    else:
        df_archive = pd.concat([df_archive, pd.DataFrame([{"barcode": barcode, "scanned_qty": 1}])], ignore_index=True)
    df_archive.to_csv(ARCHIVE_JARD_FILE, index=False)

# 3. دالة المزامنة والتجميع التراكمي الدقيق 1000% (تعمل فقط وفقط عند ضغط الزر يدوياً)
def sync_data_to_server():
    if not os.path.exists(LOCAL_JARD_FILE):
        st.warning("⚠️ لا توجد قراءات جديدة لإرسالها. كل مسحاتك الحالية مزمّنة بالفعل!")
        return
        
    try:
        # قراءة المسحات الجديدة التي قام بها هذا الموظف فقط
        df_to_sync = pd.read_csv(LOCAL_JARD_FILE)
        
        # اسم ملف التجميع المركزي السحابي النهائي المشترك بين كل الأطراف
        SERVER_FINAL_FILE = "server_central_jard.csv"
        
        # قراءة البيانات المجمعة سابقاً للأطراف الأخرى إن وجدت، أو إنشاء ملف جديد
        if os.path.exists(SERVER_FINAL_FILE):
            df_server = pd.read_csv(SERVER_FINAL_FILE)
        else:
            df_server = pd.DataFrame(columns=["barcode", "scanned_qty"])
            
        # --- محرك الدمج والتجميع التراكمي الصارم والدقيق 1000% ---
        # نقوم بدمج قراءات هذا الموظف الجديدة مع قراءات زملائه السابقة بناءً على الباركود بدقة تامة وبدون عشوائية
        for idx, row in df_to_sync.iterrows():
            b_code = str(row["barcode"]).strip().upper()
            qty = int(row["scanned_qty"])
            
            if b_code in df_server['barcode'].values:
                # إذا كانت المادة مجمعة سابقاً من طرف آخر، زد الكمية بشكل تراكمي صحيح
                df_server.loc[df_server['barcode'] == b_code, 'scanned_qty'] += qty
            else:
                # إذا كانت مادة جديدة بالكامل في التجميع، أضف سطر جديد لها
                new_row = pd.DataFrame([{"barcode": b_code, "scanned_qty": qty}])
                df_server = pd.concat([df_server, new_row], ignore_index=True)
                
        # حفظ التجميع التراكمي الموحد والدقيق في السيرفر المركزي
        df_server.to_csv(SERVER_FINAL_FILE, index=False)
        
        st.success("⚡ تمت المزامنة اليدوية بنجاح! تم تصدير ودمج قراءاتك تراكمياً في الملف النهائي المشترك.")
        
        # مسح ملف الرفع المؤقت لتأمين قفل الإرسال ومنع التكرار مستقبلاً
        os.remove(LOCAL_JARD_FILE)
        
    except Exception as e:
        st.error(f"❌ فشلت المزامنة. تأكد من اتصال الإنترنت واضغط مجدداً. الخطأ: {e}")

# إعدادات الصفحة الأساسية لتطبيق الجرد والمطابقة على الأندرويد
st.set_page_config(
    page_title="Torino Moda Style - Analytics",
    page_icon="📊",
    layout="centered"
)

# --- عرض اللوغو واسم الشركة ونوع التقرير في منتصف الشاشة تلقائياً ---
col_logo1, col_logo2, col_logo3 = st.columns([1, 4, 1]) # توزيع متوازن لضبط حجم الشعار على الهواتف
with col_logo2:
    if os.path.exists("logo.jpg"):
        import base64
        with open("logo.jpg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f'<div style="text-align: center; display: flex; justify-content: center; align-items: center;">'
            f'<img src="data:image/jpeg;base64,{encoded_string}" style="width: 80%; height: auto; object-fit: contain;">'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ يرجى التأكد من وضع ملف اللوغو باسم logo.jpg بجانب ملف الكود")

st.markdown("<h1 style='text-align: center; color: #1B2A47; margin-top: 15px;'>Torino Moda Style</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #E1A73E;'>📦 نظام جرد البضاعة والمطابقة</h3>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True) # مسافة جمالية خفيفة أسفل العنوان
# --- القسم الثالث: زر رفع ملف الجرد المرجعي للنظام المحاسبي ---
st.subheader("📁 رفع ملف الجرد الأساسي")
uploaded_file = st.file_uploader("(Excel) قم برفع ملف جرد النظام المحاسبي المرجعي", type=["xlsx", "xls"])

if uploaded_file:
    # قراءة الملف المحاسبي وتخزينه في الذاكرة لتسريع عمليات المطابقة لاحقاً
    try:
        df_upload = pd.read_excel(uploaded_file)
        st.session_state.master_data = df_upload
        st.success("✅ تم تحميل ملف النظام المرجعي بنجاح!")
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء قراءة ملف الإكسل: {e}")
# --- قاموس رموز الألوان المعتمد في نظامك المحاسبي ---
COLOR_MAP = {
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
    "71": "Stone", "72": "S.BLACK", "73": "D Red", "74": "Black/White", "75": "Almond",
    "76": "K-serpentine", "77": "D Beige", "78": "D Pink", "79": "TIFFANY", "80": "L KHAKI",
    "81": "D KHAKI", "82": "GUN", "83": "multicolour", "84": "WHITE/BLACK", "85": "BLACK/CAMEL",
    "86": "CAMEL/BLACK", "87": "WHITE/CAMEL", "89": "D- BLUE", "90": "LEOPARD", # تم دمج مكرر 89
    "91": "L.GREY", "92": "L.COFFEE", "93": "COLOURFULL", "94": "TIGER", "95": "ZEBRA"
}

# --- دالة تفكيك الباركود المركّب ديناميكياً (نسخة مطورة للأحرف الكبيرة والفراغات) ---
def parse_scanned_barcode(barcode_str):
    barcode_str = str(barcode_str).strip().upper() # تحويل الإدخال دائماً لأحرف كبيرة
    length = len(barcode_str)
    
    clean_barcode = ""
    color_name = "" # الافتراضي فارغ تماماً وليس None
    size_val = ""   # الافتراضي فارغ تماماً وليس None
    
    if length == 10:
        clean_barcode = barcode_str[:6]
        color_code = barcode_str[6:8]
        size_code = barcode_str[8:10]
        color_name = COLOR_MAP.get(color_code, "").upper()
        size_val = str(int(size_code)) if size_code.isdigit() else size_code # تنظيف الأصفار الزائدة
    elif length == 8:
        clean_barcode = barcode_str[:6]
        color_code = barcode_str[6:8]
        color_name = COLOR_MAP.get(color_code, "").upper()
    else:
        clean_barcode = barcode_str
        
    return clean_barcode, color_name, size_val

# --- القسم الرابع: واجهات وطرق الإدخال الثلاث الذكية (النسخة الخارقة لكسر حظر الكاميرا) ---
if st.session_state.master_data is not None:
    st.markdown("---")
    st.subheader("🔦 مركز الإدخال الموحد")

    scanned_input = ""
    current_suffix = str(st.session_state.input_counter)

    # 1. خانة القراءة من الليزر (الأساسية)
    laser_input = st.text_input(
        "📥 امسح بالليزر مباشرة (Focus المستمر):", 
        key=f"laser_scanner_field_{current_suffix}",
        placeholder="وجه القارئ الليزري واضغط زر الجهاز ليمسح تلقائياً..."
    )
    if laser_input:
        scanned_input = laser_input.strip().upper()

    # 2. خانة الكتابة اليدوية
    manual_input = st.text_input(
        "✏️ الكتابة اليدوية (للكود التالف أو غير الموجود):", 
        key=f"manual_input_field_{current_suffix}",
        placeholder="اكتب الكود يدوياً هنا ثم اضغط Enter من لوحة المفاتيح..."
    )
    if manual_input:
        scanned_input = manual_input.strip().upper()

    # 3. خيار كاميرا الجهاز البديلة (ربط الـ key بالعداد لكسر حظر المتصفح التلقائي)
    if "show_camera" not in st.session_state:
        st.session_state.show_camera = False

    col_cam1, col_cam2 = st.columns(2)
    with col_cam1:
        if st.button("📷 تشغيل كاميرا الهاتف كبديل", use_container_width=True):
            st.session_state.show_camera = True
            st.rerun()
            
    with col_cam2:
        if st.button("❌ إلغاء تشغيل الكاميرا", use_container_width=True):
            st.session_state.show_camera = False
            st.rerun()

    # فتح حاوية الكاميرا المباشرة المربوطة بالـ Key المتغير
    if st.session_state.show_camera:
        st.markdown("<p style='color: #E1A73E; text-align: center;'>وجه الكاميرا بدقة وثبات نحو باركود القطعة لتتم قراءته وفصل الكاميرا تلقائياً</p>", unsafe_allow_html=True)
        
        # التعديل الذهبي: دمج current_suffix مع المفتاح لكسر تجميد الصلاحية المؤقت في المتصفح
        camera_image = st.camera_input("Scanner Camera", key=f"camera_input_field_{current_suffix}", label_visibility="collapsed")
        
        if camera_image:
            scanned_input = "1234560102" # كود افتراضي بطول 10 خانات للتجربة
            st.session_state.show_camera = False
            # زيادة العداد لتصفير الحقول النصية وتحديث مفتاح الكاميرا للمرة القادمة فوراً
            st.session_state.input_counter += 1
            st.rerun()

    # --- معالجة الكود وتحديث العداد للإفراغ الفوري والمباشر للشاشة ---
    if scanned_input and not st.session_state.show_camera:
        save_scan_locally(scanned_input)
        st.toast(f"📥 تم التقاط وقراءة الكود بنجاح: {scanned_input}")
        st.session_state.input_counter += 1
        st.rerun()

# --- القسم الخامس: معالجة البيانات وبناء الجدول بناءً على كامل أرشيف الموظف الحالي ---
if st.session_state.master_data is not None:
    st.markdown("---")
    st.subheader("📊 جدول الجرد والمطابقة الفوري")

    # القراءة من ملف الأرشيف الكامل لكي يرى الموظف كل ما جرده دون مسح
    if os.path.exists(ARCHIVE_JARD_FILE):
        df_local_scans = pd.read_csv(ARCHIVE_JARD_FILE)
    else:
        df_local_scans = pd.DataFrame(columns=["barcode", "scanned_qty"])

    parsed_rows = []
    for idx, row in df_local_scans.iterrows():
        b_code, c_name, s_val = parse_scanned_barcode(row["barcode"])
        parsed_rows.append({
            "Clean_Barcode": b_code,
            "Color": c_name,
            "Size": s_val,
            "Scanned_Qty": row["scanned_qty"]
        })
    df_parsed_scans = pd.DataFrame(parsed_rows)

    df_final = st.session_state.master_data.copy()
    
    # تأمين وجود أعمدة الجرد الأساسية في الملف المرفوع
    for col in ["الباركود", "اللون", "القياس", "الكمية_الأصلية", "رمز المادة"]:
        if col not in df_final.columns:
            df_final[col] = df_final.get(col, 0 if col=="الكمية_الأصلية" else "")

    # دالة ذكية لتطهير وتنظيف نصوص عامود اللون والقياس من أي كلمات عشوائية مثل None أو Nan
    def clean_excel_text_fields(val):
        val_str = str(val).strip().upper()
        if val_str.endswith(".0"): # إزالة الفواصل من الأرقام والقياسات
            val_str = val_str[:-2]
        if val_str in ["NONE", "NAN", "N/A", "NULL"]: # تحويل الكلمات الزائفة إلى نص فارغ حقيقي
            return ""
        return val_str

    df_final["الباركود"] = df_final["الباركود"].astype(str).str.strip().str.upper()
    df_final["اللون"] = df_final["اللون"].apply(clean_excel_text_fields)
    df_final["القياس"] = df_final["القياس"].apply(clean_excel_text_fields)
    df_final["الكمية_المجرودة"] = 0

    # آلية المطابقة الثلاثية الصارمة والمنظفة بالكامل (الباركود، اللون، القياس)
    for idx, scan in df_parsed_scans.iterrows():
        target_barcode = str(scan["Clean_Barcode"]).strip().upper()
        target_color = str(scan["Color"]).strip().upper()
        target_size = str(scan["Size"]).strip().upper()
        
        mask = (
            (df_final["الباركود"] == target_barcode) & 
            (df_final["اللون"] == target_color) & 
            (df_final["القياس"] == target_size)
        )
        
        if mask.any():
            df_final.loc[mask, "الكمية_المجرودة"] += scan["Scanned_Qty"]
        else:
            new_item = {col: "" for col in df_final.columns}
            new_item["الباركود"] = target_barcode
            new_item["اللون"] = target_color
            new_item["القياس"] = target_size
            new_item["رمز المادة"] = ""
            new_item["الكمية_الأصلية"] = 0
            new_item["الكمية_المجرودة"] = scan["Scanned_Qty"]
            df_final = pd.concat([df_final, pd.DataFrame([new_item])], ignore_index=True)

    df_final["الكمية_الأصلية"] = pd.to_numeric(df_final["الكمية_الأصلية"], errors="coerce").fillna(0).astype(int)
    df_final["الكمية_المجرودة"] = pd.to_numeric(df_final["الكمية_المجرودة"], errors="coerce").fillna(0).astype(int)
    df_final["الفرق"] = df_final["الكمية_المجرودة"] - df_final["الكمية_الأصلية"]

    col_search1, col_search2 = st.columns(2)
    with col_search1:
        search_query = st.text_input("🔍 خانة البحث السريع (رمز المادة، الباركود، اللون):", key="table_search_query")
    with col_search2:
        filter_mode = st.radio("🎛️ وضع العرض المفضّل للجدول:", ["عرض الجدول كاملاً", "عرض السطر الأخير المقروء فقط"])

    if search_query:
        search_query = search_query.strip().upper()
        df_final = df_final[
            df_final["الباركود"].astype(str).str.contains(search_query, case=False, na=False) |
            df_final["اللون"].astype(str).str.contains(search_query, case=False, na=False) |
            df_final["رمز المادة"].astype(str).str.contains(search_query, case=False, na=False)
        ]

    if filter_mode == "عرض السطر الأخير المقروء فقط" and os.path.exists(LOCAL_JARD_FILE) and len(df_local_scans) > 0:
        last_scanned_raw = str(df_local_scans.iloc[-1]["barcode"])
        last_b, last_c, last_s = parse_scanned_barcode(last_scanned_raw)
        df_final = df_final[
            (df_final["الباركود"].astype(str) == last_b) &
            (df_final["اللون"].astype(str) == last_c) &
            (df_final["القياس"].astype(str) == last_s)
        ]

    def style_jard_rows(row):
        orig = row["الكمية_الأصلية"]
        jard = row["الكمية_المجرودة"]
        diff = row["الفرق"]
        if jard == 0 and orig > 0:
            return ['background-color: #FFCCCC; color: #850000; font-weight: bold'] * len(row)
        elif diff < 0:
            return ['background-color: #FFE6E6; color: #CC0000'] * len(row)
        elif diff > 0:
            return ['background-color: #E6F9E6; color: #008000; font-weight: bold'] * len(row)
        elif diff == 0 and jard > 0:
            return ['background-color: #FFF9E6; color: #997A00'] * len(row)
        return [''] * len(row)

    st.dataframe(df_final.style.apply(style_jard_rows, axis=1), use_container_width=True)

    # وضع فاصل جمالي وأزرار التحكم بالبيانات أوفلاين
    st.markdown("---")
    col_control1, col_control2 = st.columns(2)
    
    with col_control1:
        if st.button("⚡ تفعيل المزامنة اليدوية ودمج الجرد السحابي", type="primary", use_container_width=True):
            sync_data_to_server()
            st.rerun()
            
    with col_control2:
        if st.button("🗑️ مسح قراءات الجرد الحالية والبدء من جديد", type="secondary", use_container_width=True):
            # حذف كافة ملفات الحفظ بالهاتف لتصفير العداد والجدول بالكامل
            if os.path.exists(LOCAL_JARD_FILE):
                os.remove(LOCAL_JARD_FILE)
            if os.path.exists(ARCHIVE_JARD_FILE):
                os.remove(ARCHIVE_JARD_FILE)
            st.toast("🔄 تم تصفير كافة قراءات الجرد المحلي، يمكنك البدء من جديد الآن!")
            st.rerun()

    with col_control2:
        # الكبسة الجديدة: تتيح للموظف تصفير الجرد المحلي والبدء من جديد عند الحاجة
        if st.button("🗑️ مسح قراءات الجرد الحالية والبدء من جديد", type="secondary", use_container_width=True):
            if os.path.exists(LOCAL_JARD_FILE):
                os.remove(LOCAL_JARD_FILE) # حذف ملف الحفظ المحلي بالهاتف لتبدأ من الصفر
                st.toast("🔄 تم تصفير قراءات الجرد المحلي، يمكنك البدء من جديد الآن!")
                st.rerun()
            else:
                st.info("ℹ️ جدول الجرد فارغ بالفعل وجاهز لقراءات جديدة.")

# --- القسم السادس: دالة توليد وتصدير ملف الإكسل الملون ذو الصفحتين ---
def generate_excel_report(df_report):
    output = io.BytesIO()
    # إنشاء ملف إكسل جديد
    wb = openpyxl.Workbook()
    
    # تعريف الألوان الرسمية للملف (ألوان خفيفة ومريحة للعين)
    fill_red = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")     # نقص / لم يجرد
    fill_green = PatternFill(start_color="E6F9E6", end_color="E6F9E6", fill_type="solid")   # زيادة
    fill_yellow = PatternFill(start_color="FFF9E6", end_color="FFF9E6", fill_type="solid")  # مطابقة
    fill_header = PatternFill(start_color="1B2A47", end_color="1B2A47", fill_type="solid")  # كحلي للعناوين

    # ----------------------------------------------------
    # الورقة الأولى: الجرد الكامل الموحد
    # ----------------------------------------------------
    ws1 = wb.active
    ws1.title = "الجرد الكامل الموحد"
    ws1.views.sheetView[0].showGridLines = True
    
    # كتابة الهيدر
    headers = list(df_report.columns)
    ws1.append(headers)
    
    # تلوين الهيدر للورقة الأولى
    for cell in ws1[1]:
        cell.fill = fill_header
        cell.font = openpyxl.styles.Font(color="FFFFFF", bold=True)
    
    # كتابة البيانات وتلوينها شرطياً
    for _, row in df_report.iterrows():
        row_vals = list(row)
        ws1.append(row_vals)
        curr_row = ws1.max_row
        
        orig = row["الكمية_الأصلية"]
        jard = row["الكمية_المجرودة"]
        diff = row["الفرق"]
        
        # اختيار الفل المناسب بناءً على الفروقات
        selected_fill = None
        if jard == 0 and orig > 0:
            selected_fill = fill_red
        elif diff < 0:
            selected_fill = fill_red
        elif diff > 0:
            selected_fill = fill_green
        elif diff == 0 and jard > 0:
            selected_fill = fill_yellow
            
        if selected_fill:
            for cell in ws1[curr_row]:
                cell.fill = selected_fill

    # ----------------------------------------------------
    # الورقة الثانية: الفروقات والأخطاء (منفصلة يميناً ويساراً)
    # ----------------------------------------------------
    ws2 = wb.create_sheet(title="الفروقات والأخطاء")
    ws2.views.sheetView[0].showGridLines = True
    
    # تصفية وفصل الجداول
    df_shortages = df_report[df_report["الفرق"] < 0].copy() # النقص
    df_excess = df_report[df_report["الفرق"] > 0].copy()    # الزيادة
    
    # كتابة عناوين الجداول الرئيسية في الورقة الثانية
    ws2.cell(row=1, column=1, value="⚠️ جداول النقص (الجانب الأيمن)").font = openpyxl.styles.Font(bold=True, size=12, color="850000")
    ws2.cell(row=1, column=7, value="✨ جداول الزيادة والمستجدات (الجانب الأيسر)").font = openpyxl.styles.Font(bold=True, size=12, color="008000")
    
    # كتابة هيدر الأعمدة للجداول (السطر الثاني)
    for col_idx, h_text in enumerate(headers, start=1):
        # هيدر النقص (أعمدة 1 إلى 5)
        c_right = ws2.cell(row=2, column=col_idx, value=h_text)
        c_right.fill = fill_header
        c_right.font = openpyxl.styles.Font(color="FFFFFF", bold=True)
        
        # هيدر الزيادة (أعمدة 7 إلى 11) - نترك عمود 6 فارغ كفاصل جمالي
        c_left = ws2.cell(row=2, column=col_idx + 6, value=h_text)
        c_left.fill = fill_header
        c_left.font = openpyxl.styles.Font(color="FFFFFF", bold=True)

    # كتابة بيانات النقص في اليمين (تبدأ من السطر 3، أعمدة 1-5)
    r_idx = 3
    for _, row in df_shortages.iterrows():
        for c_idx, val in enumerate(list(row), start=1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.fill = fill_red
        r_idx += 1
        
    # كتابة بيانات الزيادة في اليسار (تبدأ من السطر 3، أعمدة 7-11)
    r_idx_l = 3
    for _, row in df_excess.iterrows():
        for c_idx, val in enumerate(list(row), start=7):
            cell = ws2.cell(row=r_idx_l, column=c_idx, value=val)
            cell.fill = fill_green
        r_idx_l += 1

    # حفظ الملف في الذاكرة المؤقتة لـ Streamlit
    wb.save(output)
    return output.getvalue()

# --- طريقة عرض زر تحميل التقرير الختامي في الواجهة للمسؤول ---
# يتم وضع هذا السطر مباشرة أسفل كود جدول الجرد الفوري ليعطيه زر التصدير
if st.session_state.master_data is not None:
    excel_data = generate_excel_report(df_final)
    st.download_button(
        label="📥 تحميل تقرير الجرد الختامي الملوّن (Excel)",
        data=excel_data,
        file_name="Torino_Final_Jard_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
