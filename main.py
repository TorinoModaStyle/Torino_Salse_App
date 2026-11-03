import flet as ft  # type: ignore[reportMissingImports]
import pandas as pd
import os
import io
from datetime import datetime

# --- 1. تهيئة مسارات ملفات الجرد الشخصية للموظفين والمزامنة السحابية أوفلاين ---
# المتغيرات العامة للمشروع والملفات المحلية المحفوظة بالكامل في ذاكرة فلاش الهاتف الداخلي
MASTER_DATA_FILE = "master_data_reference.xlsx"
LOCAL_JARD_FILE = ""
ARCHIVE_JARD_FILE = ""
SERVER_FINAL_FILE = "server_central_jard.csv"

# الذاكرة المؤقتة لمحرك البرنامج الداخلي لحفظ حالة الجلسة أوفلاين
class AppState:
    master_df = None       # جدول البيانات المرجعي المحاسبي للشركة
    employee_name = ""     # اسم الموظف الحالي المسؤول عن الجهاز
    input_counter = 0      # عداد الإنعاش الذاتي للحقول

state = AppState()

# دالة تحديث المسارات لربط ملفات الجرد باسم الموظف المكتوب لمنع ضياع البيانات واستعادتها أوفلاين
def update_employee_file_paths(emp_name):
    global LOCAL_JARD_FILE, ARCHIVE_JARD_FILE
    suffix = str(emp_name).strip().upper() if emp_name else "TEMP_GUEST"
    LOCAL_JARD_FILE = f"local_jard_{suffix}.csv"
    ARCHIVE_JARD_FILE = f"archive_jard_{suffix}.csv"

# --- 2. دالة حفظ المسحات المطورة والمحمية بالتاريخ والوقت سطراً بسطر أوفلاين ---
def save_scan_locally(barcode):
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emp = state.employee_name if state.employee_name else "UNKNOWN"
    
    new_scan_row = {
        "barcode": barcode,
        "scanned_qty": 1,
        "employee": emp,
        "timestamp": current_time_str
    }
    
    update_employee_file_paths(emp)
    
    # أ) الحفظ الصارم في ملف الرفع المؤقت الخاص بجهاز الموظف أوفلاين
    if os.path.exists(LOCAL_JARD_FILE):
        df_local = pd.read_csv(LOCAL_JARD_FILE)
    else:
        df_local = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
        
    df_local = pd.concat([df_local, pd.DataFrame([new_scan_row])], ignore_index=True)
    df_local.to_csv(LOCAL_JARD_FILE, index=False)

    # ب) الحفظ الصارم في ملف أرشيف شاشة الموظف لاستعادة الجرد فوراً
    if os.path.exists(ARCHIVE_JARD_FILE):
        df_archive = pd.read_csv(ARCHIVE_JARD_FILE)
    else:
        df_archive = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
        
    df_archive = pd.concat([df_archive, pd.DataFrame([new_scan_row])], ignore_index=True)
    df_archive.to_csv(ARCHIVE_JARD_FILE, index=False)

# --- 3. دالة تفكيك الباركود الذكية المعتمدة لـ Torino (لم تُمَس ومحمية 100%) ---
def parse_scanned_barcode(raw_barcode):
    barcode_str = str(raw_barcode).strip().upper()
    if not barcode_str or barcode_str in ["NONE", "NAN"]:
        return "", "", ""
        
    # أ) التحقق من نمط الباركود المركب الطويل الذي يحتوي على الرمز النجمي الفاصل *
    if "*" in barcode_str:
        parts = barcode_str.split("*")
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), parts[2].strip()
            
    # ب) التحقق من النمط القياسي لـ Torino (الذي يبدأ بـ WA وينتهي بـ القياس واللون مدمجين)
    if barcode_str.startswith("WA") and len(barcode_str) >= 12:
        clean_b = barcode_str[:8]    # أول 8 خانات تمثل كود المادة الموحد
        color_p = barcode_str[8:10]   # الخانتين 9 و 10 تمثلان رمز اللون المرجعي
        size_p = barcode_str[10:]     # بقية الخانات تمثل القياس (مثل 40 أو S)
        return clean_b, color_p, size_p
        
    # ج) إذا كان باركود تقليدي أو دولي عام، يعود كما هو لخانة الباركود الصافي
    return barcode_str, "", ""

# --- 4. دالة المزامنة والتجميع التراكمي للملف المركزي السحابي ---
def sync_data_to_server():
    emp = state.employee_name if state.employee_name else "UNKNOWN"
    update_employee_file_paths(emp)
    
    if not os.path.exists(LOCAL_JARD_FILE):
        return "⚠️ لا توجد قراءات جديدة لإرسالها. كل مسحاتك مزمّنة بالفعل!"
        
    try:
        df_to_sync = pd.read_csv(LOCAL_JARD_FILE)
        
        if os.path.exists(SERVER_FINAL_FILE):
            df_server = pd.read_csv(SERVER_FINAL_FILE)
        else:
            df_server = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
            
        # دمج الأسطر بأمان تام تفصيلياً داخل قاعدة بيانات السيرفر المشتركة
        df_server = pd.concat([df_server, df_to_sync], ignore_index=True)
        df_server.to_csv(SERVER_FINAL_FILE, index=False)
        
        # تنظيف وتطهير ملف الرفع الفوري الخاص بالجهاز بعد نجاح المزامنة
        os.remove(LOCAL_JARD_FILE)
        return "⚡ تمت المزامنة بنجاح! تم إرسال وتصدير قراءاتك المسجلة للتجميع النهائي."
    except Exception as e:
        return f"❌ فشلت المزامنة. الخطأ: {e}"

# --- 6. بناء محرك واجهات الهاتف الذكي أوفلاين كلياً (دالة الواجهة الرسومية الرئيسية) ---
def main(page: ft.Page):
    # أ) صبغة الهوية البصرية الرسمية والألوان الملكية لشركة Torino على التطبيق
    page.title = "Torino Smart Inventory"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True  # توجيه الواجهة بالكامل للغة العربية من اليمين لليسار
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO
    page.window_background_color = "#FFFFFF" # خلفية بيضاء مريحة للعين

    # ب) تهيئة حقول وعناصر الواجهة الرسومية لربطها ديناميكياً
    status_text = ft.Text(value="🟢 النظام نشط ومستعد أوفلاين... يرجى رفع ملف النظام المرجعي أولاً", color="#1B2A47", size=14, weight=ft.FontWeight.BOLD)
    employee_label = ft.Text(value="👤 لم يتم تسجيل اسم الموظف بعد", color="#850000", size=14, weight=ft.FontWeight.BOLD)
    
    # حقول الإدخال الثلاثة الذكية (مغلقة ومعطلة تلقائياً في البداية لحين رفع الملف وكتابة الاسم)
    laser_input = ft.TextField(label="📥 امسح بالليزر مباشرة (Focus المستمر):", disabled=True, password=False, can_reveal_password=False, hint_text="وجه القارئ الليزري ليمسح تلقائياً...")
    manual_input = ft.TextField(label="✏️ الكتابة اليدوية للكود:", disabled=True, hint_text="اكتب الكود يدوياً هنا ثم اضغط Enter...")
    camera_checkbox = ft.Checkbox(label="📸 تفعيل كاميرا الجوال كقارئ باركود احتياطي", value=False, disabled=True)
    
    # واجهات البحث السريع والتصحيح الذكي للكميات بجانب بعضها
    search_field = ft.TextField(label="🔍 خانة البحث السريع (رمز، باركود، لون):", hint_text="اكتب للبحث الفوري في الجدول...", expand=True)
    edit_barcode_field = ft.TextField(label="📝 كود المادة للتصحيح:", hint_text="مثال: WA049606", expand=True)
    edit_qty_field = ft.TextField(label="🔢 الكمية الصحيحة:", value="0", expand=True)
    
    # عناصر عرض جدول جرد المطابقة الفوري السفلي الملون
    jard_table = ft.DataTable(
        bgcolor="#FFFFFF",
        border=ft.border.all(1, "#1B2A47"),
        border_radius=8,
        heading_row_color="#1B2A47",
        columns=[
            ft.DataColumn(ft.Text("الرمز / الباركود", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("اللون", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("القياس", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الأصلية", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("المجرودة", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الفرق", color="#FFFFFF", weight=ft.FontWeight.BOLD)),
        ],
        rows=[]
    )
    # ج) تحديث اللوحة الجانبية (Sidebar) الأنيقة لعرض بيانات الموظف وزر التغيير المريح
    def refresh_sidebar():
        page.drawer.controls.clear()
        page.drawer.controls.append(ft.Container(height=20))
        page.drawer.controls.append(
            ft.Container(
                content=ft.Text("🏆 شركة Torino للجرد المطور", size=18, weight=ft.FontWeight.BOLD, color="#1B2A47"),
                padding=15, alignment=ft.alignment.center
            )
        )
        page.drawer.controls.append(ft.Divider(color="#D4AF37", thickness=2)) # فاصل مذهب
        
        if state.employee_name:
            page.drawer.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"👤 الموظف المسؤول حالياً:\n{state.employee_name}", size=14, weight=ft.FontWeight.BOLD, color="#008000"),
                        ft.ElevatedButton("🔄 تغيير اسم الموظف", icon=ft.icons.REFRESH, bgcolor="#850000", color="#FFFFFF", on_click=lambda _: reset_employee())
                    ]), padding=15
                )
            )
            employee_label.value = f"👤 الموظف الحالي: {state.employee_name}"
            employee_label.color = "#008000"
        else:
            page.drawer.controls.append(ft.Container(content=ft.Text("⚠️ لم يتم تسجيل اسم الموظف بعد.", size=14, color="#850000", weight=ft.FontWeight.BOLD), padding=15))
            employee_label.value = "⚠️ يرجى تسجيل اسم الموظف أولاً"
            employee_label.color = "#850000"
        
        page.drawer.update()
        page.update()

    def reset_employee():
        state.employee_name = ""
        check_security_lock()
        refresh_sidebar()
        show_employee_dialog()

    # د) جدار الحماية وقفل الأمان المشترك (حظر الحقول أوتوماتيكياً حتى رفع الملف وتسجيل الاسم)
    def check_security_lock():
        is_locked = (state.master_df is None) or (not state.employee_name)
        laser_input.disabled = is_locked
        manual_input.disabled = is_locked
        camera_checkbox.disabled = is_locked
        search_field.disabled = is_locked
        edit_barcode_field.disabled = is_locked
        edit_qty_field.disabled = is_locked
        page.update()
    # هـ) محرك بناء وتحديث أسطر جدول المطابقة الفوري الملون تلقائياً أوفلاين
    def rebuild_jard_table_rows():
        if state.master_df is None:
            return
            
        emp = state.employee_name if state.employee_name else "TEMP_GUEST"
        update_employee_file_paths(emp)
        
        # قراءة الحركات والمطابقة أوفلاين بالكامل
        if os.path.exists(ARCHIVE_JARD_FILE):
            df_local_scans = pd.read_csv(ARCHIVE_JARD_FILE)
        else:
            df_local_scans = pd.DataFrame(columns=["barcode", "scanned_qty", "employee", "timestamp"])
            
        parsed_rows = []
        for _, row in df_local_scans.iterrows():
            b_code, c_name, s_val = parse_scanned_barcode(row["barcode"])
            parsed_rows.append({"Clean_Barcode": b_code, "Color": c_name, "Size": s_val, "Scanned_Qty": row["scanned_qty"]})
        df_parsed_scans = pd.DataFrame(parsed_rows)
        
        df_final = state.master_df.copy()
        df_final["الكمية_المجرودة"] = 0
        df_final["الباركود"] = df_final["الباركود"].astype(str).str.strip().str.upper()
        
        # تجميع وحساب الكميات المجرودة من فلاش الهاتف
        for _, scan in df_parsed_scans.iterrows():
            mask = (
                (df_final["الباركود"] == str(scan["Clean_Barcode"]).strip().upper()) & 
                (df_final["اللون"].astype(str).str.strip().str.upper() == str(scan["Color"]).strip().upper()) & 
                (df_final["القياس"].astype(str).str.strip().str.upper() == str(scan["Size"]).strip().upper())
            )
            if mask.any():
                df_final.loc[mask, "الكمية_المجرودة"] += scan["Scanned_Qty"]
                
        df_final["الكمية_الأصلية"] = pd.to_numeric(df_final["الكمية_الأصلية"], errors="coerce").fillna(0).astype(int)
        df_final["الكمية_المجرودة"] = pd.to_numeric(df_final["الكمية_المجرودة"], errors="coerce").fillna(0).astype(int)
        df_final["الفرق"] = df_final["الكمية_المجرودة"] - df_final["الكمية_الأصلية"]
        
        # تصفية البحث إن وُجِد
        q = search_field.value.strip().upper() if search_field.value else ""
        if q:
            df_final = df_final[
                df_final["الباركود"].astype(str).str.contains(q, case=False, na=False) |
                df_final["اللون"].astype(str).str.contains(q, case=False, na=False) |
                df_final["رمز المادة"].astype(str).str.contains(q, case=False, na=False)
            ]
            
        jard_table.rows.clear()
        for _, row in df_final.iterrows():
            orig = row["الكمية_الأصلية"]
            jard = row["الكمية_المجرودة"]
            diff = row["الفرق"]
            
            # تحديد لون السطر الذكي هندسياً لشركة Torino
            row_bg = "#FFFFFF"
            if jard == 0 and orig > 0:
                row_bg = "#FFCCCC" # نقص كامل
            elif diff < 0:
                row_bg = "#FFE6E6" # نقص جزئي
            elif diff > 0:
                row_bg = "#E6F9E6" # زيادة
            elif diff == 0 and jard > 0:
                row_bg = "#FFF9E6" # مطابقة تامة
            jard_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(row["الباركود"]))),
                        ft.DataCell(ft.Text(str(row["اللون"]))),
                        ft.DataCell(ft.Text(str(row["القياس"]))),
                        ft.DataCell(ft.Text(str(orig))),
                        ft.DataCell(ft.Text(str(jard))),
                        ft.DataCell(ft.Text(str(diff))),
                    ],
                    color=ft.colors.BLACK,
                    selected=False,
                    on_select_changed=None,
                    shading_color=row_bg
                )
            )
        page.update()

    # و) دالات الإدخال والتصحيح اللحظي وحفظ الملفات محلياً
    def handle_laser_scan(e):
        if laser_input.value:
            save_scan_locally(laser_input.value.strip().upper())
            laser_input.value = ""
            laser_input.focus()
            rebuild_jard_table_rows()
            status_text.value = "📥 تم مسح وقيد القطعة محلياً بنجاح!"
            page.update()

    def handle_manual_submit(e):
        if manual_input.value:
            save_scan_locally(manual_input.value.strip().upper())
            manual_input.value = ""
            manual_input.focus()
            rebuild_jard_table_rows()
            status_text.value = "✏️ تم تسجيل الكود اليدوي محلياً!"
            page.update()
    def apply_quantity_correction(e):
        b_target = edit_barcode_field.value.strip().upper() if edit_barcode_field.value else ""
        try:
            qty_target = int(edit_qty_field.value.strip())
        except ValueError:
            status_text.value = "⚠️ يرجى كتابة كمية صحيحة بالأرقام!"
            page.update()
            return
            
        if not b_target:
            status_text.value = "⚠️ اكتب كود المادة كاملاً أولاً!"
            page.update()
            return
            
        emp = state.employee_name if state.employee_name else "TEMP_GUEST"
        update_employee_file_paths(emp)
        
        # تعديل قاطع ومصفى داخل أرشيف الشاشة أوفلاين
        if os.path.exists(ARCHIVE_JARD_FILE):
            df_arch = pd.read_csv(ARCHIVE_JARD_FILE)
            df_arch = df_arch[df_arch["barcode"].astype(str).str.strip().str.upper() != b_target]
            if qty_target > 0:
                df_arch = pd.concat([df_arch, pd.DataFrame([{"barcode": b_target, "scanned_qty": qty_target, "employee": emp, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])], ignore_index=True)
            df_arch.to_csv(ARCHIVE_JARD_FILE, index=False)
            
        # تعديل قاطع داخل ملف الرفع الفوري للجهاز لمنع التكرار
        if os.path.exists(LOCAL_JARD_FILE):
            df_loc = pd.read_csv(LOCAL_JARD_FILE)
            df_loc = df_loc[df_loc["barcode"].astype(str).str.strip().str.upper() != b_target]
            if qty_target > 0:
                df_loc = pd.concat([df_loc, pd.DataFrame([{"barcode": b_target, "scanned_qty": qty_target, "employee": emp, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])], ignore_index=True)
            df_loc.to_csv(LOCAL_JARD_FILE, index=False)
            
        # تطهير الباركود من السيرفر المركزي لمنع الازدواجية والتجميع العشوائي للكميات القديمة
        if os.path.exists(SERVER_FINAL_FILE):
            try:
                df_srv = pd.read_csv(SERVER_FINAL_FILE)
                mask_srv = ~((df_srv["barcode"].astype(str).str.strip().str.upper() == b_target) & (df_srv["employee"].astype(str).str.strip().str.upper() == emp))
                df_srv = df_srv[mask_srv]
                if qty_target > 0:
                    df_srv = pd.concat([df_srv, pd.DataFrame([{"barcode": b_target, "scanned_qty": qty_target, "employee": emp, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])], ignore_index=True)
                df_srv.to_csv(SERVER_FINAL_FILE, index=False)
            except Exception:
                pass
                
        edit_barcode_field.value = ""
        edit_qty_field.value = "0"
        rebuild_jard_table_rows()
        status_text.value = f"⚙️ تم استبدال وتصحيح كمية القطعة {b_target} بنجاح!"
        page.update()
    # ز) أزرار تصفير ومزامنة التجميع والمستندات أوفلاين
    def trigger_manual_sync(e):
        res = sync_data_to_server()
        status_text.value = res
        rebuild_jard_table_rows()
        page.update()

    def trigger_wipe_and_reset(e):
        emp = state.employee_name if state.employee_name else "TEMP_GUEST"
        update_employee_file_paths(emp)
        if os.path.exists(LOCAL_JARD_FILE): os.remove(LOCAL_JARD_FILE)
        if os.path.exists(ARCHIVE_JARD_FILE): os.remove(ARCHIVE_JARD_FILE)
        
        # صمام أمان السيرفر: تنظيف وتطهير أسطر هذا الموظف فقط عند مسح جهازه والبدء من جديد
        if os.path.exists(SERVER_FINAL_FILE):
            try:
                df_server = pd.read_csv(SERVER_FINAL_FILE)
                if "employee" in df_server.columns:
                    df_server = df_server[df_server["employee"].astype(str).str.strip().str.upper() != emp.upper()]
                    df_server.to_csv(SERVER_FINAL_FILE, index=False)
            except Exception: pass
            
        state.employee_name = ""
        check_security_lock()
        refresh_sidebar()
        jard_table.rows.clear()
        status_text.value = "🗑️ تم مسح جردك الشخصي وتطهير بياناتك من السيرفر بنجاح! جرد زملائك آمن."
        page.update()
        show_employee_dialog()

    def generate_excel_report(df):
        if df is None:
            return "تقرير_جرد_تورينو_الختامي.xlsx"

        export_df = df.copy()
        export_df = export_df.fillna("")
        if "الكمية_المجرودة" not in export_df.columns:
            export_df["الكمية_المجرودة"] = 0
        if "الفرق" not in export_df.columns:
            original_qty = pd.to_numeric(export_df.get("الكمية_الأصلية", 0), errors="coerce").fillna(0)
            scanned_qty = pd.to_numeric(export_df.get("الكمية_المجرودة", 0), errors="coerce").fillna(0)
            export_df["الفرق"] = scanned_qty - original_qty

        output_path = "تقرير_جرد_تورينو_الختامي.xlsx"
        export_df.to_excel(output_path, index=False)
        return output_path

    def trigger_export_excel(e):
        if state.master_df is not None:
            path = generate_excel_report(state.master_df)
            status_text.value = f"📥 تم تصدير وحفظ ملف الإكسل الختامي بنجاح باسم: {path}"
            page.update()

    # ح) النوافذ المنبثقة التلقائية لرفع ملف النظام وتسجيل اسم الموظف إجبارياً
    def handle_file_upload_simulation(e):
        if os.path.exists(MASTER_DATA_FILE):
            state.master_df = pd.read_excel(MASTER_DATA_FILE)
            status_text.value = "🎯 تم تحميل وقراءة ملف النظام المرجعي بنجاح وثبات تلقائي!"
            check_security_lock()
            rebuild_jard_table_rows()
            show_employee_dialog()
        else:
            status_text.value = f"⚠️ ملف {MASTER_DATA_FILE} غير موجود بجانب التطبيق!"
            page.update()
    def show_employee_dialog():
        def save_emp_name(e):
            if name_input.value:
                state.employee_name = name_input.value.strip().upper()
                update_employee_file_paths(state.employee_name)
                check_security_lock()
                refresh_sidebar()
                rebuild_jard_table_rows()
                dialog.open = False
                page.update()
                
        name_input = ft.TextField(label="اكتب اسمك الثلاثي صراحة:")
        dialog = ft.AlertDialog(
            title=ft.Text("👤 تسجيل اسم الموظف المسؤول"),
            content=name_input,
            actions=[ft.ElevatedButton("🔓 بدء عملية الجرد والتفعيل", on_click=save_emp_name, bgcolor="#1B2A47", color="#FFFFFF")],
            modal=True
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    # ط) بناء الهيكل الرسومي وتوزيع المربعات والأزرار في الشاشة
    page.drawer = ft.NavigationDrawer(controls=[])
    laser_input.on_submit = handle_laser_scan
    manual_input.on_submit = handle_manual_submit
    search_field.on_change = lambda _: rebuild_jard_table_rows()

    # حقن وهندسة التصميم لمركز الإدخال والتصحيح بجانب البحث
    page.add(
        ft.Row([
            ft.IconButton(ft.icons.MENU, icon_color="#1B2A47", on_click=lambda _: page.drawer.open()),
            ft.Text("🔦 نظام جرد Torino الذكي والآمن - نسخة الأوفلاين الشاملة Flutter", size=20, weight=ft.FontWeight.BOLD, color="#1B2A47")
        ], alignment=ft.MainAxisAlignment.START),
        ft.Container(content=status_text, bgcolor="#FFF9E6", padding=10, border_radius=5),
        ft.ElevatedButton("📥 اضغط لتثبيت وقراءة ملف النظام المرجعي المرفوع تلقائياً", icon=ft.icons.UPLOAD_FILE, bgcolor="#1B2A47", color="#FFFFFF", on_click=handle_file_upload_simulation, width=400),
        ft.Divider(color="#D4AF37", thickness=2),
        employee_label,
        ft.Row([
            ft.Container(content=laser_input, expand=True),
            ft.Container(content=manual_input, expand=True),
        ]),
        camera_checkbox,
        ft.Divider(color="#1B2A47"),
        ft.Row([
            ft.Column([search_field], expand=True),
            ft.Column([
                ft.Row([
                    edit_barcode_field,
                    edit_qty_field,
                    ft.ElevatedButton("✅ تعديل الكمية", on_click=apply_quantity_correction, bgcolor="#008000", color="#FFFFFF")
                ])
            ], expand=True)
        ]),
        ft.Container(content=jard_table, padding=10),
        ft.Divider(color="#1B2A47"),
        ft.Row([
            ft.ElevatedButton("⚡ تفعيل المزامنة ودمج الجرد", icon=ft.icons.SYNC, bgcolor="#1B2A47", color="#FFFFFF", on_click=trigger_manual_sync, expand=True),
            ft.ElevatedButton("📥 تحميل تقرير الجرد الختامي المجمع", icon=ft.icons.DOWNLOAD, bgcolor="#008000", color="#FFFFFF", on_click=trigger_export_excel, expand=True),
            ft.ElevatedButton("🗑️ مسح الجرد والبدء من جديد", icon=ft.icons.DELETE_FOREVER, bgcolor="#850000", color="#FFFFFF", on_click=trigger_wipe_and_reset, expand=True),
        ])
    )
    refresh_sidebar()
    check_security_lock()

# --- 7. تشغيل وإطلاق محرك التطبيق المطور الأصيل للهاتف أوفلاين ---
if __name__ == "__main__":
    ft.app(main)

