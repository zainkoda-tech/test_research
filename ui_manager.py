import json
import tkinter as tk
from tkinter import ttk
import os

# --- 1. قسم الإعدادات والتنسيق (Theme Engine) ---
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "bg_color": "#121212",  # خلفية داكنة
    "fg_color": "#00ff00",  # أخضر فسفوري
    "table_bg": "#1e1e1e",
    "font_size": 10
}


def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
    except:
        pass
    return DEFAULT_SETTINGS.copy()


def apply_custom_style(settings):
    style = ttk.Style()
    style.theme_use("clam")
    bg = settings.get("table_bg", "#1e1e1e")
    fg = settings.get("fg_color", "#4efd54")

    style.configure("Treeview", background=bg, foreground="white",
                    fieldbackground=bg, rowheight=30, borderwidth=0)
    style.configure("Treeview.Heading", background="#2e2e2e",
                    foreground=fg, font=("Arial", 10, "bold"))


def apply_settings_to_ui(root, settings):
    apply_custom_style(settings)
    root.configure(bg=settings["bg_color"])


# --- 2. قسم الكلاس المنظم (App Class) ---
class ZainStoreApp:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()

        # ضبط إعدادات النافذة
        self.root.title("Mr. Zain Store Engine")
        self.root.geometry("1100x750")

        # تطبيق التنسيق فوراً
        apply_settings_to_ui(self.root, self.settings)

        # بناء الواجهة بالترتيب الصحيح لإنهاء الفوضى
        self.create_header()  # 1. العنوان
        self.create_table()  # 2. الجدول
        self.setup_ui()  # 3. الأزرار (الفوتر)

    def create_header(self):
        header = tk.Frame(self.root, bg=self.settings["bg_color"], pady=10)
        header.pack(fill="x")
        tk.Label(header, text="اقتني متجرك الذكي - Acquire Your Smart Store",
                 font=("Arial", 18, "bold"), fg=self.settings["fg_color"],
                 bg=self.settings["bg_color"]).pack()

    def create_table(self):
        table_frame = tk.Frame(self.root, bg=self.settings["bg_color"])
        table_frame.pack(fill="both", expand=True, padx=20, pady=5)

        columns = ("desc", "price", "name")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

        self.tree.heading("name", text="اسم المنتج")
        self.tree.heading("price", text="السعر")
        self.tree.heading("desc", text="الوصف")

        for col in columns:
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(fill="both", expand=True)

    def setup_ui(self):
        # مصفوفة الأزرار المنظمة (6 أعمدة × صفين)
        footer = tk.Frame(self.root, bg=self.settings["bg_color"], pady=10)
        footer.pack(fill="x", side="bottom")

        accent = self.settings["fg_color"]
        # (النص، اللون، الصف، العمود) - يمكنك ربط الـ Command هنا
        btns = [
            ("تسجيل دخول", accent, 0, 5), ("مدير المنتجات", accent, 0, 4),
            ("WhatsApp", "#25D366", 0, 3), ("Security", "#EC0B0B", 0, 2),
            ("Backup", "#007ACC", 0, 1), ("Close", "#EC0B0B", 0, 0),
            ("License", "#16DA3A", 1, 5), ("Sonic", "#FF9800", 1, 4),
            ("سجل المشتريات", "#007ACC", 1, 3), ("SITING TN", "#007ACC", 1, 2),
            ("تفعيل النسخة", accent, 1, 1), ("شراء رخصة", "#16DA3A", 1, 0)
        ]

        for txt, bg, r, c in btns:
            btn = tk.Button(footer, text=txt, bg=bg, fg="white" if bg != "#00ff00" else "black",
                            font=("Arial", 9, "bold"), width=15, relief="flat", pady=5)
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            # تأثير الإضاءة
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="white", fg="black"))
            btn.bind("<Leave>", lambda e, b=btn, ob=bg: b.config(bg=ob, fg="white" if ob != "#00ff00" else "black"))

        for i in range(6): footer.grid_columnconfigure(i, weight=1)


# --- 3. تشغيل البرنامج ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ZainStoreApp(root)
    root.mainloop()
