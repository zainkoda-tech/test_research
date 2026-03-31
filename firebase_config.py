import firebase_admin
from firebase_admin import credentials, db

def initialize_zain_system():
    # منع تكرار التهيئة (سلطة الابن التاسع في منع العطب)
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://g10-sovereign-default-rtdb.europe-west1.firebasedatabase.app/' # تحديث الرابط ليتوافق مع مشروعك
            })
            print("الابن التاسع: تم تأمين الاتصال بنجاح.")
        except Exception as e:
            print(f"عطب في التهيئة: {e}")
            return None
    return db.reference('/')

# وظيفة الحفيد التاسع (تأمين إرسال البيانات)
def send_to_store(data):
    root = initialize_zain_system()
    if root:
        # أرشفة البيانات في قسم 'orders' بالمتجر
        new_order = root.child('orders').push(data)
        print(f"الابن التاسع: تم أرشفة الطلب برقم: {new_order.key}")
        return True
    return False