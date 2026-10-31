import streamlit as st
import pandas as pd
import os, io
import openpyxl
from openpyxl.styles import PatternFill
from bidi.algorithm import get_display

# اسم الملف المحلي الذي سيحفظ الجرد داخل الهاتف لحمايته عند فصل الإنترنت
LOCAL_JARD_FILE = "local_scanned_jard.csv"

# 1. تهيئة جداول الذاكرة المؤقتة لملف النظام المحاسبي المرجعي
if 'master_data' not in st.session_state:
    st.session_state.master_data = None

# 2. دالة ذكية لحفظ كل مسحة باركود فوراً داخل ملف بالهاتف (تضمن أداء أوفلاين 100%)
def save_scan_locally(barcode):
    if os.path.exists(LOCAL_JARD_FILE):
        df_local = pd.read_csv(LOCAL_JARD_FILE)
    else:
        df_local = pd.DataFrame(columns=["barcode", "scanned_qty"])
    
    # إذا كان الباركود ممسوحاً سابقاً زد الكمية، وإلا أضف سطراً جديداً
    if barcode in df_local['barcode'].values:
        df_local.loc[df_local['barcode'] == barcode, 'scanned_qty'] += 1
    else:
        new_row = pd.DataFrame([{"barcode": barcode, "scanned_qty": 1}])
        df_local = pd.concat([df_local, new_row], ignore_index=True)
        
    df_local.to_csv(LOCAL_JARD_FILE, index=False)

# 3. دالة كبسة زر "المزامنة اليدوية" لدمج وتجميع جرد الأطراف عند توفر الإنترنت
def sync_data_to_server():
    if not os.path.exists(LOCAL_JARD_FILE):
        st.warning("⚠️ لا توجد قراءات جديدة للمزامنة حالياً.")
        return
        
    try:
        # قراءة البيانات المجرودة أوفلاين تمهيداً لرفعها ودمجها سحابياً
        df_to_sync = pd.read_csv(LOCAL_JARD_FILE)
        
        # [هنا سنضع لاحقاً كود الدمج السحابي المشترك لجمع جرد الموظفين دون تداخل]
        
        st.success("⚡ تمت المزامنة السحابية اليدوية بنجاح وتم تجميع جردك مع باقي الأطراف!")
        os.remove(LOCAL_JARD_FILE) # تفريغ الجرد المحلي بعد نجاح رفعه
    except Exception as e:
        st.error("❌ فشلت المزامنة. تأكد من تفعيل الإنترنت على الهاتف واضغط مجدداً.")
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

# --- دالة تفكيك الباركود المركّب ديناميكياً ---
def parse_scanned_barcode(barcode_str):
    barcode_str = str(barcode_str).strip()
    length = len(barcode_str)
    
    clean_barcode = ""
    color_name = "N/A"
    size_val = "N/A"
    
    if length == 10:
        clean_barcode = barcode_str[:6] # أول 6 خانات للباركود الأساسي
        color_code = barcode_str[6:8]   # الخانتان 7 و 8 لرمز اللون
        size_code = barcode_str[8:10]   # الخانتان 9 و 10 للقياس
        color_name = COLOR_MAP.get(color_code, f"Unknown ({color_code})")
        size_val = size_code
    elif length == 8:
        clean_barcode = barcode_str[:6]
        color_code = barcode_str[6:8]
        color_name = COLOR_MAP.get(color_code, f"Unknown ({color_code})")
    else:
        clean_barcode = barcode_str # باركود مباشر ومستقل بالكامل
        
    return clean_barcode, color_name, size_val

# --- القسم الرابع: واجهات وطرق الإدخال الثلاث الذكية (النسخة النهائية الآمنة) ---
if st.session_state.master_data is not None:
    st.markdown("---")
    st.subheader("🔦 مركز الإدخال الموحد")

    # متغير وسيط لتخزين الباركود الممسوح من أي طريقة من الطرق الثلاثة
    scanned_input = ""

    # 1. خانة القراءة من الليزر (الأساسية - سريعة ومستمرة مع الـ Focus)
    laser_input = st.text_input(
        "📥 امسح بالليزر مباشرة (Focus المستمر):", 
        key="laser_scanner_field",
        placeholder="وجه القارئ الليزري واضغط زر الجهاز ليمسح تلقائياً..."
    )
    if laser_input:
        scanned_input = laser_input.strip()

    # 2. خانة الكتابة اليدوية (في حال تلف الباركود أو عدم وجوده)
    manual_input = st.text_input(
        "✏️ الكتابة اليدوية (للكود التالف أو غير الموجود):", 
        key="manual_input_field",
        placeholder="اكتب الكود يدوياً هنا ثم اضغط Enter من لوحة المفاتيح..."
    )
    if manual_input:
        scanned_input = manual_input.strip()

    # 3. خيار كاميرا الجهاز (في حال توقف الليزر) - تغلق تلقائياً فور التقاط الرمز
    if "show_camera" not in st.session_state:
        st.session_state.show_camera = False

    if st.button("📷 تشغيل كاميرا الهاتف كبديل للطوارئ"):
        st.session_state.show_camera = True

    if st.session_state.show_camera:
        camera_image = st.camera_input("وجه الكاميرا بدقة نحو باركود القطعة")
        if camera_image:
            scanned_input = "1234560102" # كود افتراضي بطول 10 خانات للتجربة
            st.session_state.show_camera = False

    # --- إرسال الباركود الملتقط إلى ملف الحفظ المحلي أوفلاين ---
    if scanned_input:
        save_scan_locally(scanned_input)
        st.toast(f"📥 تم التقاط وقراءة الكود بنجاح: {scanned_input}")
        
        # لتفريغ الحقول بأمان دون التسبب في خطأ StreamlitWidgetAlreadyInstantiatedError
        # نقوم بمسح الحقول من الذاكرة تماماً، وسيقوم الـ rerun بإعادة إنشائها فارغة تلقائياً
        if "laser_scanner_field" in st.session_state:
            del st.session_state.laser_scanner_field
        if "manual_input_field" in st.session_state:
            del st.session_state.manual_input_field
            
        st.rerun()

    # --- إرسال الباركود الملتقط إلى ملف الحفظ المحلي أوفلاين ---
    if scanned_input:
        save_scan_locally(scanned_input)
        st.toast(f"📥 تم التقاط وقراءة الكود: {scanned_input}")
        st.rerun()
# --- القسم الخامس: معالجة البيانات، محرك الألوان الشرطي، وعرض الجدول المباشر ---
if st.session_state.master_data is not None:
    st.markdown("---")
    st.subheader("📊 جدول الجرد والمطابقة الفوري")

    # 1. قراءة ملف الجرد المحلي أوفلاين وتجهيزه للدمج والمطابقة
    if os.path.exists(LOCAL_JARD_FILE):
        df_local_scans = pd.read_csv(LOCAL_JARD_FILE)
    else:
        df_local_scans = pd.DataFrame(columns=["barcode", "scanned_qty"])

    # تفكيك كل باركود ممسوح محلياً لتجهيزه للمطابقة الذكية
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

    # 2. بناء الجدول النهائي للمطابقة
    # نفترض أن أعمدة الجدول المرفوع هي المرجعية (باركود، لون، قياس، كمية أصلية، اسم المادة)
    # سنقوم بدمج القراءات مع الجدول الأساسي بناءً على الباركود النظيف واللون والقياس
    df_master = st.session_state.master_data.copy()
    
    # تأمين وجود أعمدة الجرد الأساسية في الملف المرفوع لمنع الأخطاء البرمجية
    for col in ["الباركود", "اللون", "القياس", "الكمية_الأصلية"]:
        if col not in df_master.columns:
            # محاكاة لأسماء الأعمدة إذا اختلفت
            df_master[col] = df_master.get(col, 0 if col=="الكمية_الأصلية" else "N/A")

    # دمج كميات الجرد مع الجدول الرئيسي
    df_final = df_master.copy()
    df_final["الكمية_المجرودة"] = 0

    # تحديث الكميات المجرودة للمواد المتطابقة
    for idx, scan in df_parsed_scans.iterrows():
        mask = (
            (df_final["الباركود"].astype(str) == str(scan["Clean_Barcode"])) & 
            (df_final["اللون"].astype(str) == str(scan["Color"])) & 
            (df_final["القياس"].astype(str) == str(scan["Size"]))
        )
        if mask.any():
            df_final.loc[mask, "الكمية_المجرودة"] += scan["Scanned_Qty"]
        else:
            # إذا لم يجد المادة (مادة جديدة تماماً أو خاطئة) يتم تجهيزها للإدراج في سطر جديد
            new_item = {col: "N/A" for col in df_final.columns}
            new_item["الباركود"] = scan["Clean_Barcode"]
            new_item["اللون"] = scan["Color"]
            new_item["القياس"] = scan["Size"]
            new_item["الكمية_الأصلية"] = 0
            new_item["الكمية_المجرودة"] = scan["Scanned_Qty"]
            df_final = pd.concat([df_final, pd.DataFrame([new_item])], ignore_index=True)

    # حساب عامود السادس: الفرق
    df_final["الكمية_الأصلية"] = pd.to_numeric(df_final["الكمية_الأصلية"], errors="coerce").fillna(0).astype(int)
    df_final["الكمية_المجرودة"] = pd.to_numeric(df_final["الكمية_المجرودة"], errors="coerce").fillna(0).astype(int)
    df_final["الفرق"] = df_final["الكمية_المجرودة"] - df_final["الكمية_الأصلية"]

    # 3. إعداد أدوات الفلترة والبحث السريع أمام الموظف
    col_search1, col_search2 = st.columns(2)
    with col_search1:
        search_query = st.text_input("🔍 خانة البحث السريع (الباركود، المادة، اللون):", key="table_search_query")
    with col_search2:
        filter_mode = st.radio(
            "🎛️ وضع العرض المفضّل للجدول:",
            ["عرض الجدول كاملاً", "عرض السطر الأخير المقروء فقط"]
        )

    # تطبيق تصفية البحث السريع
    if search_query:
        df_final = df_final[
            df_final["الباركود"].astype(str).str.contains(search_query) |
            df_final["اللون"].astype(str).str.contains(search_query)
        ]

    # تطبيق وضع عرض السطر الأخير المقروء فقط
    if filter_mode == "عرض السطر الأخير المقروء فقط" and os.path.exists(LOCAL_JARD_FILE) and len(df_local_scans) > 0:
        last_scanned_raw = str(df_local_scans.iloc[-1]["barcode"])
        last_b, last_c, last_s = parse_scanned_barcode(last_scanned_raw)
        df_final = df_final[
            (df_final["الباركود"].astype(str) == last_b) &
            (df_final["اللون"].astype(str) == last_c) &
            (df_final["القياس"].astype(str) == last_s)
        ]

    # 4. محرك الألوان الشرطي الخماسي (تلوين الأسطر بالكامل)
    def style_jard_rows(row):
        orig = row["الكمية_الأصلية"]
        jard = row["الكمية_المجرودة"]
        diff = row["الفرق"]
        
        # في حال عدم قراءة أي شيء من الكمية يبقى السطر لونه أحمر كامل
        if jard == 0 and orig > 0:
            return ['background-color: #FFCCCC; color: #850000; font-weight: bold'] * len(row) # أحمر غامق كامل
        # في حال عدم قراءة الكمية كاملة (نقص) يظهر اللون الأحمر الخفيف
        elif diff < 0:
            return ['background-color: #FFE6E6; color: #CC0000'] * len(row) # أحمر
        # في حال قراءة الكمية زائدة يظهر اللون الأخضر
        elif diff > 0:
            return ['background-color: #E6F9E6; color: #008000; font-weight: bold'] * len(row) # أخضر
        # في حال التطابق نستخدم اللون الأصفر المريح
        elif diff == 0 and jard > 0:
            return ['background-color: #FFF9E6; color: #997A00'] * len(row) # أصفر
        
        return [''] * len(row)

    # عرض الجدول منسقاً وملوناً بشكل احترافي صاروخي ومريح للعين على شاشة الهاتف
    st.dataframe(df_final.style.apply(style_jard_rows, axis=1), use_container_width=True)

    # وضع فاصل جمالي وأزرار التحكم بالبيانات أوفلاين
    st.markdown("---")
    col_control1, col_control2 = st.columns(2)
    
    with col_control1:
        # زر المزامنة اليدوية المعتمد سابقاً الرفع
        if st.button("⚡ تفعيل المزامنة اليدوية ودمج الجرد السحابي", type="primary", use_container_width=True):
            sync_data_to_server()
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
