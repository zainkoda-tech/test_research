import tkinter as tk
from tkinter import messagebox
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime


# --- وظائف الابن التاسع (الرقابة والربط) ---

def initialize_zain_system():
    """تفعيل الذاكرة الداخلية ومنع العطب في الاتصال"""
    if not firebase_admin._apps:
        try:
            # التأكد من وجود ملف المفتاح في المجلد
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://g10-sovereign-default-rtdb.europe-west1.firebasedatabase.app/'
            })
            print("الابن التاسع: الاتصال بالمتجر مستقر وآمن.")
            return db.reference('/')
        except Exception as e:
            print(f"عطب في النظام: {e}")
            return None
    return db.reference('/')


def send_to_store(data):
    """تحويل المدخلات إلى مخرجات في المتجر الاحترافي"""
    root = initialize_zain_system()
    if root:
        try:
            # إضافة توقيت إضافي للقراءة البشرية
            if 'timestamp' in data and data['timestamp'] == {".sv": "timestamp"}:
                data['readable_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # أرشفة الطلب في المسار 'orders'
            new_order = root.child('orders').push(data)
            print(f"✅ تم أرشفة الطلب: {new_order.key}")
            return True
        except Exception as e:
            print(f"فشل الأرشفة: {e}")
            return False
    return False


def test_firebase_connection():
    """اختبار الاتصال بقاعدة البيانات"""
    root = initialize_zain_system()
    if root:
        try:
            print("\n" + "=" * 50)
            print("🔍 اختبار الاتصال بـ Firebase:")
            print("=" * 50)

            # اختبار المسار Products
            products = root.child('Products').get()
            if products:
                print(f"✅ المسار 'Products': {len(products)} منتج")
                for key, product in products.items():
                    if isinstance(product, dict):
                        print(f"   - {product.get('name', 'منتج')}: {product.get('price', 0)} SAR")
            else:
                print("⚠️ المسار 'Products' لا يحتوي على منتجات")

            # اختبار المسار products (صغير)
            products_small = root.child('products').get()
            if products_small:
                print(f"✅ المسار 'products': {len(products_small)} منتج")
            else:
                print("ℹ️ المسار 'products' غير موجود أو فارغ")

            print("=" * 50)
            return True

        except Exception as e:
            print(f"❌ خطأ في الاتصال: {e}")
            return False


# --- واجهة الابن العاشر (نافذة الشراء الاحترافية) ---

def open_buy_window(product_name="منتج تجريبي", product_price=0, product_id=None):
    buy_window = tk.Toplevel()
    buy_window.title("نظام الشراء - الابن العاشر")
    buy_window.geometry("400x500")
    buy_window.configure(bg="#f4f7f6")

    # عنوان النافذة
    tk.Label(buy_window, text=f"شراء: {product_name}", font=("Arial", 14, "bold"),
             bg="#f4f7f6", fg="#2c3e50").pack(pady=20)

    # السعر
    tk.Label(buy_window, text=f"السعر: {product_price} SAR", font=("Arial", 12),
             bg="#f4f7f6", fg="#27ae60").pack(pady=5)

    # خانات الإدخال
    tk.Label(buy_window, text="الاسم الكامل:", bg="#f4f7f6").pack()
    name_entry = tk.Entry(buy_window, width=35, font=("Arial", 10))
    name_entry.pack(pady=5)

    tk.Label(buy_window, text="رقم الهاتف:", bg="#f4f7f6").pack()
    phone_entry = tk.Entry(buy_window, width=35, font=("Arial", 10))
    phone_entry.pack(pady=5)

    tk.Label(buy_window, text="عنوان التسليم:", bg="#f4f7f6").pack()
    address_entry = tk.Entry(buy_window, width=35, font=("Arial", 10))
    address_entry.pack(pady=5)

    tk.Label(buy_window, text="رقم الترخيص (اختياري):", bg="#f4f7f6", fg="#7f8c8d").pack(pady=(10, 0))
    license_entry = tk.Entry(buy_window, width=35, font=("Arial", 10), fg="blue")
    license_entry.pack(pady=5)

    def confirm_purchase():
        """تأكيد عملية الشراء"""
        name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        address = address_entry.get().strip()
        license_no = license_entry.get().strip()

        if not name or not phone or not address:
            messagebox.showwarning("تنبيه", "⚠️ يرجى إكمال جميع الحقول الأساسية")
            return

        # تجهيز بيانات الطلب
        order_info = {
            "product_name": product_name,
            "product_price": product_price,
            "product_id": product_id,
            "buyer_name": name,
            "buyer_phone": phone,
            "buyer_address": address,
            "license": license_no if license_no else "غير مرخص",
            "status": "جديد",
            "timestamp": {".sv": "timestamp"},
            "readable_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # إرسال الطلب
        if send_to_store(order_info):
            messagebox.showinfo("نجاح", f"✅ تم تسجيل طلب {product_name} بنجاح")
            buy_window.destroy()
        else:
            messagebox.showerror("خطأ", "❌ فشل الاتصال بقاعدة البيانات")

    # أزرار التحكم
    tk.Button(buy_window, text="تأكيد وإرسال", command=confirm_purchase,
              bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
              width=25, bd=0, cursor="hand2").pack(pady=20)

    tk.Button(buy_window, text="إلغاء", command=buy_window.destroy,
              bg="#95a5a6", fg="white", width=15, bd=0).pack()

    # زر اختبار الاتصال
    tk.Button(buy_window, text="🔍 اختبار الاتصال", command=lambda: test_firebase_connection(),
              bg="#3498db", fg="white", width=15, bd=0).pack(pady=10)

    # شريط المراقبة
    monitor_label = tk.Label(buy_window, text="الابن التاسع: يراقب توافق المدخلات",
                             font=("Arial", 8), bg="#f4f7f6", fg="#bdc3c7")
    monitor_label.pack(side="bottom", pady=5)


# للاختبار المباشر
if __name__ == "__main__":
    test_firebase_connection()
    open_buy_window("لابتوب احترافي", 5000, "123")
    tk.mainloop()