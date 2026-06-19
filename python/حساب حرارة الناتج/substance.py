"""
substance.py
============
كلاس المادة - يمثل مادة واحدة بخصائصها الحرارية والفيزيائية
"""

from enum import Enum


class PhysicalState(Enum):
    """الحالات الفيزيائية للمادة"""
    SOLID = "صلب ❄️"
    LIQUID = "سائل 💧"
    GAS = "غاز 💨"
    MELTING = "ينصهر (تحول طوري) 🔥"
    VAPORIZING = "يتبخر (تحول طوري) ♨️"
    FREEZING = "يتجمد (تحول طوري) 🧊"
    CONDENSING = "يتكثف (تحول طوري) 🌫️"


class Substance:
    """
    يمثل مادة فيزيائية بخصائصها الحرارية.
    
    الخصائص:
        name        : اسم المادة
        mass        : الكتلة بالكيلوغرام (kg)
        specific_heat: الحرارة النوعية J/(kg·°C)
        initial_temp : درجة الحرارة الابتدائية (°C)
        melting_point: درجة الانصهار (°C)
        boiling_point: درجة الغليان (°C)
        latent_fusion: الحرارة الكامنة للانصهار J/kg
        latent_vapor : الحرارة الكامنة للتبخر J/kg
        initial_state: الحالة الفيزيائية الابتدائية
    """

    def __init__(
        self,
        name: str,
        mass: float,
        specific_heat: float,
        initial_temp: float,
        melting_point: float,
        boiling_point: float,
        latent_fusion: float,
        latent_vapor: float,
        initial_state: PhysicalState = None,
    ):
        self.name = name
        self.mass = mass
        self.specific_heat = specific_heat
        self.initial_temp = initial_temp
        self.melting_point = melting_point
        self.boiling_point = boiling_point
        self.latent_fusion = latent_fusion
        self.latent_vapor = latent_vapor

        # تحديد الحالة الابتدائية تلقائياً إن لم تُعطَ
        if initial_state is not None:
            self.initial_state = initial_state
        else:
            self.initial_state = self._determine_state(initial_temp)

        # الحالة النهائية (تُحسب لاحقاً)
        self.final_state: PhysicalState = None
        self.final_temp: float = None

    # ------------------------------------------------------------------
    # حساب الحالة الفيزيائية بناءً على درجة الحرارة
    # ------------------------------------------------------------------
    def _determine_state(self, temp: float) -> PhysicalState:
        """يحدد الحالة الفيزيائية بناءً على درجة الحرارة (حالات مستقرة فقط)"""
        TOL = 1e-6
        if temp < self.melting_point - TOL:
            return PhysicalState.SOLID
        elif temp < self.boiling_point - TOL:
            return PhysicalState.LIQUID
        else:
            return PhysicalState.GAS

    # ------------------------------------------------------------------
    # الطاقة الحرارية المحمولة بالمادة (نسبي)
    # ------------------------------------------------------------------
    def thermal_capacity(self) -> float:
        """يحسب mc (الطاقة الحرارية النوعية × الكتلة)"""
        return self.mass * self.specific_heat

    def heat_content(self) -> float:
        """يحسب mcT (محتوى الطاقة الحرارية النسبي)"""
        return self.mass * self.specific_heat * self.initial_temp

    # ------------------------------------------------------------------
    # الحرارة الكامنة
    # ------------------------------------------------------------------
    def latent_heat_fusion_total(self) -> float:
        """إجمالي الحرارة الكامنة للانصهار/التجمد"""
        return self.mass * self.latent_fusion

    def latent_heat_vapor_total(self) -> float:
        """إجمالي الحرارة الكامنة للتبخر/التكثف"""
        return self.mass * self.latent_vapor

    # ------------------------------------------------------------------
    # عرض المعلومات
    # ------------------------------------------------------------------
    def display_info(self, show_final: bool = False):
        """يعرض معلومات المادة بشكل منسق"""
        sep = "═" * 55
        print(f"\n{sep}")
        print(f"  📦 المادة: {self.name}")
        print(f"{sep}")
        print(f"  ⚖️  الكتلة              : {self.mass} kg")
        print(f"  🌡️  درجة الحرارة الابتدائية : {self.initial_temp} °C")
        print(f"  🔥 الحرارة النوعية (c)   : {self.specific_heat} J/(kg·°C)")
        print(f"  🧊 نقطة الانصهار         : {self.melting_point} °C")
        print(f"  💨 نقطة الغليان          : {self.boiling_point} °C")
        print(f"  ❄️  حرارة كامنة للانصهار : {self.latent_fusion:,.0f} J/kg")
        print(f"  ♨️  حرارة كامنة للتبخر   : {self.latent_vapor:,.0f} J/kg")
        print(f"  🔬 الحالة الابتدائية      : {self.initial_state.value}")

        if show_final and self.final_state is not None:
            print(f"  ✅ الحالة النهائية       : {self.final_state.value}")
            print(f"  🌡️  درجة الحرارة النهائية : {self.final_temp:.4f} °C")
        print(sep)

    def display_summary_row(self):
        """يعرض سطراً ملخصاً للمادة"""
        state_str = self.final_state.value if self.final_state else self.initial_state.value
        temp_str = f"{self.final_temp:.2f} °C" if self.final_temp is not None else f"{self.initial_temp:.2f} °C"
        print(f"  • {self.name:<20} | {self.mass} kg | {temp_str:<15} | {state_str}")
