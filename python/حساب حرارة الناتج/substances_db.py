"""
substances_db.py
================
إدارة قاعدة بيانات المواد المحفوظة في ملف materials.json
يدعم التعديل المؤقت (للجلسة) والتعديل الدائم (بكلمة سر: 1)
"""

import json
import os
import copy
from typing import Optional, Dict, Any

# المسار الافتراضي لملف قاعدة البيانات
DB_PATH = os.path.join(os.path.dirname(__file__), "materials.json")

# كلمة السر للتعديل الدائم
ADMIN_PASSWORD = "1"


class SubstanceDatabase:
    """
    يُدير قاعدة بيانات المواد المحفوظة.
    
    - يقرأ البيانات من materials.json
    - يسمح بالبحث والعرض
    - يدعم التعديل المؤقت (للجلسة الحالية فقط)
    - يدعم التعديل الدائم (بكلمة السر '1')
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._persistent_data: Dict[str, Any] = {}   # بيانات الملف الأصلية
        self._session_data: Dict[str, Any] = {}       # بيانات الجلسة (مع التعديلات المؤقتة)
        self._load()

    # ------------------------------------------------------------------
    # تحميل البيانات
    # ------------------------------------------------------------------
    def _load(self):
        """يحمّل البيانات من الملف"""
        if not os.path.exists(self.db_path):
            print(f"⚠️  ملف قاعدة البيانات غير موجود: {self.db_path}")
            self._persistent_data = {"materials": {}}
        else:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self._persistent_data = json.load(f)

        # نسخ للجلسة الحالية
        self._session_data = copy.deepcopy(self._persistent_data)

    # ------------------------------------------------------------------
    # الحصول على بيانات المواد
    # ------------------------------------------------------------------
    def get_all_materials(self) -> Dict[str, Any]:
        """يُرجع جميع المواد من بيانات الجلسة"""
        return self._session_data.get("materials", {})

    def get_material(self, key: str) -> Optional[Dict[str, Any]]:
        """يُرجع بيانات مادة معينة بمفتاحها"""
        return self._session_data.get("materials", {}).get(key.lower())

    def search_material(self, query: str) -> Optional[tuple]:
        """
        يبحث عن مادة بالاسم (عربي أو إنجليزي أو المفتاح).
        يُرجع (key, data) أو None إن لم يُوجد
        """
        query_lower = query.strip().lower()
        materials = self.get_all_materials()
        for key, data in materials.items():
            if (
                query_lower == key
                or query_lower == data.get("name_en", "").lower()
                or query_lower == data.get("name_ar", "").lower()
            ):
                return key, data
        return None

    # ------------------------------------------------------------------
    # عرض المواد
    # ------------------------------------------------------------------
    def display_all(self):
        """يعرض جميع المواد المتاحة في قاعدة البيانات"""
        materials = self.get_all_materials()
        if not materials:
            print("  ⚠️  قاعدة البيانات فارغة!")
            return

        print("\n  ╔══════════════════════════════════════════════════════╗")
        print("  ║          📚 المواد المتاحة في قاعدة البيانات        ║")
        print("  ╠═══╦══════════════════╦══════════╦══════════╦═════════╣")
        print("  ║ # ║ الاسم            ║  c       ║  T_غليان ║ T_انصهار║")
        print("  ╠═══╬══════════════════╬══════════╬══════════╬═════════╣")
        for i, (key, data) in enumerate(materials.items(), 1):
            name = data.get("name_ar", key)
            c = data.get("specific_heat", "-")
            bp = data.get("boiling_point", "-")
            mp = data.get("melting_point", "-")
            print(f"  ║{i:^3}║ {name:<18}║{c:^10}║{bp:^10}║{mp:^9}║")
        print("  ╚═══╩══════════════════╩══════════╩══════════╩═════════╝")

    def display_material_details(self, key: str):
        """يعرض تفاصيل مادة معينة"""
        data = self.get_material(key)
        if not data:
            print(f"  ⚠️  المادة '{key}' غير موجودة في قاعدة البيانات.")
            return

        print(f"\n  ┌─────────────────────────────────────────────────┐")
        print(f"  │  📋 تفاصيل: {data.get('name_ar', key)} ({data.get('name_en', key)})")
        print(f"  ├─────────────────────────────────────────────────┤")
        print(f"  │  🔥 الحرارة النوعية (c)       : {data.get('specific_heat')} J/(kg·°C)")
        print(f"  │  🧊 نقطة الانصهار             : {data.get('melting_point')} °C")
        print(f"  │  💨 نقطة الغليان              : {data.get('boiling_point')} °C")
        print(f"  │  ❄️  حرارة كامنة للانصهار    : {data.get('latent_heat_fusion'):,} J/kg")
        print(f"  │  ♨️  حرارة كامنة للتبخر      : {data.get('latent_heat_vaporization'):,} J/kg")
        print(f"  └─────────────────────────────────────────────────┘")

    # ------------------------------------------------------------------
    # التعديل
    # ------------------------------------------------------------------
    def modify_material(self, key: str, field: str, new_value: float, permanent: bool = False):
        """
        يعدّل حقلاً في بيانات مادة معينة.
        
        permanent=False → تعديل مؤقت (الجلسة فقط)
        permanent=True  → تعديل دائم (يُحفظ في الملف)
        """
        materials = self._session_data.get("materials", {})
        if key not in materials:
            print(f"  ⚠️  المادة '{key}' غير موجودة.")
            return False

        materials[key][field] = new_value
        print(f"  ✅ تم تعديل '{field}' للمادة '{materials[key].get('name_ar', key)}'"
              f" إلى {new_value} {'(مؤقت)' if not permanent else '(دائم)'}")

        if permanent:
            self._persistent_data["materials"][key][field] = new_value
            self._save()
        return True

    def add_material(self, key: str, data: Dict[str, Any], permanent: bool = False):
        """يضيف مادة جديدة لقاعدة البيانات"""
        self._session_data["materials"][key] = data
        if permanent:
            self._persistent_data["materials"][key] = data
            self._save()
        action = "دائم ✅" if permanent else "مؤقت (هذه الجلسة فقط) ⏳"
        print(f"  ✅ تمت إضافة '{data.get('name_ar', key)}' بشكل {action}.")

    def _save(self):
        """يحفظ البيانات الدائمة في الملف"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self._persistent_data, f, ensure_ascii=False, indent=2)
        print(f"  💾 تم حفظ التغييرات في: {self.db_path}")

    # ------------------------------------------------------------------
    # التحقق من كلمة السر
    # ------------------------------------------------------------------
    @staticmethod
    def verify_password() -> bool:
        """يطلب كلمة السر للتعديل الدائم"""
        print("\n  🔐 أدخل كلمة السر للتعديل الدائم (أو اضغط Enter للتخطي): ", end="")
        pwd = input().strip()
        if pwd == ADMIN_PASSWORD:
            print("  ✅ كلمة السر صحيحة - سيتم حفظ التغييرات بشكل دائم.")
            return True
        else:
            print("  ℹ️  كلمة السر غير صحيحة - التعديل مؤقت لهذه الجلسة فقط.")
            return False

    # ------------------------------------------------------------------
    # إنشاء قاموس بيانات المادة
    # ------------------------------------------------------------------
    @staticmethod
    def build_material_data(
        name_ar: str,
        name_en: str,
        specific_heat: float,
        melting_point: float,
        boiling_point: float,
        latent_heat_fusion: float,
        latent_heat_vaporization: float,
    ) -> Dict[str, Any]:
        """يبني قاموس بيانات مادة جديدة"""
        return {
            "name_ar": name_ar,
            "name_en": name_en,
            "specific_heat": specific_heat,
            "melting_point": melting_point,
            "boiling_point": boiling_point,
            "latent_heat_fusion": latent_heat_fusion,
            "latent_heat_vaporization": latent_heat_vaporization,
        }
