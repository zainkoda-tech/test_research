# --- الاستدعاءات الأساسية ---
import os
import json
import requests
import webbrowser
import threading
import queue
from datetime import datetime, timedelta

# --- مكتبة Tkinter للواجهة الرسومية ---
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from PIL import Image, ImageTk
from io import BytesIO

# --- Firebase ---
import firebase_admin
from firebase_admin import credentials, db
from license_manager import LicenseManager
lm = LicenseManager()

# تفعيل الترخيص
if lm.activate("Zain", "ZAIN-PRO-2026"):
    print("تم التفعيل بنجاح ✅")
else:
    print("المفتاح غير صالح ❌")

print(lm.get_status_text())

# --- ملف الإعدادات الخارجي ---
from config import CONFIG

# --- إعدادات الملفات ---
USERS_FILE = "users.json"
LOCAL_FILE = "store_data.json"
SETTINGS_FILE = "settings.json"
PRODUCTS_FILE = "products.json"
TRANSACTIONS_FILE = "transactions.json"
SESSION_FILE = "session.json"

# --- إعدادات افتراضية ---
DEFAULT_SETTINGS = {
    "theme": "Light",
    "bg_color": "#ffffff",
    "fg_color": "#000000",
    "font_size": 12
}

TIMEOUT_LIMIT = 10
FIREBASE_URL = CONFIG["firebase"]["databaseURL"] + "/products.json"

# ============================================
# ========== دوال الإعدادات ==================
# ============================================

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        settings = DEFAULT_SETTINGS.copy()
    for key, value in DEFAULT_SETTINGS.items():
        settings.setdefault(key, value)
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def apply_settings(root, label, settings):
    root.configure(bg=settings["bg_color"])
    label.config(bg=settings["bg_color"],
                 fg=settings["fg_color"],
                 font=("Arial", settings["font_size"]))

# ============================================
# ========== تهيئة Firebase ==================
# ============================================

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            "databaseURL": CONFIG["firebase"]["databaseURL"]
        })
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print(f"⚠️ Firebase initialization error: {e}")

PRODUCTS_REF = db.reference("Products")


# ============================================
# ========== دوال المستخدمين Firebase ========
# ============================================

# Firebase Users Functions
def save_user_to_firebase(email, password):
    try:
        users_ref = db.reference("users")
        users = users_ref.get() or {}
        for uid, user_data in users.items():
            if user_data.get("email") == email:
                return False, "البريد موجود"
        import uuid
        new_uid = str(uuid.uuid4())
        trial_end = int((datetime.now().timestamp() + 30*24*60*60) * 1000)
        users_ref.child(new_uid).set({
            "email": email,
            "password": password,
            "role": "trial",
            "trial_end": trial_end,
            "products_limit": 5,
            "products_count": 0,
            "created_at": datetime.now().isoformat()
        })
        return True, new_uid
    except Exception as e:
        return False, str(e)

def get_user_from_firebase(email, password):
    try:
        users_ref = db.reference("users")
        users = users_ref.get() or {}
        for uid, user_data in users.items():
            if user_data.get("email") == email and user_data.get("password") == password:
                return uid, user_data
        return None, None
    except:
        return None, None
# ============================================
# ========== دوال المستخدمين =================
# ============================================

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

def save_user(email, password):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    users.append({"email": email, "password": password})
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def check_user(email, password):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    for u in users:
        if u["email"] == email and u["password"] == password:
            return True
    return False

# ============================================
# ========== دوال الجلسة ====================
# ============================================

def save_session(email):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"email": email, "timestamp": str(datetime.now())}, f, ensure_ascii=False, indent=4)

def load_session():
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# ============================================
# ========== نوافذ التسجيل والدخول ============
# ============================================

def register_window(root, callback=None):
    win = tk.Toplevel(root)
    win.title("تسجيل مستخدم")
    win.geometry("350x280")
    win.configure(bg="#1a1c2c")
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="📝 تسجيل جديد", font=("Arial", 14, "bold"),
             fg="#4efd54", bg="#1a1c2c").pack(pady=10)

    tk.Label(win, text="البريد الإلكتروني:", fg="white", bg="#1a1c2c").pack()
    email_ent = tk.Entry(win, width=30, bg="#2a2c3c", fg="white", insertbackground="white")
    email_ent.pack(pady=5)

    tk.Label(win, text="كلمة المرور:", fg="white", bg="#1a1c2c").pack()
    pass_ent = tk.Entry(win, width=30, show="*", bg="#2a2c3c", fg="white", insertbackground="white")
    pass_ent.pack(pady=5)

    def register():
        email = email_ent.get().strip()
        password = pass_ent.get().strip()
        if email and password:
            success, result = save_user_to_firebase(email, password)
            if success:
                messagebox.showinfo("نجاح ✅", "تم التسجيل بنجاح")
                if callback:
                    callback(email)
                win.destroy()
            else:
                messagebox.showerror("خطأ", result)
        else:
            messagebox.showerror("خطأ", "يرجى إدخال البيانات كاملة")

    # ✅ أضف هذا الزر
    tk.Button(win, text="تسجيل", command=register,
              bg="#4efd54", fg="black", padx=20, bd=0, cursor="hand2").pack(pady=10)
def login_window(root, callback=None):
    win = tk.Toplevel(root)
    win.title("تسجيل دخول")
    win.geometry("350x280")
    win.configure(bg="#1a1c2c")
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="🔐 تسجيل الدخول", font=("Arial", 14, "bold"),
             fg="#4efd54", bg="#1a1c2c").pack(pady=10)

    tk.Label(win, text="البريد الإلكتروني:", fg="white", bg="#1a1c2c").pack()
    email_ent = tk.Entry(win, width=30, bg="#2a2c3c", fg="white", insertbackground="white")
    email_ent.pack(pady=5)

    tk.Label(win, text="كلمة المرور:", fg="white", bg="#1a1c2c").pack()
    pass_ent = tk.Entry(win, width=30, show="*", bg="#2a2c3c", fg="white", insertbackground="white")
    pass_ent.pack(pady=5)

    remember_var = tk.BooleanVar(value=True)
    tk.Checkbutton(win, text="تذكرني", variable=remember_var,
                   fg="white", bg="#1a1c2c", selectcolor="#1a1c2c", activebackground="#1a1c2c").pack()

    def login():
        email = email_ent.get().strip()
        password = pass_ent.get().strip()
        if check_user(email, password):
            if remember_var.get():
                save_session(email)
            if callback:
                callback(email)
            win.destroy()
        else:
            messagebox.showerror("خطأ", "بيانات غير صحيحة")

    tk.Button(win, text="دخول", command=login,
              bg="#4efd54", fg="black", padx=20, bd=0, cursor="hand2").pack(pady=10)

def open_license_window(root, callback):
    win = tk.Toplevel(root)
    win.title("تفعيل الرخصة")
    win.geometry("400x200")
    win.configure(bg="#1a1c2c")
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="🔑 تفعيل الرخصة", font=("Arial", 14, "bold"),
             fg="#4efd54", bg="#1a1c2c").pack(pady=10)

    tk.Label(win, text="أدخل مفتاح التفعيل:", fg="white", bg="#1a1c2c").pack()
    key_ent = tk.Entry(win, width=30, bg="#2a2c3c", fg="white", insertbackground="white", show="*")
    key_ent.pack(pady=5)

    def activate():
        key = key_ent.get().strip()
        if key == "12345" or lm.activate("User", key):
            messagebox.showinfo("✅", "تم التفعيل بنجاح")
            callback()
            win.destroy()
        else:
            messagebox.showerror("❌", "مفتاح غير صالح")

    tk.Button(win, text="تفعيل", command=activate,
              bg="#4efd54", fg="black", padx=20, bd=0, cursor="hand2").pack(pady=10)

# ============================================
# ========== دوال الأرشفة ====================
# ============================================

def load_local_data():
    try:
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def archive_locally(data):
    with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def sync_process():
    print("\n[جاري الاتصال بـ Firebase... ⏳]")
    try:
        response = requests.get(FIREBASE_URL, timeout=TIMEOUT_LIMIT)
        if response.status_code == 200:
            buffer_data = response.json()
            if buffer_data and isinstance(buffer_data, dict):
                archive_locally(buffer_data)
                print("[تم التحديث: البيانات مطابقة للسحابة ✅]")
                return buffer_data
            else:
                print("[المدقق 🛡️: تم رفض التحديث!]")
        else:
            print(f"[خطأ من الخادم: {response.status_code}]")
    except Exception:
        print("[نواجه صعوبة في الاتصال ☁️، سنعتمد على البيانات المحلية حالياً.]")
    return load_local_data()

# ============================================
# ========== إعدادات الهوية ==================
# ============================================

DEVELOPER_NAME = "Mr. Zain"
DEVELOPER_EMAIL = "Zain.koda@gmail.com"
WHATSAPP_NUM = "+201005032186"
SLOGAN = "اقتني متجرك الذكي - Acquire Your Smart Store"

# ============================================
# ========== كلاس مدير المنتجات ==============
# ============================================

class ProductManager:
    def __init__(self, root, data, refresh_callback):
        self.root = root
        self.data = data
        self.refresh_callback = refresh_callback
        self.product_tree = None
        self.prod_win = None
        self.temp_thumb_path = ""

    def save_to_firebase(self):
        """حفظ البيانات مباشرة في Firebase"""
        try:
            PRODUCTS_REF.set(self.data)
            print("✅ تم الحفظ في Firebase")
            return True
        except Exception as e:
            print(f"❌ خطأ في الحفظ: {e}")
            messagebox.showerror("❌", f"فشل الحفظ في Firebase: {e}")
            return False

    def open_manager(self):
        self.prod_win = tk.Toplevel(self.root)
        self.prod_win.title("📦 مدير المنتجات")
        self.prod_win.geometry("1000x600")
        self.prod_win.configure(bg="#1a1c2c")
        self.prod_win.transient(self.root)
        self.prod_win.grab_set()

        # شريط الأدوات
        toolbar = tk.Frame(self.prod_win, bg="#2a2c3c", height=50)
        toolbar.pack(fill="x", padx=0, pady=0)

        tk.Button(toolbar, text="➕ إضافة", command=self.add_product,
                  bg="#4efd54", fg="black", padx=15, bd=0, cursor="hand2").pack(side="left", padx=5)
        tk.Button(toolbar, text="✏️ تعديل", command=self.edit_product,
                  bg="#3498DB", fg="white", padx=15, bd=0, cursor="hand2").pack(side="left", padx=5)
        tk.Button(toolbar, text="🗑️ حذف", command=self.delete_product,
                  bg="#E74C3C", fg="white", padx=15, bd=0, cursor="hand2").pack(side="left", padx=5)
        tk.Button(toolbar, text="🔄 تحديث", command=self.refresh_from_firebase,
                  bg="#34495e", fg="white", padx=15, bd=0, cursor="hand2").pack(side="left", padx=5)

        # إطار الجدول
        main_frame = tk.Frame(self.prod_win, bg="#1a1c2c")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # إنشاء الجدول
        columns = ("id", "name", "price", "desc")
        self.product_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)

        self.product_tree.heading("id", text="الرقم")
        self.product_tree.heading("name", text="الاسم")
        self.product_tree.heading("price", text="السعر")
        self.product_tree.heading("desc", text="الوصف")

        self.product_tree.column("id", width=80, anchor="center")
        self.product_tree.column("name", width=200, anchor="center")
        self.product_tree.column("price", width=100, anchor="center")
        self.product_tree.column("desc", width=300, anchor="center")

        v_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=v_scrollbar.set)

        self.product_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")

        self.show_all_products()

    def show_all_products(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        if not isinstance(self.data, dict):
            messagebox.showerror("خطأ", "بيانات المنتجات غير صالحة")
            return

        for pid, item in self.data.items():
            if not isinstance(item, dict):
                continue
            self.product_tree.insert("", tk.END, values=(
                pid,
                item.get("name", "N/A"),
                item.get("price", 0),
                item.get("desc", "")
            ))

    def refresh_from_firebase(self):
        try:
            products = PRODUCTS_REF.get()
            if products and isinstance(products, dict):
                self.data = products
                self.show_all_products()
                if self.refresh_callback:
                    self.refresh_callback(self.data)
                messagebox.showinfo("✅", "تم التحديث من Firebase")
            else:
                self.data = {}
                self.show_all_products()
                messagebox.showinfo("ℹ️", "لا توجد منتجات في Firebase")
        except Exception as e:
            messagebox.showerror("❌", f"خطأ: {e}")

    def add_product(self):
        win = tk.Toplevel(self.prod_win)
        win.title("إضافة منتج جديد")
        win.geometry("450x500")
        win.configure(bg="#1a1c2c")
        win.transient(self.prod_win)
        win.grab_set()

        # حقول الإدخال
        fields = [
            ("اسم المنتج:", "name"),
            ("السعر:", "price"),
            ("الوصف:", "desc"),
        ]

        entries = {}
        for label, key in fields:
            tk.Label(win, text=label, fg="white", bg="#1a1c2c").pack(pady=2)
            entries[key] = tk.Entry(win, width=30, bg="#2a2c3c", fg="white", insertbackground="white")
            entries[key].pack(pady=5)

        # صورة المنتج
        tk.Label(win, text="الصورة:", fg="white", bg="#1a1c2c").pack(pady=2)
        thumb_var = tk.StringVar()
        thumb_entry = tk.Entry(win, textvariable=thumb_var, width=30, bg="#2a2c3c", fg="white")
        thumb_entry.pack(pady=5)

        def select_image():
            path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
            if path:
                thumb_var.set(path)

        tk.Button(win, text="اختر صورة", command=select_image,
                  bg="#4efd54", fg="black", padx=10, bd=0, cursor="hand2").pack(pady=5)

        def save():
            name = entries["name"].get().strip()
            price = entries["price"].get().strip()

            if not name or not price:
                messagebox.showerror("خطأ", "الاسم والسعر مطلوبان")
                return

            try:
                price = float(price)
            except:
                messagebox.showerror("خطأ", "السعر يجب أن يكون رقماً")
                return

            # إنشاء ID جديد
            new_id = str(len(self.data) + 1)
            while new_id in self.data:  # تأكد من عدم التكرار
                new_id = str(int(new_id) + 1)

            if not isinstance(self.data, dict):
                self.data = {}

            self.data[new_id] = {
                "name": name,
                "price": price,
                "desc": entries["desc"].get(),
                "thumbnail": thumb_var.get()
            }

            # ✅ حفظ في Firebase أولاً
            if self.save_to_firebase():
                self.show_all_products()
                if self.refresh_callback:
                    self.refresh_callback(self.data)
                messagebox.showinfo("✅", "تمت الإضافة بنجاح في Firebase")
                win.destroy()
            else:
                # لو فشل الحفظ، نحذف المنتج من البيانات المحلية
                del self.data[new_id]

        tk.Button(win, text="حفظ", command=save,
                  bg="#4efd54", fg="black", padx=20, bd=0, cursor="hand2").pack(pady=10)

    def edit_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "اختر منتجاً للتعديل")
            return

        values = self.product_tree.item(selected[0])['values']
        if not values:
            return

        pid = str(values[0])
        product = self.data.get(pid, {})

        win = tk.Toplevel(self.prod_win)
        win.title("تعديل المنتج")
        win.geometry("450x400")
        win.configure(bg="#1a1c2c")
        win.transient(self.prod_win)
        win.grab_set()

        tk.Label(win, text="اسم المنتج:", fg="white", bg="#1a1c2c").pack(pady=2)
        name_ent = tk.Entry(win, width=30, bg="#2a2c3c", fg="white")
        name_ent.insert(0, product.get("name", ""))
        name_ent.pack(pady=5)

        tk.Label(win, text="السعر:", fg="white", bg="#1a1c2c").pack(pady=2)
        price_ent = tk.Entry(win, width=30, bg="#2a2c3c", fg="white")
        price_ent.insert(0, str(product.get("price", "")))
        price_ent.pack(pady=5)

        tk.Label(win, text="الوصف:", fg="white", bg="#1a1c2c").pack(pady=2)
        desc_ent = tk.Entry(win, width=30, bg="#2a2c3c", fg="white")
        desc_ent.insert(0, product.get("desc", ""))
        desc_ent.pack(pady=5)

        def save():
            # حفظ البيانات القديمة في حالة التراجع
            old_data = self.data[pid].copy()

            try:
                self.data[pid]["name"] = name_ent.get()
                self.data[pid]["price"] = float(price_ent.get())
                self.data[pid]["desc"] = desc_ent.get()

                # ✅ حفظ في Firebase أولاً
                if self.save_to_firebase():
                    self.show_all_products()
                    if self.refresh_callback:
                        self.refresh_callback(self.data)
                    win.destroy()
                    messagebox.showinfo("✅", "تم التعديل بنجاح في Firebase")
                else:
                    # لو فشل، نرجع البيانات القديمة
                    self.data[pid] = old_data

            except Exception as e:
                messagebox.showerror("خطأ", f"بيانات غير صالحة: {e}")

        tk.Button(win, text="حفظ", command=save,
                  bg="#4efd54", fg="black", padx=20, bd=0, cursor="hand2").pack(pady=10)

    def delete_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "اختر منتجاً للحذف")
            return

        values = self.product_tree.item(selected[0])['values']
        if not values:
            return

        pid = values[0]
        product_name = values[1]

        if messagebox.askyesno("تأكيد", f"هل تريد حذف المنتج {product_name}؟"):
            if pid in self.data:
                # حفظ نسخة احتياطية
                deleted_product = self.data[pid]
                del self.data[pid]

                # ✅ حفظ في Firebase أولاً
                if self.save_to_firebase():
                    self.show_all_products()
                    if self.refresh_callback:
                        self.refresh_callback(self.data)
                    messagebox.showinfo("✅", "تم الحذف بنجاح من Firebase")
                else:
                    # لو فشل، نرجع المنتج
                    self.data[pid] = deleted_product
                    self.show_all_products()
# ============================================
# ========== كلاس التطبيق الرئيسي ============
# ============================================

class ZainStoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{DEVELOPER_NAME} - Zain Store Engine")
        self.root.geometry("1200x700")
        self.root.configure(bg="#0f172a")

        # متغيرات أساسية
        self.cart = {}
        self.cart_label = None
        self.logged_in = False
        self.owner_mode = lm.is_fully_active()
        self.current_user_email = None

        # ✅ التعديل - نبدأ ببيانات فاضية بس
        self.data = {}
        self.products = self.data
        self.services = {}
        self.show_services = False  # للتبديل بين المنتجات والخدمات
        self.queue = queue.Queue()
        self.settings = load_settings()
        self.product_images = []

        # متغيرات التحكم في إظهار الأزرار
        self.show_security = False
        self.show_backup = False
        self.show_sonic = False
        self.show_siting = False
        self.show_diagnostic = False

        # تحميل الجلسة المحفوظة
        session = load_session()
        if session and session.get("email"):
            self.logged_in = True
            self.current_user_email = session.get("email")

        # ✅ أولاً: إنشاء واجهة المستخدم (عشان products_frame يظهر)
        self.create_modern_ui()

        # ✅ ثانياً: تحميل المنتجات من Firebase (بعد ما products_frame جهز)
        self.load_products_from_firebase()
        self.update_vendors_list()


        # ✅ ثالثاً: تحميل المنتجات وعرضها
        self.load_products()
        self.check_queue()
    # ========================================
    # ========== الواجهة الحديثة =============
    # ========================================

    def create_modern_ui(self):
        """إنشاء واجهة عصرية بالكامل"""

        # الشريط العلوي
        self.create_modern_header()

        # المحتوى الرئيسي
        main_container = tk.Frame(self.root, bg="#0f172a")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # شريط جانبي
        self.create_modern_sidebar(main_container)

        # منطقة المحتوى الرئيسي
        self.content_frame = tk.Frame(main_container, bg="#0f172a")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # شريط البحث
        self.create_modern_search()

        # إطار المنتجات
        self.products_frame = tk.Frame(self.content_frame, bg="#0f172a")
        self.products_frame.pack(fill="both", expand=True, pady=10)

    def create_modern_header(self):
        """شريط علوي عصري"""
        header = tk.Frame(self.root, bg="#1e293b", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        # الشعار
        logo_frame = tk.Frame(header, bg="#1e293b")
        logo_frame.pack(side="right", padx=20)

        # أيقونة المتجر
        logo_canvas = tk.Canvas(logo_frame, width=40, height=40, bg="#1e293b", highlightthickness=0)
        logo_canvas.create_oval(5, 5, 35, 35, fill="#4efd54", outline="")
        logo_canvas.create_text(20, 20, text="Z", fill="#0f172a", font=("Arial", 16, "bold"))
        logo_canvas.pack(side="right", padx=5)

        tk.Label(logo_frame, text="Zain Store", font=("Arial", 18, "bold"),
                 fg="white", bg="#1e293b").pack(side="right")

        # الشعار النصي
        tk.Label(header, text=SLOGAN, font=("Arial", 11),
                 fg="#94a3b8", bg="#1e293b").pack(side="right", padx=20)

        # أيقونات المستخدم والسلة
        left_frame = tk.Frame(header, bg="#1e293b")
        left_frame.pack(side="left", padx=20)

        # عداد السلة
        self.cart_indicator = tk.Label(left_frame, text="🛒 0",
                                       font=("Arial", 12, "bold"),
                                       fg="#4efd54", bg="#1e293b",
                                       cursor="hand2")
        self.cart_indicator.pack(side="left", padx=10)
        self.cart_indicator.bind("<Button-1>", lambda e: self.show_cart())

        # حالة المستخدم
        user_text = f"👤 {self.current_user_email[:15]}..." if self.logged_in else "👤 ضيف"
        self.user_indicator = tk.Label(left_frame, text=user_text,
                                       font=("Arial", 11), fg="#94a3b8",
                                       bg="#1e293b", cursor="hand2")
        self.user_indicator.pack(side="left", padx=10)
        self.user_indicator.bind("<Button-1>", lambda e: self.show_login_options())

    def show_vendor_products(self, vendor_id, vendor_name):
        """عرض منتجات تاجر معين"""
        if not vendor_id:
            return

        # فلتر المنتجات للتاجر ده
        filtered = {}
        for pid, product in self.products.items():
            if isinstance(product, dict) and product.get("vendorId") == vendor_id:
                filtered[pid] = product

        if filtered:
            self.setup_products_cards(filtered)
            # تحديث الفلتر لو موجود
            if hasattr(self, 'vendor_filter_var'):
                self.vendor_filter_var.set(vendor_name)
            self.show_products_view()

            # ✅ إغلاق نافذة الإحصائيات
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Toplevel) and widget.title() == "📊 إحصائيات المالك":
                    widget.destroy()
        else:
            messagebox.showinfo("ℹ️", f"لا توجد منتجات للتاجر {vendor_name}")
    # ========== دوال التبديل بين المنتجات والخدمات ==========
    def show_products_view(self):
        """عرض المنتجات"""
        self.show_services = False
        self.products_btn.config(bg="#4efd54", fg="black")
        self.services_btn.config(bg="#334155", fg="white")
        self.load_products_from_firebase()

    def show_services_view(self):
        """عرض الخدمات"""
        self.show_services = True
        self.products_btn.config(bg="#334155", fg="white")
        self.services_btn.config(bg="#4efd54", fg="black")
        self.load_services_from_firebase()

    def load_services_from_firebase(self):
        """تحميل الخدمات وعرضها"""
        try:
            self.services = self.load_all_services()
            self.setup_services_cards()
        except Exception as e:
            messagebox.showerror("❌", f"خطأ في تحميل الخدمات: {e}")

    def create_modern_sidebar(self, parent):
        """شريط جانبي عصري"""
        sidebar = tk.Frame(parent, bg="#1e293b", width=200)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        # عنوان القسم
        tk.Label(sidebar, text="القائمة الرئيسية", font=("Arial", 12, "bold"),
                 fg="#4efd54", bg="#1e293b").pack(pady=(15, 10))

        # أزرار القائمة
        menu_items = [
            ("🏠 الرئيسية", self.show_home),
            ("📦 المنتجات", self.show_products),
            ("🛒 السلة", self.show_cart),
            ("📋 الطلبات", self.open_transactions_window),
        ]

        for text, command in menu_items:
            btn = tk.Button(sidebar, text=text, command=command,
                            bg="#334155", fg="white",
                            font=("Arial", 11), bd=0,
                            padx=15, pady=8, anchor="w",
                            cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)

            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#4efd54", fg="black"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#334155", fg="white"))

        # ✅ أزرار التبديل بين المنتجات والخدمات (جديد)
        toggle_frame = tk.Frame(sidebar, bg="#1e293b")
        toggle_frame.pack(fill="x", padx=10, pady=10)

        self.products_btn = tk.Button(toggle_frame, text="📦 منتجات", command=self.show_products_view,
                                      bg="#4efd54", fg="black", bd=0, padx=15, pady=5, cursor="hand2")
        self.products_btn.pack(side="right", padx=2, expand=True, fill="x")

        self.services_btn = tk.Button(toggle_frame, text="🛠️ خدمات", command=self.show_services_view,
                                      bg="#334155", fg="white", bd=0, padx=15, pady=5, cursor="hand2")
        self.services_btn.pack(side="left", padx=2, expand=True, fill="x")

        # فصل
        tk.Frame(sidebar, bg="#334155", height=1).pack(fill="x", padx=10, pady=15)

        # أزرار إضافية (للمالك)
        if self.owner_mode:
            tk.Label(sidebar, text="لوحة التحكم", font=("Arial", 11, "bold"),
                     fg="#f59e0b", bg="#1e293b").pack(pady=5)

            admin_buttons = [
                ("➕ إضافة منتج", self.add_product_shortcut),
                ("➕ إضافة خدمة", self.add_service_shortcut),
                ("📊 الإحصائيات", self.open_statistics_window),  # 👈 جديد
                ("💰 العمولات", self.open_commission_window),  # 👈 جديد (مكان جاهز)
                ("🔐 الأمان", self.open_security_window),
                ("💾 النسخ الاحتياطي", self.open_backup_manager),
            ]

            for text, command in admin_buttons:
                btn = tk.Button(sidebar, text=text, command=command,
                                bg="#2d3748", fg="#f59e0b",
                                font=("Arial", 10), bd=0,
                                padx=15, pady=5, anchor="w")
                btn.pack(fill="x", padx=10, pady=2)
    def open_backup_manager(self):
        """مدير النسخ الاحتياطي - تصدير البيانات"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "مدير النسخ الاحتياطي للمالك فقط")
            return

        win = tk.Toplevel(self.root)
        win.title("💾 النسخ الاحتياطي")
        win.geometry("500x400")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="النسخ الاحتياطي", font=("Arial", 18, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        # أزرار التصدير
        btn_frame = tk.Frame(win, bg="#0f172a")
        btn_frame.pack(pady=10)

        def export_users():
            try:
                users = db.reference("users").get() or {}
                with open("backup_users.json", "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("✅", "تم تصدير المستخدمين إلى backup_users.json")
            except Exception as e:
                messagebox.showerror("❌", f"خطأ: {e}")

        def export_products():
            try:
                products = db.reference("Products").get() or {}
                with open("backup_products.json", "w", encoding="utf-8") as f:
                    json.dump(products, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("✅", "تم تصدير المنتجات إلى backup_products.json")
            except Exception as e:
                messagebox.showerror("❌", f"خطأ: {e}")

        def export_vendor_products():
            try:
                vendor_products = db.reference("VendorProducts").get() or {}
                with open("backup_vendor_products.json", "w", encoding="utf-8") as f:
                    json.dump(vendor_products, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("✅", "تم تصدير منتجات التجار إلى backup_vendor_products.json")
            except Exception as e:
                messagebox.showerror("❌", f"خطأ: {e}")

        def export_services():
            try:
                services = db.reference("Services").get() or {}
                with open("backup_services.json", "w", encoding="utf-8") as f:
                    json.dump(services, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("✅", "تم تصدير الخدمات إلى backup_services.json")
            except Exception as e:
                messagebox.showerror("❌", f"خطأ: {e}")

        def export_all():
            try:
                export_users()
                export_products()
                export_vendor_products()
                export_services()
                messagebox.showinfo("✅", "تم تصدير جميع البيانات")
            except Exception as e:
                messagebox.showerror("❌", f"خطأ: {e}")

        tk.Button(btn_frame, text="👥 تصدير المستخدمين", command=export_users,
                  bg="#334155", fg="white", padx=15, pady=5).pack(pady=5)
        tk.Button(btn_frame, text="📦 تصدير المنتجات", command=export_products,
                  bg="#334155", fg="white", padx=15, pady=5).pack(pady=5)
        tk.Button(btn_frame, text="🏪 تصدير منتجات التجار", command=export_vendor_products,
                  bg="#334155", fg="white", padx=15, pady=5).pack(pady=5)
        tk.Button(btn_frame, text="🛠️ تصدير الخدمات", command=export_services,
                  bg="#334155", fg="white", padx=15, pady=5).pack(pady=5)
        tk.Button(btn_frame, text="💾 تصدير الكل", command=export_all,
                  bg="#4efd54", fg="black", padx=20, pady=5).pack(pady=10)

        # تعليمات الاستيراد
        tk.Label(win, text="للاستيراد، قم بوضع ملفات JSON في مجلد البرنامج",
                 fg="#94a3b8", bg="#0f172a", font=("Arial", 10)).pack(pady=10)

    def open_statistics_window(self):
        """نافذة إحصائيات المالك (مبيعات، منتجات، تجار)"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "الإحصائيات للمالك فقط")
            return

        win = tk.Toplevel(self.root)
        win.title("📊 إحصائيات المالك")
        win.geometry("900x700")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="إحصائيات المتجر", font=("Arial", 20, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        # إطار الإحصائيات السريعة
        stats_frame = tk.Frame(win, bg="#0f172a")
        stats_frame.pack(fill="x", padx=20, pady=10)

        # جلب البيانات
        try:
            users = db.reference("users").get() or {}
            products = db.reference("Products").get() or {}
            vendor_products = db.reference("VendorProducts").get() or {}
            services = db.reference("Services").get() or {}
            orders = db.reference("Orders").get() or {}

            # حساب الإحصائيات
            total_users = len(users)
            total_sellers = sum(
                1 for u in users.values() if u.get("role") in ["seller_monthly", "seller_yearly", "seller"])
            total_products = len(products) + sum(len(vp) for vp in vendor_products.values() if isinstance(vp, dict))
            total_services = len(services)

            # حساب المبيعات
            total_sales = 0
            total_orders = 0
            for customer_id, customer_orders in orders.items():
                if isinstance(customer_orders, dict):
                    for order_id, order in customer_orders.items():
                        if isinstance(order, dict) and order.get("status") != "cancelled":
                            total_sales += order.get("total", 0)
                            total_orders += 1

            # بطاقات الإحصائيات
            cards = [
                ("👥 المستخدمين", total_users),
                ("🏪 التجار", total_sellers),
                ("📦 المنتجات", total_products),
                ("🛠️ الخدمات", total_services),
                ("🛒 الطلبات", total_orders),
                ("💰 إجمالي المبيعات", f"{total_sales} EGP"),
            ]

            for i, (label, value) in enumerate(cards):
                card = tk.Frame(stats_frame, bg="#1e293b", padx=20, pady=15, relief="flat", bd=0)
                card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")
                tk.Label(card, text=label, font=("Arial", 12), fg="#94a3b8", bg="#1e293b").pack()
                tk.Label(card, text=str(value), font=("Arial", 24, "bold"), fg="#4efd54", bg="#1e293b").pack()

            for i in range(3):
                stats_frame.grid_columnconfigure(i, weight=1)

            # ========== مبيعات التجار (جدول) ==========
            tk.Label(win, text="مبيعات التجار", font=("Arial", 16, "bold"),
                     fg="#f59e0b", bg="#0f172a").pack(pady=10)

            # إطار الجدول
            table_frame = tk.Frame(win, bg="#0f172a")
            table_frame.pack(fill="both", expand=True, padx=20, pady=5)

            columns = ("التاجر", "عدد المنتجات", "عدد الطلبات", "إجمالي المبيعات")
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150, anchor="center")

            # حساب مبيعات كل تاجر
            seller_stats = {}

            # حساب منتجات كل تاجر
            for vendor_id, vp in vendor_products.items():
                if isinstance(vp, dict):
                    seller_stats[vendor_id] = {
                        "name": self.get_vendor_name(vendor_id),
                        "products": len(vp),
                        "orders": 0,
                        "total": 0
                    }

            # حساب الطلبات لكل تاجر
            for customer_id, customer_orders in orders.items():
                if isinstance(customer_orders, dict):
                    for order_id, order in customer_orders.items():
                        if isinstance(order, dict) and order.get("status") != "cancelled":
                            if order.get("items"):
                                for item in order["items"]:
                                    seller_id = item.get("sellerId") or item.get("vendorId")
                                    if seller_id and seller_id in seller_stats:
                                        seller_stats[seller_id]["orders"] += 1
                                        seller_stats[seller_id]["total"] += item.get("price", 0) * item.get("quantity",
                                                                                                            1)

            for seller_id, stats in seller_stats.items():
                item_id = tree.insert("", "end", values=(
                    stats["name"],
                    stats["products"],
                    stats["orders"],
                    f"{stats['total']} EGP"
                ))
                # ✅ ربط الضغط المزدوج على اسم التاجر
                tree.tag_bind(item_id, "<Double-1>",
                              lambda e, sid=seller_id, sname=stats["name"]: self.show_vendor_products(sid, sname))

            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        except Exception as e:
            tk.Label(win, text=f"خطأ في تحميل البيانات: {e}", fg="red", bg="#0f172a").pack(pady=20)

        tk.Button(win, text="❌ إغلاق", command=win.destroy,
                  bg="#e74c3c", fg="white", padx=20, pady=5).pack(pady=10)

    def open_commission_window(self):
        """نافذة العمولات (مكان جاهز للتطوير)"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "العمولات للمالك فقط")
            return

        win = tk.Toplevel(self.root)
        win.title("💰 نظام العمولات")
        win.geometry("600x400")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="نظام العمولات", font=("Arial", 18, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        tk.Label(win, text="⚠️ قيد التطوير - سيتم إضافة نظام العمولات قريباً",
                 fg="#f59e0b", bg="#0f172a", font=("Arial", 12)).pack(pady=50)

        tk.Label(win, text="المميزات القادمة:", fg="white", bg="#0f172a", font=("Arial", 12)).pack(pady=5)
        features = [
            "• تحديد نسبة العمولة (مثلاً 10%)",
            "• عرض أرباح كل تاجر",
            "• إحصائيات العمولات الشهرية",
            "• تصدير تقارير العمولات",
        ]
        for f in features:
            tk.Label(win, text=f, fg="#94a3b8", bg="#0f172a").pack()

        tk.Button(win, text="❌ إغلاق", command=win.destroy,
                  bg="#e74c3c", fg="white", padx=20, pady=5).pack(pady=20)
    def create_modern_search(self):
        """شريط بحث عصري"""
        search_frame = tk.Frame(self.content_frame, bg="#0f172a", pady=10)
        search_frame.pack(fill="x")

        search_container = tk.Frame(search_frame, bg="#1e293b", padx=10, pady=5)
        search_container.pack(side="right")

        tk.Label(search_container, text="🔍", font=("Arial", 12),
                 fg="white", bg="#1e293b").pack(side="right")

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_products())

        tk.Entry(search_container, textvariable=self.search_var,
                 width=40, font=("Arial", 11), bd=0,
                 bg="#1e293b", fg="white",
                 insertbackground="white").pack(side="right", padx=5)

        # أزرار الفرز
        sort_frame = tk.Frame(search_frame, bg="#0f172a")
        sort_frame.pack(side="left")

        sort_buttons = [
            ("💰 الأعلى", "high"),
            ("💰 الأقل", "low"),
            ("🔤 أبجدي", "name"),
        ]

        for text, sort_type in sort_buttons:
            btn = tk.Button(sort_frame, text=text,
                            command=lambda t=sort_type: self.sort_products(t),
                            bg="#334155", fg="white", bd=0,
                            padx=12, pady=5, cursor="hand2")
            btn.pack(side="left", padx=2)

            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#4efd54", fg="black"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#334155", fg="white"))

        # ✅ فلتر التجار (جديد)
        vendor_frame = tk.Frame(search_frame, bg="#0f172a")
        vendor_frame.pack(side="left", padx=10)

        tk.Label(vendor_frame, text="تاجر:", fg="white", bg="#0f172a",
                 font=("Arial", 10)).pack(side="right", padx=5)

        self.vendor_filter_var = tk.StringVar(value="all")
        self.vendor_filter_menu = ttk.Combobox(vendor_frame, textvariable=self.vendor_filter_var,
                                               values=["all"], width=20,
                                               state="readonly", font=("Arial", 10))
        self.vendor_filter_menu.pack(side="right")
        self.vendor_filter_menu.bind("<<ComboboxSelected>>", lambda e: self.filter_products())

        # تحديث قائمة التجار
        self.update_vendors_list()
        # فلتر التصنيفات
        category_frame = tk.Frame(search_frame, bg="#0f172a")
        category_frame.pack(side="left", padx=10)

        tk.Label(category_frame, text="تصنيف:", fg="white", bg="#0f172a",
                 font=("Arial", 10)).pack(side="right", padx=5)

        self.category_filter_var = tk.StringVar(value="all")
        self.category_filter_menu = ttk.Combobox(category_frame, textvariable=self.category_filter_var,
                                                  values=["all", "الكترونيات", "مستلزمات مطبخ", "اخرى", "موادغذائيه", "خدمات"],
                                                  width=15, state="readonly", font=("Arial", 10))
        self.category_filter_menu.pack(side="right")
        self.category_filter_menu.bind("<<ComboboxSelected>>", lambda e: self.filter_products())
    # ========================================
    # ========== دوال المنتجات ===============
    # ========================================

    def show_home(self):
        """العرض الرئيسي"""
        self.setup_products_cards()

    def show_products(self):
        """عرض المنتجات"""
        self.setup_products_cards()

    def load_products(self):
        """تحميل المنتجات من المصادر المختلفة"""
        if not self.products or len(self.products) == 0:
            self.products = {
                "1": {"name": "منتج تجريبي", "price": 100, "desc": "للاختبار"}
            }
        self.setup_products_cards()

    def load_products_from_firebase(self):
        """تحميل جميع المنتجات من Firebase (رئيسية + تجار)"""
        try:
            all_products = self.load_all_products()
            self.products = all_products
            self.data = all_products
            self.setup_products_cards()
            messagebox.showinfo("✅", f"تم تحميل {len(all_products)} منتج")
        except Exception as e:
            messagebox.showerror("❌", f"خطأ في التحميل: {e}")

    def load_all_products(self):
        """جلب جميع المنتجات (رئيسية + تجار)"""
        all_products = {}

        # 1. جلب المنتجات الرئيسية
        try:
            products = PRODUCTS_REF.get() or {}
            for pid, p in products.items():
                if isinstance(p, dict) and p.get('name'):
                    all_products[f"main_{pid}"] = {
                        **p,
                        "uniqueId": f"main_{pid}",
                        "originalId": pid,
                        "vendorId": None,
                        "vendorName": None,
                        "source": "main"
                    }
        except Exception as e:
            print(f"خطأ في جلب المنتجات الرئيسية: {e}")

        # 2. جلب منتجات التجار (VendorProducts)
        try:
            vendor_ref = db.reference("VendorProducts")
            vendor_products = vendor_ref.get() or {}

            for vendor_id, vendor_items in vendor_products.items():
                if not isinstance(vendor_items, dict):
                    continue
                for prod_id, prod in vendor_items.items():
                    if isinstance(prod, dict) and prod.get('name'):
                        all_products[f"vendor_{vendor_id}_{prod_id}"] = {
                            **prod,
                            "uniqueId": f"vendor_{vendor_id}_{prod_id}",
                            "originalId": prod_id,
                            "vendorId": vendor_id,
                            "vendorName": self.get_vendor_name(vendor_id),
                            "source": "vendor"
                        }
        except Exception as e:
            print(f"خطأ في جلب منتجات التجار: {e}")

        print(f"✅ تم تحميل {len(all_products)} منتج (رئيسي + تجار)")
        return all_products

    def load_all_services(self):
        """جلب جميع الخدمات من Firebase"""
        all_services = {}
        try:
            services_ref = db.reference("Services")
            services = services_ref.get() or {}

            for sid, service in services.items():
                if isinstance(service, dict):
                    all_services[sid] = {
                        **service,
                        "uniqueId": sid,
                        "source": "service"
                    }
            print(f"✅ تم تحميل {len(all_services)} خدمة")
        except Exception as e:
            print(f"خطأ في جلب الخدمات: {e}")

        return all_services

    def get_vendor_name(self, vendor_id):
        """جلب اسم التاجر من Firebase"""
        try:
            user_ref = db.reference(f"users/{vendor_id}")
            user_data = user_ref.get()
            if user_data:
                name = user_data.get("storeName")
                if name:
                    return name
                email = user_data.get("email", "")
                if email:
                    return email.split("@")[0]
            return "تاجر"
        except:
            return "تاجر"

    def update_vendors_list(self):
        """تحديث قائمة التجار في الفلتر"""
        vendors_display = ["كل التجار"]
        self.vendor_mapping = {}  # الاسم → {uid, phone}
        self.vendor_uid_to_name = {}  # uid → الاسم

        try:
            users_ref = db.reference("users")
            users = users_ref.get() or {}

            for uid, user_data in users.items():
                role = user_data.get("role", "")
                if role in ["seller_monthly", "seller_yearly", "seller", "trial"]:
                    name = user_data.get("storeName")
                    if not name:
                        email = user_data.get("email", "")
                        name = email.split("@")[0] if email else "تاجر"

                    phone = user_data.get("phone", "")  # جلب رقم التاجر

                    vendors_display.append(name)
                    self.vendor_mapping[name] = {
                        "uid": uid,
                        "phone": phone
                    }
                    self.vendor_uid_to_name[uid] = name

            self.vendor_filter_menu['values'] = vendors_display
            self.vendor_filter_menu.set("كل التجار")
        except Exception as e:
            print(f"خطأ في تحميل التجار: {e}")

    def filter_products(self):
        """تصفية المنتجات حسب البحث والتاجر والتصنيف"""
        term = self.search_var.get().lower().strip()
        selected_name = self.vendor_filter_var.get()
        selected_category = self.category_filter_var.get()

        # فلتر التاجر
        if selected_name == "كل التجار" or selected_name not in self.vendor_mapping:
            vendor_id = "all"
        else:
            vendor_id = self.vendor_mapping[selected_name]["uid"]

        if not isinstance(self.products, dict):
            self.setup_products_cards(self.products)
            return

        filtered = {}
        for pid, product in self.products.items():
            if not isinstance(product, dict):
                continue

            match = True

            # فلتر البحث
            if term:
                match = term in product.get("name", "").lower() or term in product.get("desc", "").lower()

            # فلتر التاجر
            if match and vendor_id != "all":
                product_vendor = product.get("vendorId")
                match = product_vendor == vendor_id

            # فلتر التصنيف
            if match and selected_category != "all":
                product_category = product.get("category", "")
                match = product_category == selected_category

            if match:
                filtered[pid] = product

        self.setup_products_cards(filtered if filtered else self.products)
    def load_image_from_url(self, url, size=(150, 150)):
        """تحميل صورة من رابط وعرضها في Tkinter"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"خطأ في تحميل الصورة: {e}")
        return None

    def sort_products(self, sort_type):
        """فرز المنتجات"""
        if not isinstance(self.products, dict):
            return

        items = list(self.products.items())
        valid_items = [(pid, p) for pid, p in items if isinstance(p, dict)]

        if sort_type == "high":
            valid_items.sort(key=lambda x: float(x[1].get("price", 0)), reverse=True)
        elif sort_type == "low":
            valid_items.sort(key=lambda x: float(x[1].get("price", 0)))
        elif sort_type == "name":
            valid_items.sort(key=lambda x: x[1].get("name", "").lower())

        sorted_products = dict(valid_items)
        self.setup_products_cards(sorted_products)

    def setup_products_cards(self, display_data=None):
        """عرض المنتجات في بطاقات مع الصور (مع دعم روابط الإنترنت)"""
        # مسح الإطار القديم
        for widget in self.products_frame.winfo_children():
            widget.destroy()

        # إنشاء كانفاس للتمرير
        canvas = tk.Canvas(self.products_frame, bg="#0f172a", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.products_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#0f172a")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        # تحديد البيانات المراد عرضها
        data_to_show = display_data if display_data is not None else self.products

        if not isinstance(data_to_show, dict):
            data_to_show = {"1": {"name": "منتج تجريبي", "price": 100}}

        row, col = 0, 0
        self.product_images = []

        for pid, product in data_to_show.items():
            if not isinstance(product, dict):
                continue

            # بطاقة المنتج
            card = tk.Frame(scroll_frame, bg="#1e293b", padx=15, pady=15,
                            relief="flat", bd=0, highlightbackground="#334155",
                            highlightthickness=1)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # إطار الصورة
            img_frame = tk.Frame(card, width=120, height=120, bg="#334155")
            img_frame.pack(pady=(0, 10))
            img_frame.pack_propagate(False)

            img_label = tk.Label(img_frame, bg="#334155", text="📦",
                                 font=("Arial", 30), fg="#4efd54")
            img_label.place(relx=0.5, rely=0.5, anchor="center")

            # محاولة تحميل الصورة من الرابط أو من الملف المحلي
            thumbnail_url = product.get('thumbnail', '')

            if thumbnail_url and thumbnail_url.startswith('http'):
                try:
                    import requests
                    from io import BytesIO

                    response = requests.get(thumbnail_url, timeout=10)
                    if response.status_code == 200:
                        img_data = response.content
                        img = Image.open(BytesIO(img_data))
                        img = img.resize((100, 100), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        img_label.config(image=photo, text="")
                        self.product_images.append(photo)
                    else:
                        print(f"فشل تحميل الصورة: {response.status_code}")
                except Exception as e:
                    print(f"خطأ في تحميل الصورة من الرابط: {e}")

            elif thumbnail_url and os.path.exists(thumbnail_url):
                try:
                    img = Image.open(thumbnail_url)
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label.config(image=photo, text="")
                    self.product_images.append(photo)
                except Exception as e:
                    print(f"خطأ في تحميل الصورة المحلية: {e}")

            # اسم المنتج
            name = product.get('name', 'منتج')
            tk.Label(card, text=name, font=("Arial", 13, "bold"),
                     fg="white", bg="#1e293b").pack()

            # السعر
            price = product.get('price', 0)
            tk.Label(card, text=f"{price} EGP", font=("Arial", 12),
                     fg="#4efd54", bg="#1e293b").pack(pady=2)

            # ✅ إضافة اسم التاجر (لو موجود)
            vendor_name = product.get("vendorName")
            if vendor_name:
                tk.Label(card, text=f"🏪 {vendor_name}", font=("Arial", 9),
                         fg="#f59e0b", bg="#1e293b").pack()

            # ✅ زر الإضافة للسلة (معدل ليشمل vendorId و vendorName)
            vid = product.get('vendorId')
            vname = product.get('vendorName')
            add_btn = tk.Button(card, text="➕ أضف للسلة",
                                command=lambda p=pid, n=name, pr=price, vid=vid, vname=vname: self.add_to_cart(p, n, pr,
                                                                                                               vid,
                                                                                                               vname),
                                bg="#4efd54", fg="black",
                                font=("Arial", 10, "bold"),
                                padx=15, pady=5, bd=0, cursor="hand2")
            add_btn.pack(pady=5)

            # تحديث موقع البطاقة
            col += 1
            if col > 4:
                col = 0
                row += 1

        # ضبط أعمدة الشبكة
        for i in range(5):
            scroll_frame.grid_columnconfigure(i, weight=1)
    def setup_services_cards(self, display_data=None):
        """عرض الخدمات في بطاقات"""
        for widget in self.products_frame.winfo_children():
            widget.destroy()

        data_to_show = display_data if display_data is not None else self.services

        if not isinstance(data_to_show, dict) or len(data_to_show) == 0:
            tk.Label(self.products_frame, text="📭 لا توجد خدمات",
                     fg="white", bg="#0f172a", font=("Arial", 14)).pack(pady=50)
            return

        # إنشاء كانفاس للتمرير
        canvas = tk.Canvas(self.products_frame, bg="#0f172a", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.products_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#0f172a")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        row, col = 0, 0
        for sid, service in data_to_show.items():
            if not isinstance(service, dict):
                continue

            card = tk.Frame(scroll_frame, bg="#1e293b", padx=15, pady=15,
                            relief="flat", bd=0, highlightbackground="#334155", highlightthickness=1)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # اسم مقدم الخدمة
            provider = service.get("provider_name", "مقدم خدمة")
            tk.Label(card, text=provider, font=("Arial", 13, "bold"),
                     fg="white", bg="#1e293b").pack()

            # المهنة
            profession = service.get("profession", "خدمة")
            tk.Label(card, text=f"⚡ {profession}", font=("Arial", 11),
                     fg="#4efd54", bg="#1e293b").pack(pady=2)

            # السعر
            rate = service.get("rate", 0)
            rate_type = "ساعة" if service.get("rate_type") == "hour" else "زيارة"
            tk.Label(card, text=f"💰 {rate} EGP / {rate_type}", font=("Arial", 10),
                     fg="#f59e0b", bg="#1e293b").pack(pady=2)

            # الموقع
            location = service.get("location", "غير محدد")
            tk.Label(card, text=f"📍 {location}", font=("Arial", 9),
                     fg="#94a3b8", bg="#1e293b").pack(pady=2)

            # تقييم
            rating = service.get("rating", 0)
            stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
            tk.Label(card, text=stars, font=("Arial", 9),
                     fg="#f59e0b", bg="#1e293b").pack(pady=2)

            # زر الاتصال
            phone = service.get("phone", "")
            if phone:
                call_btn = tk.Button(card, text="📞 اتصل",
                                     command=lambda p=phone: webbrowser.open(f"tel:{p}"),
                                     bg="#25D366", fg="white", bd=0, padx=10, pady=3, cursor="hand2")
                call_btn.pack(pady=5)

            col += 1
            if col > 2:
                col = 0
                row += 1

        for i in range(3):
            scroll_frame.grid_columnconfigure(i, weight=1)
    def add_product_shortcut(self):
        """اختصار لإضافة منتج (للمالك)"""
        self.open_products_manager()

    def add_service_shortcut(self):
        """إضافة خدمة جديدة (للمالك)"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "غير مصرح لك")
            return

        win = tk.Toplevel(self.root)
        win.title("➕ إضافة خدمة جديدة")
        win.geometry("450x500")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="إضافة خدمة جديدة", font=("Arial", 16, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        fields = [
            ("اسم مقدم الخدمة:", "provider_name"),
            ("المهنة (سباك/كهربائي/...):", "profession"),
            ("رقم الهاتف:", "phone"),
            ("السعر:", "rate"),
            ("نوع السعر (hour/visit):", "rate_type"),
            ("المنطقة:", "location"),
            ("الوصف:", "description"),
        ]

        entries = {}
        for label, key in fields:
            frame = tk.Frame(win, bg="#0f172a")
            frame.pack(fill="x", padx=20, pady=5)
            tk.Label(frame, text=label, fg="white", bg="#0f172a", width=20, anchor="w").pack(side="right")
            entries[key] = tk.Entry(frame, width=25, bg="#1e293b", fg="white")
            entries[key].pack(side="left", padx=5)

        entries["rate_type"].insert(0, "hour")

        def save_service():
            data = {}
            for key, entry in entries.items():
                val = entry.get().strip()
                if key == "rate":
                    try:
                        val = float(val)
                    except:
                        messagebox.showerror("خطأ", "السعر يجب أن يكون رقماً")
                        return
                data[key] = val

            if not data.get("provider_name") or not data.get("profession"):
                messagebox.showerror("خطأ", "اسم مقدم الخدمة والمهنة مطلوبان")
                return

            data["provider_id"] = self.current_user_uid
            data["rating"] = 0
            data["reviews_count"] = 0
            data["created_at"] = datetime.now().isoformat()
            data["active"] = True

            try:
                db.reference("Services").push(data)
                messagebox.showinfo("✅", "تم إضافة الخدمة بنجاح")
                win.destroy()
            except Exception as e:
                messagebox.showerror("❌", f"خطأ: {e}")

        tk.Button(win, text="💾 حفظ الخدمة", command=save_service,
                  bg="#4efd54", fg="black", padx=20, pady=5).pack(pady=20)

    def add_product_shortcut(self):
        """اختصار لإضافة منتج (للمالك)"""
        self.open_products_manager()

    # ========================================
    # ========== دوال المستخدم ===============
    # ========================================

    def after_login(self, email):
        """تنفيذ بعد تسجيل الدخول"""
        self.logged_in = True
        self.current_user_email = email
        self.user_indicator.config(text=f"👤 {email[:15]}...")
        self.refresh_ui()

    def logout(self):
        """تسجيل الخروج"""
        self.logged_in = False
        self.current_user_email = None
        clear_session()
        self.user_indicator.config(text="👤 ضيف")
        self.refresh_ui()
        messagebox.showinfo("✅", "تم تسجيل الخروج")

    def show_login_options(self):
        """إظهار خيارات تسجيل الدخول"""
        popup = tk.Menu(self.root, tearoff=0, bg="#1e293b", fg="white")
        if self.logged_in:
            popup.add_command(label="تسجيل خروج", command=self.logout)
        else:
            popup.add_command(label="تسجيل دخول",
                              command=lambda: login_window(self.root, self.after_login))
            popup.add_command(label="تسجيل جديد",
                              command=lambda: register_window(self.root, self.after_login))
        try:
            popup.tk_popup(self.user_indicator.winfo_rootx(),
                           self.user_indicator.winfo_rooty() + 20)
        except:
            pass

    def refresh_ui(self):
        """إعادة بناء الواجهة بعد تغيير حالة المستخدم"""
        # حفظ البيانات الحالية
        current_data = self.data
        current_products = self.products

        # إعادة إنشاء الواجهة
        for widget in self.root.winfo_children():
            widget.destroy()

        self.create_modern_ui()
        self.data = current_data
        self.products = current_products
        self.load_products()

    def show_owner_buttons(self):
        """تفعيل وضع المالك"""
        self.owner_mode = True
        messagebox.showinfo("✅", "تم تفعيل صلاحيات المالك")
        self.refresh_ui()

    # ========================================
    # ========== دوال السلة ==================
    # ========================================

    def add_to_cart(self, product_id, product_name, product_price, vendor_id=None, vendor_name=None):
        """إضافة منتج للسلة"""
        if not self.logged_in:
            messagebox.showwarning("تنبيه", "يجب تسجيل الدخول أولاً")
            return

        product_id = str(product_id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] += 1
        else:
            self.cart[product_id] = {
                'name': product_name,
                'price': float(product_price),
                'quantity': 1,
                'vendorId': vendor_id,
                'vendor_name': vendor_name
            }

        self.update_cart_counter()
        messagebox.showinfo("✅", f"تمت إضافة {product_name}")
    def update_cart_counter(self):
        """تحديث عداد السلة"""
        total = sum(item['quantity'] for item in self.cart.values())
        self.cart_indicator.config(text=f"🛒 {total}")

    def show_cart(self):
        """عرض محتويات السلة"""
        if not self.cart:
            messagebox.showinfo("السلة فارغة", "لم تقم بإضافة أي منتجات")
            return

        win = tk.Toplevel(self.root)
        win.title("🛍️ سلة المشتريات")
        win.geometry("600x500")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="سلة المشتريات", font=("Arial", 18, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        frame = tk.Frame(win, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=10)

        total_price = 0
        for pid, item in self.cart.items():
            item_total = item['price'] * item['quantity']
            total_price += item_total

            item_frame = tk.Frame(frame, bg="#1e293b", pady=10, padx=15)
            item_frame.pack(fill="x", pady=5)

            tk.Label(item_frame, text=item['name'],
                     font=("Arial", 12, "bold"),
                     fg="white", bg="#1e293b",
                     width=20, anchor="w").pack(side="right")

            tk.Label(item_frame, text=f"{item['price']} EGP",
                     fg="#4efd54", bg="#1e293b",
                     width=8).pack(side="right")

            # الكمية مع أزرار التحكم
            qty_frame = tk.Frame(item_frame, bg="#1e293b")
            qty_frame.pack(side="left")

            tk.Button(qty_frame, text="+",
                      command=lambda p=pid: self.adjust_quantity(p, 1, win),
                      bg="#4efd54", fg="black",
                      width=2, bd=0, cursor="hand2").pack(side="left", padx=2)

            tk.Label(qty_frame, text=str(item['quantity']),
                     fg="white", bg="#1e293b", width=2).pack(side="left")

            tk.Button(qty_frame, text="-",
                      command=lambda p=pid: self.adjust_quantity(p, -1, win),
                      bg="#EC0B0B", fg="white",
                      width=2, bd=0, cursor="hand2").pack(side="left", padx=2)

            tk.Button(qty_frame, text="✕",
                      command=lambda p=pid: self.remove_from_cart(p, win),
                      bg="#64748b", fg="white",
                      width=2, bd=0, cursor="hand2").pack(side="left", padx=2)

        # الإجمالي
        tk.Label(win, text=f"الإجمالي: {total_price} EGP",
                 font=("Arial", 16, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        # أزرار الإجراءات
        btn_frame = tk.Frame(win, bg="#0f172a")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🔄 متابعة التسوق",
                  command=win.destroy,
                  bg="#334155", fg="white",
                  padx=20, bd=0, cursor="hand2").pack(side="right", padx=10)

        tk.Button(btn_frame, text="💳 إتمام الشراء",
                  command=lambda: self.checkout(win),
                  bg="#4efd54", fg="black",
                  padx=20, bd=0, cursor="hand2").pack(side="left", padx=10)

    def adjust_quantity(self, product_id, change, cart_win):
        """تعديل كمية منتج في السلة"""
        if product_id in self.cart:
            self.cart[product_id]['quantity'] += change
            if self.cart[product_id]['quantity'] <= 0:
                del self.cart[product_id]
            self.update_cart_counter()
            cart_win.destroy()
            self.show_cart()

    def remove_from_cart(self, product_id, cart_win):
        """حذف منتج من السلة"""
        if product_id in self.cart:
            del self.cart[product_id]
            self.update_cart_counter()
            cart_win.destroy()
            self.show_cart()

    def checkout(self, cart_win):
        """إتمام عملية الشراء"""
        cart_win.destroy()

        if not self.logged_in:
            messagebox.showwarning("تنبيه", "يجب تسجيل الدخول")
            return

        win = tk.Toplevel(self.root)
        win.title("📋 إتمام الشراء")
        win.geometry("450x500")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="بيانات الشحن", font=("Arial", 18, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        fields_frame = tk.Frame(win, bg="#0f172a")
        fields_frame.pack(pady=10)

        tk.Label(fields_frame, text="الاسم:", fg="white", bg="#0f172a").pack()
        name_ent = tk.Entry(fields_frame, width=30, font=("Arial", 11),
                            bg="#1e293b", fg="white", bd=0, insertbackground="white")
        name_ent.pack(pady=5)

        tk.Label(fields_frame, text="رقم الهاتف:", fg="white", bg="#0f172a").pack()
        phone_ent = tk.Entry(fields_frame, width=30, font=("Arial", 11),
                             bg="#1e293b", fg="white", bd=0, insertbackground="white")
        phone_ent.pack(pady=5)

        tk.Label(fields_frame, text="العنوان:", fg="white", bg="#0f172a").pack()
        address_ent = tk.Entry(fields_frame, width=30, font=("Arial", 11),
                               bg="#1e293b", fg="white", bd=0, insertbackground="white")
        address_ent.pack(pady=5)

        # ملخص الطلب
        summary_frame = tk.Frame(win, bg="#1e293b", padx=15, pady=10)
        summary_frame.pack(pady=10, fill="x", padx=30)

        summary = "المنتجات:\n" + "-" * 20 + "\n"
        total = 0
        for item in self.cart.values():
            item_total = item['price'] * item['quantity']
            total += item_total
            summary += f"• {item['name']} x{item['quantity']} = {item_total} EGP\n"
        summary += "-" * 20 + f"\nالإجمالي: {total} EGP"

        tk.Label(summary_frame, text=summary, justify="right",
                 fg="white", bg="#1e293b").pack()

        def confirm():
            name = name_ent.get().strip()
            phone = phone_ent.get().strip()
            address = address_ent.get().strip()

            # طباعة محتويات السلة للفحص
            print("🔍 محتويات السلة:", self.cart)

            if not all([name, phone, address]):
                messagebox.showwarning("خطأ", "يرجى ملء جميع الحقول")
                return

            # حفظ الطلب
            orders = []
            if os.path.exists("orders.json"):
                with open("orders.json", "r", encoding="utf-8") as f:
                    try:
                        orders = json.load(f)
                    except:
                        orders = []

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # جلب رقم التاجر من أول منتج في السلة
            first_item = list(self.cart.values())[0]
            vendor_id = first_item.get('vendorId')
            print(f"🔍 vendor_id: {vendor_id}")

            # جلب رقم التاجر
            vPhone = "01005032186"  # افتراضي
            if vendor_id:
                try:
                    user_ref = db.reference(f"users/{vendor_id}")
                    user_data = user_ref.get()
                    if user_data:
                        vPhone = user_data.get("phone", "01005032186")
                        print(f"📱 رقم التاجر من Firebase: {vPhone}")
                    else:
                        print("❌ المستخدم غير موجود")
                except Exception as e:
                    print(f"خطأ في جلب رقم التاجر: {e}")

            print(f"📱 الرقم المستخدم: {vPhone}")

            for pid, item in self.cart.items():
                order = {
                    "user": self.current_user_email,
                    "product_name": item['name'],
                    "product_price": item['price'],
                    "quantity": item['quantity'],
                    "total": item['price'] * item['quantity'],
                    "buyer_name": name,
                    "buyer_phone": phone,
                    "buyer_address": address,
                    "timestamp": timestamp
                }
                orders.append(order)

            with open("orders.json", "w", encoding="utf-8") as f:
                json.dump(orders, f, ensure_ascii=False, indent=4)

            # رسالة واتساب
            msg = f"🔔 طلب جديد\nالاسم: {name}\nالهاتف: {phone}\nالعنوان: {address}\n\n{summary}"
            webbrowser.open(f"https://wa.me/{vPhone}?text={msg}")

            # تفريغ السلة
            self.cart = {}
            self.update_cart_counter()

            messagebox.showinfo("✅ نجاح", "تم تأكيد الطلب")
            win.destroy()

        tk.Button(win, text="تأكيد الطلب", command=confirm,
                  bg="#4efd54", fg="black", font=("Arial", 11, "bold"),
                  padx=20, pady=5, bd=0, cursor="hand2").pack(pady=10)
    # ========================================
    # ========== النوافذ الأخرى ==============
    # ========================================

    def open_products_manager(self):
        """فتح مدير المنتجات (للمالك فقط)"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "مدير المنتجات متاح فقط للمالك")
            return

        ProductManager(self.root, self.data, self.update_products).open_manager()

    def update_products(self, new_data):
        """تحديث المنتجات بعد التعديل"""
        self.products = new_data
        self.data = new_data
        self.setup_products_cards()

    def open_transactions_window(self):
        """عرض سجل المشتريات"""
        if not self.logged_in:
            messagebox.showwarning("تنبيه", "يجب تسجيل الدخول أولاً")
            return

        win = tk.Toplevel(self.root)
        win.title("📋 سجل المشتريات")
        win.geometry("800x450")
        win.configure(bg="#0f172a")
        win.transient(self.root)

        tk.Label(win, text="سجل المشتريات", font=("Arial", 18, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        frame = tk.Frame(win, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=10)

        columns = ("المنتج", "السعر", "المشتري", "الهاتف", "التاريخ")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)

        # تنسيق الجدول
        style = ttk.Style()
        style.configure("Treeview", background="#1e293b", foreground="white",
                        fieldbackground="#1e293b", rowheight=30)
        style.configure("Treeview.Heading", background="#2d3a4f", foreground="#4efd54")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # تحميل البيانات
        if os.path.exists("orders.json"):
            with open("orders.json", "r", encoding="utf-8") as f:
                try:
                    orders = json.load(f)
                    for order in orders:
                        tree.insert("", "end", values=(
                            order.get("product_name", ""),
                            order.get("product_price", ""),
                            order.get("buyer_name", ""),
                            order.get("buyer_phone", ""),
                            order.get("timestamp", "")
                        ))
                except Exception as e:
                    print(f"خطأ في قراءة الطلبات: {e}")

        tk.Button(win, text="❌ إغلاق", command=win.destroy,
                  bg="#EC0B0B", fg="white", padx=20, bd=0, cursor="hand2").pack(pady=10)

    def open_activation_window(self):
        """نافذة تفعيل النسخة"""
        win = tk.Toplevel(self.root)
        win.title("🔑 تفعيل النسخة")
        win.geometry("350x200")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="تفعيل النسخة الكاملة", font=("Arial", 14, "bold"),
                 fg="#4efd54", bg="#0f172a").pack(pady=10)

        tk.Label(win, text="أدخل مفتاح التفعيل:", fg="white", bg="#0f172a").pack()
        key_ent = tk.Entry(win, width=30, show="*", bg="#1e293b", fg="white", bd=0)
        key_ent.pack(pady=5)

        def activate():
            if lm.activate(self.current_user_email or "User", key_ent.get()):
                messagebox.showinfo("✅", "تم التفعيل بنجاح")
                self.owner_mode = True
                win.destroy()
                self.refresh_ui()
            else:
                messagebox.showerror("❌", "مفتاح غير صالح")

        tk.Button(win, text="تفعيل", command=activate,
                  bg="#4efd54", fg="black", padx=20, bd=0, cursor="hand2").pack(pady=10)

    def open_purchase_window(self, product_name="الرخصة الكاملة"):
        """نافذة شراء الرخصة"""
        webbrowser.open(f"https://wa.me/{WHATSAPP_NUM}")

    def open_whatsapp(self):
        """فتح واتساب"""
        webbrowser.open(f"https://wa.me/{WHATSAPP_NUM}")

    def open_security_window(self):
        """نافذة الأمان - إدارة المستخدمين والمنتجات والخدمات"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "نافذة الأمان للمالك فقط")
            return

        win = tk.Toplevel(self.root)
        win.title("🔒 لوحة التحكم - الأمان")
        win.geometry("900x700")
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.grab_set()

        # Notebook (تبويبات)
        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # تبويب المستخدمين
        users_frame = tk.Frame(notebook, bg="#0f172a")
        notebook.add(users_frame, text="👥 المستخدمين")
        self.create_users_tab(users_frame)

        # تبويب المنتجات
        products_frame = tk.Frame(notebook, bg="#0f172a")
        notebook.add(products_frame, text="📦 المنتجات")
        self.create_products_admin_tab(products_frame)

        # تبويب الخدمات
        services_frame = tk.Frame(notebook, bg="#0f172a")
        notebook.add(services_frame, text="🛠️ الخدمات")
        self.create_services_admin_tab(services_frame)
    def create_users_tab(self, parent):
        """تبويب إدارة المستخدمين"""
        # إطار البحث
        search_frame = tk.Frame(parent, bg="#0f172a")
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="بحث:", fg="white", bg="#0f172a").pack(side="right", padx=5)
        search_entry = tk.Entry(search_frame, width=30, bg="#1e293b", fg="white")
        search_entry.pack(side="right", padx=5)

        def filter_users():
            term = search_entry.get().lower()
            for item in tree.get_children():
                tree.delete(item)
            for user in self.all_users:
                if term in user[0].lower() or term in user[1].lower():
                    tree.insert("", "end", values=user)

        search_entry.bind("<KeyRelease>", lambda e: filter_users())

        # جدول المستخدمين
        columns = ("البريد", "الدور", "التاجر", "حالة الاشتراك", "إجراءات")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # تحميل المستخدمين
        self.all_users = []
        try:
            users = db.reference("users").get() or {}
            for uid, user_data in users.items():
                email = user_data.get("email", "")
                role = user_data.get("role", "user")
                store_name = user_data.get("storeName", "-")
                subscription = ""
                if role == "trial":
                    trial_end = user_data.get("trial_end", 0)
                    if trial_end:
                        days = (trial_end - int(datetime.now().timestamp() * 1000)) // (24 * 60 * 60 * 1000)
                        subscription = f"{days} يوم متبقي"
                elif role in ["seller_monthly", "seller_yearly"]:
                    sub_end = user_data.get("subscription_end", "")
                    if sub_end:
                        sub_end_date = datetime.fromisoformat(sub_end.replace('Z', '+00:00'))
                        days = (sub_end_date - datetime.now()).days
                        subscription = f"ينتهي بعد {days} يوم"

                self.all_users.append((email, role, store_name, subscription, uid))
                tree.insert("", "end", values=(email, role, store_name, subscription))
        except Exception as e:
            tk.Label(parent, text=f"خطأ: {e}", fg="red", bg="#0f172a").pack()

        # أزرار الإجراءات
        actions_frame = tk.Frame(parent, bg="#0f172a")
        actions_frame.pack(fill="x", padx=10, pady=10)

        def get_selected_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "اختر مستخدم أولاً")
                return None
            item = tree.item(selected[0])
            values = item['values']
            # البحث عن UID من الـ all_users
            for user in self.all_users:
                if user[0] == values[0]:
                    return user[4], values[0], values[1]
            return None

        def upgrade_to_monthly():
            result = get_selected_user()
            if result:
                uid, email, current_role = result
                if current_role == "owner":
                    messagebox.showwarning("تنبيه", "لا يمكن ترقية المالك")
                    return
                end_date = (datetime.now() + timedelta(days=30)).isoformat()
                db.reference(f"users/{uid}").update({
                    "role": "seller_monthly",
                    "subscription_end": end_date
                })
                messagebox.showinfo("✅", f"تم ترقية {email} إلى شهري")
                filter_users()

        def upgrade_to_yearly():
            result = get_selected_user()
            if result:
                uid, email, current_role = result
                if current_role == "owner":
                    messagebox.showwarning("تنبيه", "لا يمكن ترقية المالك")
                    return
                end_date = (datetime.now() + timedelta(days=365)).isoformat()
                db.reference(f"users/{uid}").update({
                    "role": "seller_yearly",
                    "subscription_end": end_date
                })
                messagebox.showinfo("✅", f"تم ترقية {email} إلى سنوي")
                filter_users()

        def suspend_user():
            result = get_selected_user()
            if result:
                uid, email, current_role = result
                if current_role == "owner":
                    messagebox.showwarning("تنبيه", "لا يمكن إيقاف المالك")
                    return
                if messagebox.askyesno("تأكيد", f"هل تريد إيقاف {email}؟"):
                    db.reference(f"users/{uid}").update({"role": "suspended"})
                    messagebox.showinfo("✅", f"تم إيقاف {email}")
                    filter_users()

        def delete_user():
            result = get_selected_user()
            if result:
                uid, email, current_role = result
                if current_role == "owner":
                    messagebox.showwarning("تنبيه", "لا يمكن حذف المالك")
                    return
                if messagebox.askyesno("تأكيد", f"⚠️ هل تريد حذف {email} نهائياً؟ هذا سيحذف جميع منتجاته وخدماته"):
                    # حذف منتجات التاجر
                    db.reference(f"VendorProducts/{uid}").delete()
                    # حذف خدمات التاجر (بدون order_by_child)
                    services_ref = db.reference("Services")
                    all_services = services_ref.get() or {}
                    for sid, service in all_services.items():
                        if service.get("provider_id") == uid:
                            services_ref.child(sid).delete()
                    # حذف المستخدم
                    db.reference(f"users/{uid}").delete()
                    messagebox.showinfo("✅", f"تم حذف {email}")
                    filter_users()
        btn_frame = tk.Frame(actions_frame, bg="#0f172a")
        btn_frame.pack()

        tk.Button(btn_frame, text="⬆️ ترقية شهري", command=upgrade_to_monthly,
                  bg="#4efd54", fg="black", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="⬆️ ترقية سنوي", command=upgrade_to_yearly,
                  bg="#f59e0b", fg="black", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="⛔ إيقاف", command=suspend_user,
                  bg="#e67e22", fg="white", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="🗑️ حذف", command=delete_user,
                  bg="#e74c3c", fg="white", padx=10, pady=5).pack(side="right", padx=5)

    def create_products_admin_tab(self, parent):
        """تبويب إدارة المنتجات (للمالك)"""
        columns = ("المنتج", "السعر", "التاجر", "الحالة", "الإجراءات")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def load_products():
            for item in tree.get_children():
                tree.delete(item)

            # منتجات رئيسية
            products = PRODUCTS_REF.get() or {}
            for pid, p in products.items():
                if isinstance(p, dict):
                    tree.insert("", "end", values=(
                        p.get("name", ""),
                        p.get("price", 0),
                        "الموقع",
                        "نشط" if p.get("active", True) else "موقوف",
                        f"main|{pid}"
                    ))

            # منتجات التجار
            vendor_products = db.reference("VendorProducts").get() or {}
            for vendor_id, items in vendor_products.items():
                vendor_name = self.get_vendor_name(vendor_id)
                for prod_id, prod in items.items():
                    if isinstance(prod, dict):
                        tree.insert("", "end", values=(
                            prod.get("name", ""),
                            prod.get("price", 0),
                            vendor_name,
                            "نشط" if prod.get("active", True) else "موقوف",
                            f"vendor|{vendor_id}|{prod_id}"
                        ))

        def delete_product():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "اختر منتجاً")
                return
            item = tree.item(selected[0])
            values = item['values']
            product_id_data = values[4]

            if messagebox.askyesno("تأكيد", f"هل تريد حذف {values[0]}؟"):
                parts = product_id_data.split("|")
                if parts[0] == "main":
                    PRODUCTS_REF.child(parts[1]).delete()
                else:
                    db.reference(f"VendorProducts/{parts[1]}/{parts[2]}").delete()
                messagebox.showinfo("✅", "تم الحذف")
                load_products()

        def toggle_product_status():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "اختر منتجاً")
                return
            item = tree.item(selected[0])
            values = item['values']
            product_id_data = values[4]
            current_status = values[3]
            new_status = current_status == "موقوف"

            parts = product_id_data.split("|")
            if parts[0] == "main":
                PRODUCTS_REF.child(parts[1]).update({"active": new_status})
            else:
                db.reference(f"VendorProducts/{parts[1]}/{parts[2]}").update({"active": new_status})

            messagebox.showinfo("✅", f"تم {'تفعيل' if new_status else 'إيقاف'} المنتج")
            load_products()

        btn_frame = tk.Frame(parent, bg="#0f172a")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🗑️ حذف منتج", command=delete_product,
                  bg="#e74c3c", fg="white", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="⛔ إيقاف/تفعيل", command=toggle_product_status,
                  bg="#f59e0b", fg="black", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="🔄 تحديث", command=load_products,
                  bg="#3498db", fg="white", padx=10, pady=5).pack(side="right", padx=5)

        load_products()

    def create_services_admin_tab(self, parent):
        """تبويب إدارة الخدمات (للمالك)"""
        columns = ("الخدمة", "مقدم الخدمة", "المهنة", "السعر", "الحالة", "الإجراءات")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def load_services():
            for item in tree.get_children():
                tree.delete(item)

            services = db.reference("Services").get() or {}
            for sid, service in services.items():
                if isinstance(service, dict):
                    provider = service.get("provider_name", "غير معروف")
                    profession = service.get("profession", "-")
                    rate = service.get("rate", 0)
                    tree.insert("", "end", values=(
                        sid[:8],
                        provider,
                        profession,
                        f"{rate} EGP",
                        "نشط" if service.get("active", True) else "موقوف",
                        sid
                    ))

        def delete_service():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "اختر خدمة")
                return
            item = tree.item(selected[0])
            sid = item['values'][5]

            if messagebox.askyesno("تأكيد", f"هل تريد حذف هذه الخدمة؟"):
                db.reference(f"Services/{sid}").delete()
                messagebox.showinfo("✅", "تم الحذف")
                load_services()

        def toggle_service_status():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("تنبيه", "اختر خدمة")
                return
            item = tree.item(selected[0])
            sid = item['values'][5]
            current_status = item['values'][4]
            new_status = current_status == "موقوف"

            db.reference(f"Services/{sid}").update({"active": new_status})
            messagebox.showinfo("✅", f"تم {'تفعيل' if new_status else 'إيقاف'} الخدمة")
            load_services()

        btn_frame = tk.Frame(parent, bg="#0f172a")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🗑️ حذف خدمة", command=delete_service,
                  bg="#e74c3c", fg="white", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="⛔ إيقاف/تفعيل", command=toggle_service_status,
                  bg="#f59e0b", fg="black", padx=10, pady=5).pack(side="right", padx=5)
        tk.Button(btn_frame, text="🔄 تحديث", command=load_services,
                  bg="#3498db", fg="white", padx=10, pady=5).pack(side="right", padx=5)

        load_services()

    def open_backup_manager(self):
        """مدير النسخ الاحتياطي"""
        if not self.logged_in or not self.owner_mode:
            messagebox.showwarning("تنبيه", "مدير النسخ الاحتياطي للمالك فقط")
            return
        messagebox.showinfo("💾", "مدير النسخ الاحتياطي قيد التطوير")

    def open_settings_window(self):
        """نافذة الإعدادات"""
        messagebox.showinfo("⚙️", "الإعدادات قيد التطوير")

    def debug_products(self):
        """تشخيص المنتجات"""
        print(f"📊 عدد المنتجات: {len(self.products) if isinstance(self.products, dict) else 0}")
        if isinstance(self.products, dict):
            for pid, p in list(self.products.items())[:5]:
                print(f"  - {pid}: {p.get('name') if isinstance(p, dict) else 'غير صالح'}")

    def check_queue(self):
        """التحقق من قائمة الانتظار"""
        try:
            while True:
                new_data = self.queue.get_nowait()
                self.data = new_data
                self.products = new_data
        except queue.Empty:
            pass
        self.root.after(200, self.check_queue)

# ============================================
# ========== تشغيل البرنامج ==================
# ============================================

if __name__ == "__main__":
    root = tk.Tk()
    app = ZainStoreApp(root)
    root.mainloop()