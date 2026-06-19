"""
main.py
=======
نقطة الدخول الرئيسية لمشروع حساب الحرارة والحالات الفيزيائية
يستخدم OOP ويدعم المواد المحفوظة وإدخال المستخدم
"""

import os
import sys
from substance import Substance, PhysicalState
from substances_db import SubstanceDatabase
from mixer import ThermalMixer


# =============================================================================
# ألوان الطرفية (ANSI)
# =============================================================================
class Color:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    WHITE  = "\033[97m"
    DIM    = "\033[2m"


def c(text: str, color: str) -> str:
    """يُلوّن النص بلون معين"""
    return f"{color}{text}{Color.RESET}"


# =============================================================================
# دوال المساعدة للإدخال
# =============================================================================
def get_float(prompt: str, min_val: float = None, max_val: float = None) -> float:
    """يطلب من المستخدم رقماً عشرياً مع التحقق"""
    while True:
        try:
            raw = input(f"  {prompt}").strip()
            val = float(raw)
            if min_val is not None and val < min_val:
                print(c(f"  ❌ القيمة يجب أن تكون >= {min_val}", Color.RED))
                continue
            if max_val is not None and val > max_val:
                print(c(f"  ❌ القيمة يجب أن تكون <= {max_val}", Color.RED))
                continue
            return val
        except ValueError:
            print(c("  ❌ أدخل رقماً صحيحاً أو عشرياً من فضلك.", Color.RED))


def get_int(prompt: str, min_val: int = 1, max_val: int = None) -> int:
    """يطلب من المستخدم رقماً صحيحاً مع التحقق"""
    while True:
        try:
            raw = input(f"  {prompt}").strip()
            val = int(raw)
            if min_val is not None and val < min_val:
                print(c(f"  ❌ القيمة يجب أن تكون >= {min_val}", Color.RED))
                continue
            if max_val is not None and val > max_val:
                print(c(f"  ❌ القيمة يجب أن تكون <= {max_val}", Color.RED))
                continue
            return val
        except ValueError:
            print(c("  ❌ أدخل رقماً صحيحاً من فضلك.", Color.RED))


def get_choice(prompt: str, choices: list) -> str:
    """يطلب من المستخدم اختيار من قائمة"""
    while True:
        raw = input(f"  {prompt}").strip().lower()
        if raw in [ch.lower() for ch in choices]:
            return raw
        print(c(f"  ❌ اختر من: {', '.join(choices)}", Color.RED))


def press_enter():
    """ينتظر المستخدم يضغط Enter"""
    input(c("\n  ↩️  اضغط Enter للمتابعة...", Color.DIM))


# =============================================================================
# رأس الصفحة
# =============================================================================
def print_header():
    """يطبع رأس البرنامج"""
    os.system("clear" if os.name != "nt" else "cls")
    print(c("""
  ╔══════════════════════════════════════════════════════════════╗
  ║                                                              ║
  ║       🔬  حاسبة الحرارة والحالات الفيزيائية              ║
  ║                                                              ║
  ║   يحسب درجة الحرارة النهائية والحالة الفيزيائية لكل مادة  ║
  ║           عند الخلط مع مراعاة التحولات الطورية              ║
  ║                                                              ║
  ╚══════════════════════════════════════════════════════════════╝
    """, Color.CYAN))


def print_section(title: str):
    """يطبع عنوان قسم"""
    print(c(f"\n  {'─'*55}", Color.BLUE))
    print(c(f"  📌 {title}", Color.BOLD + Color.YELLOW))
    print(c(f"  {'─'*55}", Color.BLUE))


# =============================================================================
# إدخال بيانات مادة
# =============================================================================
def input_substance_from_scratch(db: SubstanceDatabase, index: int) -> Substance:
    """يطلب جميع بيانات مادة جديدة من المستخدم يدوياً"""
    print_section(f"إدخال بيانات المادة رقم {index} - يدوي")

    name = input("  📝 اسم المادة: ").strip()
    mass = get_float("⚖️  الكتلة (kg): ", min_val=0.0001)
    specific_heat = get_float("🔥 الحرارة النوعية c بـ J/(kg·°C): ", min_val=0.001)
    initial_temp = get_float("🌡️  درجة الحرارة الابتدائية (°C): ")
    melting_point = get_float("🧊 درجة الانصهار/التجمد (°C): ")
    boiling_point = get_float("💨 درجة الغليان/التكثف (°C): ")

    if boiling_point <= melting_point:
        print(c("  ⚠️  تحذير: درجة الغليان يجب أن تكون أكبر من درجة الانصهار.", Color.YELLOW))

    latent_fusion = get_float("❄️  الحرارة الكامنة للانصهار L_f بـ J/kg: ", min_val=0)
    latent_vapor = get_float("♨️  الحرارة الكامنة للتبخر L_v بـ J/kg: ", min_val=0)

    substance = Substance(
        name=name,
        mass=mass,
        specific_heat=specific_heat,
        initial_temp=initial_temp,
        melting_point=melting_point,
        boiling_point=boiling_point,
        latent_fusion=latent_fusion,
        latent_vapor=latent_vapor,
    )

    # سؤال: هل تريد حفظها في قاعدة البيانات؟
    print(c("\n  💾 هل تريد حفظ هذه المادة في قاعدة البيانات؟", Color.CYAN))
    save = get_choice("  (n=لا، y=نعم): ", ["y", "n"])
    if save == "y":
        permanent = db.verify_password()
        key = name.lower().replace(" ", "_")
        data = SubstanceDatabase.build_material_data(
            name_ar=name,
            name_en=name,
            specific_heat=specific_heat,
            melting_point=melting_point,
            boiling_point=boiling_point,
            latent_heat_fusion=latent_fusion,
            latent_heat_vaporization=latent_vapor,
        )
        db.add_material(key, data, permanent=permanent)

    return substance


def input_substance_from_db(db: SubstanceDatabase, index: int) -> Substance:
    """يطلب من المستخدم اختيار مادة من قاعدة البيانات"""
    print_section(f"اختيار المادة رقم {index} من قاعدة البيانات")
    db.display_all()

    print(c("\n  🔍 أدخل اسم المادة (عربي / إنجليزي / المفتاح):", Color.CYAN))
    while True:
        query = input("  > ").strip()
        result = db.search_material(query)
        if result:
            key, data = result
            break
        print(c(f"  ❌ لم يتم إيجاد '{query}'. حاول مرة أخرى أو اكتب 'رجوع'.", Color.RED))
        if query.lower() in ("رجوع", "back", "exit"):
            return None

    db.display_material_details(key)

    # تعديل البيانات إذا أراد المستخدم
    substance_data = dict(data)
    substance_data = _offer_modification(db, key, substance_data)

    # طلب الكتلة (دائماً يدوية)
    print(c(f"\n  ⚖️  أدخل الكتلة المستخدمة لـ '{substance_data.get('name_ar', key)}' بالكيلوغرام:", Color.CYAN))
    mass = get_float("  الكتلة (kg): ", min_val=0.0001)

    # الحرارة الابتدائية
    print(c("  🌡️  أدخل درجة الحرارة الابتدائية (°C):", Color.CYAN))
    initial_temp = get_float("  T_i (°C): ")

    return Substance(
        name=substance_data.get("name_ar", key),
        mass=mass,
        specific_heat=substance_data.get("specific_heat"),
        initial_temp=initial_temp,
        melting_point=substance_data.get("melting_point"),
        boiling_point=substance_data.get("boiling_point"),
        latent_fusion=substance_data.get("latent_heat_fusion"),
        latent_vapor=substance_data.get("latent_heat_vaporization"),
    )


def _offer_modification(db: SubstanceDatabase, key: str, data: dict) -> dict:
    """
    يعرض خيار تعديل بيانات المادة.
    يدعم التعديل المؤقت أو الدائم بكلمة السر.
    """
    print(c("\n  ✏️  هل تريد تعديل أي من البيانات؟ (y=نعم، n=لا):", Color.CYAN))
    choice = get_choice("  > ", ["y", "n"])
    if choice == "n":
        return data

    # حقول قابلة للتعديل
    fields = {
        "1": ("specific_heat",            "الحرارة النوعية c"),
        "2": ("melting_point",            "درجة الانصهار"),
        "3": ("boiling_point",            "درجة الغليان"),
        "4": ("latent_heat_fusion",       "الحرارة الكامنة للانصهار"),
        "5": ("latent_heat_vaporization", "الحرارة الكامنة للتبخر"),
    }

    while True:
        print(c("\n  📋 اختر الحقل للتعديل:", Color.YELLOW))
        for num, (field_key, field_name) in fields.items():
            current = data.get(field_key, "—")
            print(f"    {num}. {field_name} (الحالي: {current})")
        print("    0. انتهاء التعديل")

        choice_num = input("  > ").strip()
        if choice_num == "0":
            break

        if choice_num not in fields:
            print(c("  ❌ اختيار غير صالح.", Color.RED))
            continue

        field_key, field_name = fields[choice_num]
        new_val = get_float(f"  أدخل القيمة الجديدة لـ '{field_name}': ")

        # هل تعديل دائم أم مؤقت؟
        print(c(f"\n  🔐 للتعديل الدائم أدخل كلمة السر، للمؤقت اضغط Enter مباشرة:", Color.CYAN))
        pwd_input = input("  > ").strip()
        permanent = (pwd_input == "1")

        # تحديث القاموس المحلي
        data[field_key] = new_val
        # تحديث قاعدة البيانات
        db.modify_material(key, field_key, new_val, permanent=permanent)

        if not permanent and pwd_input != "":
            print(c("  ℹ️  كلمة السر غير صحيحة - التعديل مؤقت لهذه الجلسة.", Color.YELLOW))

    return data


# =============================================================================
# جمع بيانات المواد
# =============================================================================
def collect_substances(db: SubstanceDatabase) -> list:
    """يجمع بيانات جميع المواد من المستخدم"""
    print_section("عدد المواد")
    n = get_int("🔢 كم عدد المواد التي تريد خلطها؟ (1 على الأقل): ", min_val=1)

    substances = []
    for i in range(1, n + 1):
        print(c(f"\n  ╔══ المادة {i} من {n} ══╗", Color.MAGENTA))
        print(c("  كيف تريد إدخال بيانات هذه المادة؟", Color.WHITE))
        print("    1. اختيار من قاعدة البيانات")
        print("    2. إدخال يدوي")

        source = get_choice("  اختيارك (1/2): ", ["1", "2"])

        if source == "1":
            substance = input_substance_from_db(db, i)
            if substance is None:
                print(c("  ↩️  تم الرجوع. الانتقال للإدخال اليدوي...", Color.YELLOW))
                substance = input_substance_from_scratch(db, i)
        else:
            substance = input_substance_from_scratch(db, i)

        # عرض بيانات المادة للمراجعة
        substance.display_info()
        print(c("\n  ✅ هل البيانات صحيحة؟ (y=نعم، n=أعد الإدخال):", Color.GREEN))
        confirm = get_choice("  > ", ["y", "n"])
        if confirm == "n":
            print(c("  🔄 إعادة إدخال المادة...", Color.YELLOW))
            i -= 1  # إعادة نفس الرقم
            continue

        substances.append(substance)
        print(c(f"  ✅ تمت إضافة '{substance.name}' بنجاح!", Color.GREEN))

    return substances


# =============================================================================
# الدالة الرئيسية
# =============================================================================
def main():
    print_header()

    # تحميل قاعدة البيانات
    db = SubstanceDatabase()
    print(c(f"  ✅ تم تحميل قاعدة البيانات ({len(db.get_all_materials())} مادة).", Color.GREEN))
    press_enter()

    # ─── حلقة التشغيل الرئيسية ───────────────────────────────────────────
    while True:
        print_header()
        print(c("  📋 القائمة الرئيسية:", Color.CYAN))
        print("    1. بدء حساب جديد")
        print("    2. عرض قاعدة البيانات")
        print("    3. خروج")

        choice = get_choice("\n  اختيارك (1/2/3): ", ["1", "2", "3"])

        if choice == "3":
            print(c("\n  👋 مع السلامة!\n", Color.CYAN))
            sys.exit(0)

        if choice == "2":
            db.display_all()
            press_enter()
            continue

        # ─── حساب جديد ────────────────────────────────────────────────────
        print_header()

        # 1) جمع بيانات المواد
        substances = collect_substances(db)

        if not substances:
            print(c("  ⚠️  لم يتم إدخال أي مواد!", Color.RED))
            press_enter()
            continue

        # 2) إنشاء كائن الخلط
        mixer = ThermalMixer(substances)

        # ─── الخطوة 1: T_mix الأولية ──────────────────────────────────────
        print_section("الخطوة 1: حساب درجة الحرارة الأولية عند الخلط")
        t_initial = mixer.calculate_initial_mix_temp()
        mixer.display_initial_result()
        press_enter()

        # ─── الخطوة 2: التحولات الطورية والحالة النهائية ──────────────────
        print_section("الخطوة 2: تحديد التحولات الطورية والحالة النهائية")
        t_final = mixer.calculate_final_state()
        mixer.display_phase_log()
        mixer.display_final_result()

        # ─── عرض تفاصيل كل مادة ──────────────────────────────────────────
        print_section("تفاصيل كل مادة بعد الخلط")
        for substance in substances:
            substance.display_info(show_final=True)

        # ─── ملخص مقارن ───────────────────────────────────────────────────
        sep = "═" * 60
        print(f"\n{c(sep, Color.CYAN)}")
        print(c("  📊 ملخص النتائج:", Color.BOLD + Color.CYAN))
        print(c(sep, Color.CYAN))
        print(c(f"  🌡️  T_mix الأولية (بدون تفاعلات) : {t_initial:.4f} °C", Color.YELLOW))
        print(c(f"  🎯 T_final الحقيقية              : {t_final:.4f} °C", Color.GREEN))
        delta = t_final - t_initial
        delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"
        print(c(f"  📈 الفرق (تأثير التحولات الطورية): {delta_str} °C", Color.MAGENTA))
        print(c(sep, Color.CYAN))

        press_enter()

        # سؤال: هل تريد حساباً جديداً؟
        print(c("\n  🔄 هل تريد إجراء حساب جديد؟ (y=نعم، n=لا):", Color.CYAN))
        again = get_choice("  > ", ["y", "n"])
        if again == "n":
            print(c("\n  👋 مع السلامة!\n", Color.CYAN))
            break


# =============================================================================
# نقطة الدخول
# =============================================================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(c("\n\n  ⚠️  تم إيقاف البرنامج بواسطة المستخدم.\n", Color.YELLOW))
        sys.exit(0)
