import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

USERS_FILE = "users.json"
current_user = None


# --- دوال التسجيل والدخول ---
def save_user(email, password):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

    with open(USERS_FILE, "r") as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            users = []

    for u in users:
        if u["email"].strip().lower() == email.strip().lower():
            u["password"] = password.strip()
            break
    else:
        users.append({"email": email.strip(), "password": password.strip()})

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def check_user(email, password):
    with open(USERS_FILE, "r") as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            users = []
    for u in users:
        if u["email"].strip().lower() == email.strip().lower() and u["password"].strip() == password.strip():
            return u
    return None


def register_window(root):
    win = tk.Toplevel(root)
    win.title("تسجيل مستخدم")
    tk.Label(win, text="البريد الإلكتروني:").pack()
    email_ent = tk.Entry(win)
    email_ent.pack()
    tk.Label(win, text="كلمة المرور:").pack()
    pass_ent = tk.Entry(win, show="*")
    pass_ent.pack()

    def register():
        email = email_ent.get()
        password = pass_ent.get()
        if email and password:
            save_user(email, password)
            messagebox.showinfo("نجاح ✅", "تم التسجيل بنجاح")
            win.destroy()
        else:
            messagebox.showerror("خطأ", "يرجى إدخال البيانات كاملة")

    tk.Button(win, text="تسجيل", command=register).pack(pady=10)


def login_window(root):
    global current_user
    win = tk.Toplevel(root)
    win.title("تسجيل دخول")
    tk.Label(win, text="البريد الإلكتروني:").pack()
    email_ent = tk.Entry(win)
    email_ent.pack()
    tk.Label(win, text="كلمة المرور:").pack()
    pass_ent = tk.Entry(win, show="*")
    pass_ent.pack()

    def login():
        global current_user
        email = email_ent.get()
        password = pass_ent.get()
        user = check_user(email, password)
        if user:
            current_user = user
            messagebox.showinfo("نجاح ✅", f"تم تسجيل الدخول: {email}")
            win.destroy()
        else:
            messagebox.showerror("خطأ", "بيانات غير صحيحة")

    tk.Button(win, text="دخول", command=login).pack(pady=10)


def buy_item(item_name, item_price):
    global current_user
    if current_user:
        messagebox.showinfo("نجاح ✅", f"تم شراء {item_name} بسعر {item_price} بواسطة {current_user['email']}")
    else:
        messagebox.showerror("خطأ", "يرجى تسجيل الدخول أولًا قبل الشراء")


# --- قائمة المنتجات التجريبية ---
products_data = [
    {"name": "لابتوب احترافي", "price": 5000},
    {"name": "خدمة صيانة", "price": 300},
    {"name": "شاشة 60 بوصة", "price": 23000},
    {"name": "هاتف سامسونج", "price": 1500},
    {"name": "سماعات بلوتوث", "price": 500}
]


# --- دالة عرض المنتجات في جدول ---
def show_products_table(root):
    # نافذة جديدة لعرض المنتجات
    products_win = tk.Toplevel(root)
    products_win.title("الواجهة التجارية الأنيقة")
    products_win.geometry("600x500")

    # --- خانة إدخال البحث + زر ---
    search_frame = tk.Frame(products_win)
    search_frame.pack(pady=10)

    search_entry = tk.Entry(search_frame, width=30)
    search_entry.pack(side="left", padx=5)

    def search():
        term = search_entry.get().lower()
        filtered = [item for item in products_data if term in item["name"].lower()]
        update_table(filtered)

    search_button = tk.Button(search_frame, text="بحث", command=search)
    search_button.pack(side="left", padx=5)

    # --- أزرار الفرز ---
    sort_frame = tk.Frame(products_win)
    sort_frame.pack(pady=10)

    def sort_high():
        update_table(sorted(products_data, key=lambda x: x["price"], reverse=True))

    def sort_low():
        update_table(sorted(products_data, key=lambda x: x["price"]))

    def sort_name():
        update_table(sorted(products_data, key=lambda x: x["name"].lower()))

    tk.Button(sort_frame, text="الأعلى سعرًا", command=sort_high).pack(side="left", padx=5)
    tk.Button(sort_frame, text="الأقل سعرًا", command=sort_low).pack(side="left", padx=5)
    tk.Button(sort_frame, text="أبجديًا", command=sort_name).pack(side="left", padx=5)

    # --- جدول المنتجات ---
    table_frame = tk.Frame(products_win)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(table_frame, columns=("name", "price"), show="headings")
    tree.heading("name", text="اسم المنتج")
    tree.heading("price", text="السعر")
    tree.column("name", width=250)
    tree.column("price", width=100)

    # إضافة شريط تمرير
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def update_table(data):
        # مسح الجدول القديم
        for row in tree.get_children():
            tree.delete(row)
        # إدخال البيانات الجديدة
        for item in data:
            tree.insert("", tk.END, values=(item["name"], item["price"]))

    update_table(products_data)

    # زر شراء المنتج المحدد
    def buy_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "الرجاء اختيار منتج أولاً")
            return

        item = tree.item(selected[0])['values']
        buy_item(item[0], item[1])

    tk.Button(products_win, text="شراء المنتج المحدد", command=buy_selected,
              bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=10)


# --- الدالة الرئيسية ---
def main():
    global root
    root = tk.Tk()
    root.title("Zain Store")
    root.geometry("300x250")

    # الأزرار الرئيسية
    tk.Button(root, text="تسجيل مستخدم جديد",
              command=lambda: register_window(root),
              bg="#4efd54", fg="black").pack(pady=5)

    tk.Button(root, text="تسجيل دخول",
              command=lambda: login_window(root),
              bg="#4efd54", fg="black").pack(pady=5)

    tk.Button(root, text="عرض المنتجات",
              command=lambda: show_products_table(root),
              bg="#FF9800", fg="black").pack(pady=5)

    tk.Button(root, text="خروج",
              command=root.destroy,
              bg="#EC0B0B", fg="white").pack(pady=5)

    root.mainloop()


# --- تشغيل البرنامج ---
if __name__ == "__main__":
    main()