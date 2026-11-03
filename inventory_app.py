import streamlit as st

# حقن إعدادات التطبيق الاحترافي في أول سطر لإجبار الهاتف على تشغيله كتطبيق مستقل فائق السرعة
st.set_page_config(
    page_title="Torino Smart Inventory",
    page_icon="🔦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# بقية مكتباتك المعتادة تحتها مباشرة...
import pandas as pd
import os, io
import openpyxl
from openpyxl.styles import PatternFill
from datetime import datetime

# 1. تهيئة الذاكرة المؤقتة لملف النظام المحاسبي المرجعي والعداد
if 'master_data' not in st.session_state:
    st.session_state.master_data = None

if 'input_counter' not in st.session_state:
    st.session_state.input_counter = 0

# تهيئة خانة حفظ اسم الموظف في الذاكرة الدائمة للتطبيق
if "employee_name" not in st.session_state:
    st.session_state.employee_name = ""

# 2. الحل الهندسي الذكي: ربط أسماء ملفات الجرد باسم الموظف المكتوب لمنع ضياع البيانات واستعادتها دائماً
EMP_SUFFIX = str(st.session_state.employee_name).strip().upper() if st.session_state.employee_name else "TEMP_GUEST"

LOCAL_JARD_FILE = f"local_jard_{EMP_SUFFIX}.csv"       # ملف الرفع الفوري الخاص بهذا الموظف وثابت باسمه
ARCHIVE_JARD_FILE = f"archive_jard_{EMP_SUFFIX}.csv"   # أرشيف الشاشة الثابت للموظف لاستعادة جِرده في أي وقت
SERVER_FINAL_FILE = "server_central_jard.csv"       # التجميع السحابي المركزي المشترك

# دالة تحديث مسارات الملفات فوراً عند كتابة أو تغيير اسم الموظف لضمان القراءة الصحيحة
def update_employee_file_paths():
    global LOCAL_JARD_FILE, ARCHIVE_JARD_FILE
    NEW_SUFFIX = str(st.session_state.employee_name).strip().upper() if st.session_state.employee_name else "TEMP_GUEST"
    LOCAL_JARD_FILE = f"local_jard_{NEW_SUFFIX}.csv"
    ARCHIVE_JARD_FILE = f"archive_jard_{NEW_SUFFIX}.csv"

# تهيئة الذاكرة المؤقتة لملف النظام المحاسبي المرجعي والعداد #
if 'input_counter' not in st.session_state:
    st.session_state.input_counter = 0

# --- واجهة الموظف الإلزامية في اللوحة الجانبية (Sidebar) ---
if st.session_state.master_data is not None:
    # حقن صندوق معلومات الموظف وزر التغيير داخل اللوحة الجانبية دائماً
    with st.sidebar:
        st.markdown("### 👤 بيانات الموظف")
        if st.session_state.employee_name:
            st.success(f"الموظف الحالي:\n**{st.session_state.employee_name}**")
            if st.button("🔄 تغيير اسم الموظف", key="unique_sidebar_change_emp_btn", use_container_width=True):
                st.session_state.employee_name = ""
                st.rerun()
        else:
            st.warning("⚠️ لم يتم تسجيل اسم الموظف بعد.")

    # عرض التنبيه وخانة الكتابة في منتصف الواجهة فقط إذا كان الاسم فارغاً
    if not st.session_state.employee_name:
        st.markdown("---")
        st.warning("⚠️ يرجى تسجيل اسم الموظف أولاً لتفعيل حقول الإدخال والبدء بالجرد.")
        emp_input = st.text_input("✍️ اكتب اسم الموظف المسؤول عن هذا الجهاز حالياً:", key="emp_name_setup_field")
        if emp_input:
            st.session_state.employee_name = emp_input.strip().upper()
            update_employee_file_paths()  # السطر المكمل المستهدف لإعادة استدعاء جرد الموظف القديم #
            st.rerun()

# --- 2. دالة حفظ المسحات المطورة: تحفظ القراءات سطراً بسطر مع الاسم والتاريخ والوقت ---
def save_scan_locally(barcode):
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # التقاط تاريخ ووقت المسحة بدقة
    emp_name = st.session_state.employee_name if st.session_state.employee_name else "UNKNOWN"
    
    # بناء السطر الجديد المنفصل تماماً للجرد التفصيلي
    new_scan_row = {
        "barcode": barcode,
        "scanned_qty": 1,
        "employee": emp_name,
        "timestamp": current_time_str
    }

    # أ) الحفظ في ملف الرفع المؤقت الخاص بالجهاز
    if os.path.exists(LOCAL_JARD_FILE):
        df_local = pd.read_csv(LOCAL_JARD_FILE)
    else:
        df_local = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
    
    df_local = pd.concat([df_local, pd.DataFrame([new_scan_row])], ignore_index=True)
    df_local.to_csv(LOCAL_JARD_FILE, index=False)

    # ب) الحفظ في ملف أرشيف الموظف المعزول (المسؤول عن عرض جدول الموظف أمام عينه)
    if os.path.exists(ARCHIVE_JARD_FILE):
        df_archive = pd.read_csv(ARCHIVE_JARD_FILE)
    else:
        df_archive = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
    
    df_archive = pd.concat([df_archive, pd.DataFrame([new_scan_row])], ignore_index=True)
    df_archive.to_csv(ARCHIVE_JARD_FILE, index=False)


# --- 3. دالة المزامنة والتجميع التراكمي الصارم (تمت المحافظة عليها كاملة دون أي تغيير برميجي يمس عملها) ---
def sync_data_to_server():
    if not os.path.exists(LOCAL_JARD_FILE):
        st.warning("⚠️ لا توجد قراءات جديدة لإرسالها. كل مسحاتك الحالية مزمّنة بالفعل!")
        return
        
    try:
        df_to_sync = pd.read_csv(LOCAL_JARD_FILE)
        
        if os.path.exists(SERVER_FINAL_FILE):
            df_server = pd.read_csv(SERVER_FINAL_FILE)
        else:
            # تحديث أعمدة الملف المركزي السحابي لتشمل الاسم والوقت تفصيلياً بالتاريخ
            df_server = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
            
        # دمج أسطر جرد الموظف بشكل تفصيلي وسلس داخل السيرفر لضمان فرزها لاحقاً
        df_server = pd.concat([df_server, df_to_sync], ignore_index=True)
        df_server.to_csv(SERVER_FINAL_FILE, index=False)
        
        st.success("⚡ تمت المزامنة اليدوية بنجاح! تم إرسال وتصدير قراءاتك المسجلة باسمك ووقتك للتجميع النهائي.")
        os.remove(LOCAL_JARD_FILE)
        
    except Exception as e:
        st.error(f"❌ فشلت المزامنة. الخطأ: {e}")

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
        # تحقق ذكي: إذا كانت البيانات فارغة حالياً، نضعها وننعش المتصفح فوراً لإظهار الاسم واللوحة الجانبية
        if st.session_state.master_data is None:
            st.session_state.master_data = df_upload
            st.rerun()
        else:
            st.session_state.master_data = df_upload
            
        st.success("🎯 تم تحميل ملف النظام المرجعي بنجاح!")
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

# --- القسم الرابع: واجهات وطرق الإدخال الثلاث الذكية (نسخة البرق بنصف ثانية حماية) ---
if st.session_state.master_data is not None and st.session_state.employee_name:
    st.markdown("---")
    st.subheader("🔦 مركز الإدخال الموحد")

    scanned_input = ""
    current_suffix = str(st.session_state.input_counter)
    
    import time
    if "last_cam_scan_time" not in st.session_state:
        st.session_state.last_cam_scan_time = 0.0
        
    if "cam_keep_alive" not in st.session_state:
        st.session_state.cam_keep_alive = False

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

    # 3. خيار كاميرا الجهاز البديلة (تنزيل فوري مفتوح 100% مع إنعاش الكاميرا بنصف ثانية)
    st.markdown("---")
    
    def on_camera_toggle():
        st.session_state.cam_keep_alive = st.session_state.enable_camera_checkbox_jard

    enable_camera = st.checkbox(
        "📸 تفعيل كاميرا الجوال كقارئ باركود احتياطي", 
        value=st.session_state.cam_keep_alive,
        key="enable_camera_checkbox_jard",
        on_change=on_camera_toggle
    )
    
    if st.session_state.cam_keep_alive:
        current_time = time.time()
        elapsed_time = current_time - st.session_state.last_cam_scan_time
        
        # جدار الحماية مخصص فقط وبشكل مستقل لتهيئة وإنعاش مفتاح الكاميرا برمجياً لكي لا ترمش بصرياً
        if elapsed_time < 0.1:
            from streamlit_qrcode_scanner import qrcode_scanner
            # إبقاء الشاشة حية ومستمرة أثناء معالجة التنزيل في الخلفية
            qrcode_scanner(key=f"live_scanner_hold_{current_suffix}")
        else:
            st.markdown("<p style='color: #008000; text-align: center; font-weight: bold;'>🟢 السكنر نشط... وجه العدسة نحو الباركود لقرائته بسرعة البرق</p>", unsafe_allow_html=True)
            
            from streamlit_qrcode_scanner import qrcode_scanner
            scanned_code = qrcode_scanner(key=f"live_scanner_active_{current_suffix}")
            
            if scanned_code:
                # التقاط الكود فوراً وتمريره دون أي إعاقة أو قيود زمنية على التنزيل
                scanned_input = str(scanned_code).strip().upper()
                st.session_state.last_cam_scan_time = time.time()

    # --- نظام معالجة البيانات الفوري اللحظي وتجديد العداد لإنعاش الشاشة والجدول بالأسفل ---
    if scanned_input:
        # إلغاء جدار الحماية هنا تماماً للتنزيل والحفظ الفوري أوفلاين في أجزاء من الملي ثانية
        save_scan_locally(scanned_input)
        st.toast(f"📥 تم التقاط وقراءة الكود بنجاح: {scanned_input}")
        
        # تجديد العداد برمجياً لتصفير حقل الكاميرا والخانات للمسحة القادمة فوراً
        st.session_state.input_counter += 1
        st.rerun()

# --- القسم الخامس: معالجة البيانات وبناء الجدول ومركز التصحيح الذكي بجانب البحث ---
if st.session_state.master_data is not None:
    st.markdown("---")
    st.subheader("📊 جدول الجرد والمطابقة الفوري")

    EMP_SUFFIX = str(st.session_state.employee_name).strip().upper() if st.session_state.employee_name else "TEMP_GUEST"
    LOCAL_JARD_FILE = f"local_jard_{EMP_SUFFIX}.csv"       
    ARCHIVE_JARD_FILE = f"archive_jard_{EMP_SUFFIX}.csv"   

    # 1. قراءة جرد الموظف المعزول والحركات
    if os.path.exists(ARCHIVE_JARD_FILE):
        df_local_scans = pd.read_csv(ARCHIVE_JARD_FILE)
    else:
        df_local_scans = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])

    # 2. بناء الأسطر المفرزة والمفككة للمطابقة
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
    
    # تأمين وتطهير الأعمدة المحاسبية المرجعية
    for col in ["الباركود", "اللون", "القياس", "الكمية_الأصلية", "رمز المادة"]:
        if col not in df_final.columns:
            df_final[col] = df_final.get(col, 0 if col=="الكمية_الأصلية" else "")

    def clean_excel_text_fields(val):
        val_str = str(val).strip().upper()
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        if val_str in ["NONE", "NAN", "N/A", "NULL"]:
            return ""
        return val_str

    df_final["الباركود"] = df_final["الباركود"].astype(str).str.strip().str.upper()
    df_final["اللون"] = df_final["اللون"].apply(clean_excel_text_fields)
    df_final["القياس"] = df_final["القياس"].apply(clean_excel_text_fields)
    df_final["الكمية_المجرودة"] = 0

    # تجميع الكميات الشخصية المقروءة للموظف
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

    # --- 🏗️ تقسيم وتوزيع الواجهة بجانب بعضها البعض كما في صورتك تماماً ---
    col_layout1, col_layout2 = st.columns([2, 1])
    
    with col_layout1:
        # خانة البحث السريع المعتادة مع خيارات الفرز
        search_query = st.text_input("🔍 خانة البحث السريع (رمز المادة، الباركود، اللون):", key="table_search_query")
        filter_mode = st.radio("🎛️ وضع العرض المفضّل للجدول:", ["عرض الجدول كاملاً", "عرض السطر الأخير المقروء فقط"], horizontal=True)

    with col_layout2:
        # 🌟 مركز تصحيح وتعديل الكميات الفوري المطلوب بجانب البحث
        st.markdown("<p style='color: #1B2A47; font-weight: bold; margin-bottom: 2px;'>⚙️ مركز تعديل وتصحيح الكمية</p>", unsafe_allow_html=True)
        edit_barcode = st.text_input("📝 اكتب كود المادة كاملاً للتصحيح:", key="edit_barcode_input_field", placeholder="مثال: WA049606...")
        edit_qty = st.number_input("🔢 الكمية المجرودة الصحيحة حالياً:", min_value=0, value=0, step=1, key="edit_qty_input_field")
        
        if st.button("✅ اعتماد وتعديل الكمية فورا", type="primary", use_container_width=True):
            if edit_barcode:
                target_b_clean = edit_barcode.strip().upper()
                
                # أ) تحديث ملف الأرشيف الخاص بالشاشة للموظف بشكل فوري وقاطع
                if os.path.exists(ARCHIVE_JARD_FILE):
                    df_arch = pd.read_csv(ARCHIVE_JARD_FILE)
                    # مسح أي قراءات سابقة لهذا الباركود واستبدالها بالكمية الجديدة الصافية
                    df_arch = df_arch[df_arch["barcode"].astype(str).str.strip().str.upper() != target_b_clean]
                    if edit_qty > 0:
                        new_arch_row = {
                            "barcode": target_b_clean, "scanned_qty": edit_qty,
                            "employee": EMP_SUFFIX, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        df_arch = pd.concat([df_arch, pd.DataFrame([new_arch_row])], ignore_index=True)
                    df_arch.to_csv(ARCHIVE_JARD_FILE, index=False)

                # ب) تحديث ملف الرفع المؤقت الخاص بهذا الموظف لمنع التكرار عند المزامنة اليدوية
                if os.path.exists(LOCAL_JARD_FILE):
                    df_loc = pd.read_csv(LOCAL_JARD_FILE)
                    df_loc = df_loc[df_loc["barcode"].astype(str).str.strip().str.upper() != target_b_clean]
                    if edit_qty > 0:
                        new_loc_row = {
                            "barcode": target_b_clean, "scanned_qty": edit_qty,
                            "employee": EMP_SUFFIX, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        df_loc = pd.concat([df_loc, pd.DataFrame([new_loc_row])], ignore_index=True)
                    df_loc.to_csv(LOCAL_JARD_FILE, index=False)
                else:
                    if edit_qty > 0:
                        df_loc = pd.DataFrame([{
                            "barcode": target_b_clean, "scanned_qty": edit_qty,
                            "employee": EMP_SUFFIX, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        df_loc.to_csv(LOCAL_JARD_FILE, index=False)

                # ج) تحديث ملف التجميع المركزي على السيرفر (إذا كان الموظف قد ضغط سابقاً على المزامنة اليدوية)
                SERVER_FINAL_FILE = "server_central_jard.csv"
                if os.path.exists(SERVER_FINAL_FILE):
                    df_srv = pd.read_csv(SERVER_FINAL_FILE)
                    # فلترة وتنظيف أسطر هذا الباركود الخاص بهذا الموظف تحديداً دون المساس بقراءات زملائه الآخرين
                    mask_srv_clean = ~(
                        (df_srv["barcode"].astype(str).str.strip().str.upper() == target_b_clean) & 
                        (df_srv["employee"].astype(str).str.strip().str.upper() == EMP_SUFFIX)
                    )
                    df_srv = df_srv[mask_srv_clean]
                    if edit_qty > 0:
                        new_srv_row = {
                            "barcode": target_b_clean, "scanned_qty": edit_qty,
                            "employee": EMP_SUFFIX, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        df_srv = pd.concat([df_srv, pd.DataFrame([new_srv_row])], ignore_index=True)
                    df_srv.to_csv(SERVER_FINAL_FILE, index=False)

                st.success(f"⚙️ تم تعديل وتثبيت كمية القطعة {target_b_clean} لتصبح {edit_qty} قطة بنجاح!")
                st.rerun()
            else:
                st.error("⚠️ يرجى كتابة كود المادة كاملاً أولاً لتتمكن من التعديل.")

    # تطبيق البحث السريع المعتاد والفرز على الجدول السفلي
    if search_query:
        search_query = search_query.strip().upper()
        df_final = df_final[
            df_final["الباركود"].astype(str).str.contains(search_query, case=False, na=False) |
            df_final["اللون"].astype(str).str.contains(search_query, case=False, na=False) |
            df_final["رمز المادة"].astype(str).str.contains(search_query, case=False, na=False)
        ]

    if filter_mode == "عرض السطر الأخير المقروء فقط" and os.path.exists(ARCHIVE_JARD_FILE) and len(df_local_scans) > 0:
        last_scanned_raw = str(df_local_scans.iloc[-1]["barcode"])
        last_b, last_c, last_s = parse_scanned_barcode(last_scanned_raw)
        df_final = df_final[
            (df_final["الباركود"].astype(str) == last_b) &
            (df_final["اللون"].astype(str) == last_c) &
            (df_final["القياس"].astype(str) == last_s)
        ]

    # دالة التلوين المعتمدة الذكية لأسطر الجدول الثابتة والمحفوظة كاملة
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

    # وضع فاصل جمالي وأزرار التحكم بالبيانات أوفلاين (محمية ومحاذية داخل نطاق البيانات المرجعية)
    st.markdown("---")
    col_control1, col_control2 = st.columns(2)
    
    with col_control1:
        # هذا الزر المحمي الذي يرسل ويجمع تراكمياً فقط عند الضغط عليه يدوياً
        if st.button("⚡ تفعيل المزامنة اليدوية ودمج الجرد السحابي", type="primary", use_container_width=True, key="final_sync_manual_btn"):
            sync_data_to_server()
            st.rerun()
            
    with col_control2:
        # زر التصفير الشخصي الذكي: يطهر جهاز الموظف الحالي ويحذف بياناته فقط من السيرفر دون لمس زملائه
        if st.button("🗑️ مسح قراءات الجرد الحالية والبدء من جديد", type="secondary", use_container_width=True, key="final_reset_jard_btn"):
            # 1. تحديد اسم الموظف الحالي بدقة
            EMP_NAME_TO_CLEAN = str(st.session_state.employee_name).strip().upper() if st.session_state.employee_name else "TEMP_GUEST"
            
            CURRENT_LOCAL = f"local_jard_{EMP_NAME_TO_CLEAN}.csv"
            CURRENT_ARCHIVE = f"archive_jard_{EMP_NAME_TO_CLEAN}.csv"
            SERVER_FINAL_FILE = "server_central_jard.csv"
            
            # 2. حذف ملفات هذا الموظف المحلية من الجهاز (الرفع والأرشيف) ليتصفر جدوله أمامه
            if os.path.exists(CURRENT_LOCAL):
                os.remove(CURRENT_LOCAL)
            if os.path.exists(CURRENT_ARCHIVE):
                os.remove(CURRENT_ARCHIVE)
                
            # 3. صمام أمان السيرفر المشترك: قراءة ملف التجميع المركزي لحذف بيانات هذا الموظف فقط
            if os.path.exists(SERVER_FINAL_FILE):
                try:
                    df_server = pd.read_csv(SERVER_FINAL_FILE)
                    if "employee" in df_server.columns:
                        df_server_cleaned = df_server[df_server["employee"].astype(str).str.strip().str.upper() != EMP_NAME_TO_CLEAN]
                        df_server_cleaned.to_csv(SERVER_FINAL_FILE, index=False)
                except Exception as e:
                    pass
                    
            # 4. تصفير العدادات والاسم في ذاكرة الجلسة الحالية لإعادة فتح خانة الاسم من جديد
            st.session_state.input_counter += 1
            st.session_state.employee_name = ""
            st.session_state.cam_keep_alive = False
            
            st.toast(f"🔄 تم تصفير جردك الشخصي وتطهير بياناتك من السيرفر بنجاح! جرد زملائك آمن تماماً.")
            st.rerun()

# --- القسم السادس: دالة توليد وتصدير ملف الإكسل الملون ذو الصفحات المتعددة (نسخة فرز الموظفين) ---
def generate_excel_report(df_report):
    # تأمين وتعبئة الصفر تلقائياً في حال لم يتم جرد المادة لتكون البيانات دقيقة 1000%
    df_report["الكمية_المجرودة"] = pd.to_numeric(df_report["الكمية_المجرودة"], errors="coerce").fillna(0).astype(int)
    df_report["الفرق"] = pd.to_numeric(df_report["الفرق"], errors="coerce").fillna(0).astype(int)
    df_report["الكمية_الأصلية"] = pd.to_numeric(df_report["الكمية_الأصلية"], errors="coerce").fillna(0).astype(int)

    output = io.BytesIO()
    wb = openpyxl.Workbook()
    
    fill_red = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")     # نقص
    fill_green = PatternFill(start_color="E6F9E6", end_color="E6F9E6", fill_type="solid")   # زيادة
    fill_yellow = PatternFill(start_color="FFF9E6", end_color="FFF9E6", fill_type="solid")  # مطابقة
    fill_header = PatternFill(start_color="1B2A47", end_color="1B2A47", fill_type="solid")  # كحلي للعناوين
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")   # أبيض فاصل

    # ----------------------------------------------------
    # الورقة الأولى: الجرد الكامل الموحد (لم تُمس ومحمية 100%)
    # ----------------------------------------------------
    ws1 = wb.active
    ws1.title = "الجرد الكامل الموحد"
    
    headers = list(df_report.columns)
    # تنظيف العناوين المارة للورقة الأولى لكي لا تظهر أعمدة الاسم والوقت في الجدول العام
    clean_headers = [h for h in headers if h not in ["employee", "timestamp"]]
    ws1.append(clean_headers)
    
    for col_num in range(1, len(clean_headers) + 1):
        cell = ws1.cell(row=1, column=col_num)
        cell.fill = fill_header
        cell.font = openpyxl.styles.Font(color="FFFFFF", bold=True)
    
    for _, row in df_report.iterrows():
        # استخراج البيانات الأساسية فقط للورقة الأولى
        row_data = [row[h] for h in clean_headers]
        ws1.append(row_data)
        curr_row = ws1.max_row
        
        orig = row["الكمية_الأصلية"]
        jard = row["الكمية_المجرودة"]
        diff = row["الفرق"]
        
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
    # الورقة الثانية: الفروقات والأخطاء (لم تُمس ومحمية 100%)
    # ----------------------------------------------------
    ws2 = wb.create_sheet(title="الفروقات والأخطاء")
    
    df_shortages = df_report[df_report["الفرق"] < 0].copy() # النقص
    df_excess = df_report[df_report["الفرق"] > 0].copy()    # الزيادة
    
    num_cols = len(clean_headers)    
    sep_col = num_cols + 1           
    start_left_table = sep_col + 1   
    
    ws2.cell(row=1, column=1, value="⚠️ جداول النقص (الجانب الأيمن)").font = openpyxl.styles.Font(bold=True, size=12, color="850000")
    ws2.cell(row=1, column=start_left_table, value="✨ جداول الزيادة والمستجدات (الجانب الأيسر)").font = openpyxl.styles.Font(bold=True, size=12, color="008000")
    
    ws2.cell(row=1, column=sep_col, value="").fill = fill_white
    ws2.cell(row=2, column=sep_col, value="").fill = fill_white
    
    for col_idx, h_text in enumerate(clean_headers, start=1):
        c_right = ws2.cell(row=2, column=col_idx, value=h_text)
        c_right.fill = fill_header
        c_right.font = openpyxl.styles.Font(color="FFFFFF", bold=True)
        
        c_left = ws2.cell(row=2, column=col_idx + start_left_table - 1, value=h_text)
        c_left.fill = fill_header
        c_left.font = openpyxl.styles.Font(color="FFFFFF", bold=True)

    r_idx = 3
    for _, row in df_shortages.iterrows():
        row_data = [row[h] for h in clean_headers]
        for c_idx, val in enumerate(row_data, start=1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.fill = fill_red
        ws2.cell(row=r_idx, column=sep_col, value="").fill = fill_white  
        r_idx += 1
        
    r_idx_l = 3
    for _, row in df_excess.iterrows():
        row_data = [row[h] for h in clean_headers]
        for c_idx, val in enumerate(row_data, start=start_left_table):
            cell = ws2.cell(row=r_idx_l, column=c_idx, value=val)
            cell.fill = fill_green
        ws2.cell(row=r_idx_l, column=sep_col, value="").fill = fill_white  
        r_idx_l += 1

    # ----------------------------------------------------
    # 🌟 الإضافة المطلوبة: توليد صفحات الموظفين المستقلة (تبدأ من الصفحة الثالثة)
    # ----------------------------------------------------
    if os.path.exists("server_central_jard.csv"):
        df_central = pd.read_csv("server_central_jard.csv")
        
        # التأكد من وجود بيانات الموظفين والوقت وتصنيفها
        if "employee" in df_central.columns and "timestamp" in df_central.columns:
            # استخراج قائمة بأسماء الموظفين الفريدين الذين شاركوا في الجرد
            unique_employees = df_central["employee"].unique()
            
            for emp in unique_employees:
                # إنشاء ورقة إكسل منفصلة لكل موظف تحمل اسمه صراحة
                ws_emp = wb.create_sheet(title=f"جرد الموظف - {str(emp)[:15]}")
                
                # كتابة عنوان الصفحة التفصيلي الكبير
                ws_emp.cell(row=1, column=1, value=f"📋 سجل المسحات التفصيلي للموظف: {emp}").font = openpyxl.styles.Font(bold=True, size=12, color="1B2A47")
                
                # هيدر الأعمدة التفصيلي لصفحة الموظف (قراءة متتالية تاريخية سطراً بسطر)
                emp_headers = ["الباركود المقروء", "الكمية الممسوحة", "تاريخ ووقت القراءة المباشر"]
                ws_emp.append([]) # ترحيل السطر الثاني ليكون فارغاً جمالياً
                ws_emp.append(emp_headers)
                
                # تلوين هيدر صفحة الموظف باللون الكحلي المميز لشركتك
                for col_num in range(1, len(emp_headers) + 1):
                    cell = ws_emp.cell(row=3, column=col_num)
                    cell.fill = fill_header
                    cell.font = openpyxl.styles.Font(color="FFFFFF", bold=True)
                
                # فلترة وسحب مسحات هذا الموظف فقط وترتيبها تصاعدياً حسب الوقت والتاريخ
                df_emp_data = df_central[df_central["employee"] == emp].sort_values(by="timestamp", ascending=True)
                
                # ضخ البيانات تفصيلياً؛ حتى لو جرد قطعتين من نفس الباركود ستنزل في سطرين منفصلين ومفصلين بالوقت
                for _, r_data in df_emp_data.iterrows():
                    ws_emp.append([
                        str(r_data["barcode"]).strip().upper(),
                        int(r_data["scanned_qty"]),
                        str(r_data["timestamp"])
                    ])
                    
                    # تلوين أسطر الموظف بلون المطابقة الخفيف لإعطاء مظهر متناسق ومريح للعين
                    curr_emp_row = ws_emp.max_row
                    for cell in ws_emp[curr_emp_row]:
                        cell.fill = fill_yellow

    wb.save(output)
    return output.getvalue()

# --- طريقة عرض زر تحميل التقرير الختامي في الواجهة للمسؤول ---
# --- القسم السادس والأخير: زر تحميل التقرير الختامي الموحد لجميع الأطراف (للمسؤول) ---
if st.session_state.master_data is not None:
    st.markdown("---")
    st.subheader("📊 تصدير التقرير الختامي العام")
    
    # زر جانبي يتيح للمسؤول توليد التقرير من الملف المركزي السحابي المجمع
    if st.button("🔄 تحديث وقراءة الجرد المجمع لكافة الأطراف"):
        if os.path.exists("server_central_jard.csv"):
            df_server_central = pd.read_csv("server_central_jard.csv")
            
            # بناء جدول المطابقة النهائي الشامل لكل الأطراف معاً
            df_final_report = st.session_state.master_data.copy()
            
            # تنظيف الأعمدة وتأمينها
            for col in ["الباركود", "اللون", "القياس", "الكمية_الأصلية", "رمز المادة"]:
                if col not in df_final_report.columns:
                    df_final_report[col] = df_final_report.get(col, 0 if col=="الكمية_الأصلية" else "")
            
            df_final_report["الباركود"] = df_final_report["الباركود"].astype(str).str.strip().str.upper()
            df_final_report["اللون"] = df_final_report["اللون"].apply(clean_excel_text_fields)
            df_final_report["القياس"] = df_final_report["القياس"].apply(clean_excel_text_fields)
            df_final_report["الكمية_المجرودة"] = 0
            
            # دمج القراءات المجمعة من السيرفر
            for idx, scan in df_server_central.iterrows():
                # تفكيك الباركود المركزي للمطابقة الثلاثية الصارمة
                b_code, c_name, s_val = parse_scanned_barcode(scan["barcode"])
                
                mask = (
                    (df_final_report["الباركود"] == b_code) & 
                    (df_final_report["اللون"] == c_name) & 
                    (df_final_report["القياس"] == s_val)
                )
                
                if mask.any():
                    df_final_report.loc[mask, "الكمية_المجرودة"] += int(scan["scanned_qty"])
                else:
                    new_item = {col: "" for col in df_final_report.columns}
                    new_item["الباركود"] = b_code
                    new_item["اللون"] = c_name
                    new_item["القياس"] = s_val
                    new_item["الكمية_الأصلية"] = 0
                    new_item["الكمية_المجرودة"] = int(scan["scanned_qty"])
                    df_final_report = pd.concat([df_final_report, pd.DataFrame([new_item])], ignore_index=True)
            
            # حساب الفروقات الختامية
            df_final_report["الكمية_الأصلية"] = pd.to_numeric(df_final_report["الكمية_الأصلية"], errors="coerce").fillna(0).astype(int)
            df_final_report["الكمية_المجرودة"] = pd.to_numeric(df_final_report["الكمية_المجرودة"], errors="coerce").fillna(0).astype(int)
            df_final_report["الفرق"] = df_final_report["الكمية_المجرودة"] - df_final_report["الكمية_الأصلية"]
            
            # توليد وإتاحة ملف الإكسل الملون ذو الصفحتين للتحميل فوراً
            excel_data = generate_excel_report(df_final_report)
            st.download_button(
                label="📥 تحميل تقرير الجرد الختامي الملوّن المجمع (Excel)",
                data=excel_data,
                file_name="Torino_Final_Muted_Jard_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="central_download_excel_btn"
            )
        else:
            st.info("ℹ️ لا توجد بيانات مجمعة سحابياً من الأطراف حتى الآن لتوليد التقرير الختامي.")
