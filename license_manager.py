import json
import os
import uuid
import base64
from datetime import datetime, timedelta

class LicenseManager:
    def __init__(self, file_path="config.json"):
        self.file_path = file_path
        self.gold_serial = "ZAIN-PRO-2026"
        self.support_stamp = "✅ Certified Support 2026"
        self.data = self._load_config()
        self.start_time = datetime.now()

    def _get_device_id(self):
        return str(uuid.getnode())

    def _encode(self, text):
        return base64.b64encode(text.encode()).decode()

    def _decode(self, text):
        try:
            return base64.b64decode(text.encode()).decode()
        except Exception:
            return text

    def _load_config(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                raw = json.load(f)
                return {
                    "owner": self._decode(raw.get("owner", "Guest")),
                    "serial": self._decode(raw.get("serial", "")),
                    "activated": raw.get("activated", False),
                    "device_id": raw.get("device_id", ""),
                    "last_reminder": raw.get("last_reminder", "")
                }
        return {"owner": "Guest", "serial": "", "activated": False, "device_id": "", "last_reminder": ""}

    def _save_config(self):
        raw = {
            "owner": self._encode(self.data["owner"]),
            "serial": self._encode(self.data["serial"]),
            "activated": self.data["activated"],
            "device_id": self.data["device_id"],
            "last_reminder": self.data.get("last_reminder", "")
        }
        with open(self.file_path, 'w') as f:
            json.dump(raw, f)

    def activate(self, name, serial):
        if serial == self.gold_serial:
            self.data = {
                "owner": name,
                "serial": serial,
                "activated": True,
                "device_id": self._get_device_id(),
                "last_reminder": str(datetime.now())
            }
            self._save_config()
            return True
        return False

    def is_fully_active(self):
        return (
            self.data.get("activated") and
            self.data.get("serial") == self.gold_serial and
            self.data.get("device_id") == self._get_device_id()
        )

    def check_reminder(self):
        if not self.is_fully_active():
            now = datetime.now()
            last_reminder = self.data.get("last_reminder")
            if not last_reminder or (now - datetime.fromisoformat(last_reminder)) >= timedelta(minutes=30):
                self.data["last_reminder"] = str(now)
                self._save_config()
                return "🔔 نظام زين: يرجى تفعيل النسخة للحصول على كامل الصلاحيات."
        return None

    def get_status_text(self):
        if self.is_fully_active():
            return f"👤 المالك: {self.data['owner']} | {self.support_stamp}"
        return "⚠️ نسخة تجريبية (غير مسجلة)"
