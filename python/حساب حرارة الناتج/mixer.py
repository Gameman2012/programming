"""
mixer.py
========
كلاس الخلط الحراري - يحسب درجة الحرارة النهائية والحالات الفيزيائية
عند خلط مجموعة من المواد مع مراعاة التحولات الطورية.

الخوارزمية: نهج الإنثالبي بالمقاطع (Piecewise Enthalpy Method)
════════════════════════════════════════════════════════════════════
H_system(T) دالة تصاعدية لكنها غير مستمرة - تقفز عند نقاط التحول
(بسبب الحرارة الكامنة). نعامل كل مقطع بشكل منفصل.

المقاطع:
  (..., T_event_1)  → خطي
  [T_event_1] = نقطة تحول (الحرارة الكامنة)
  (T_event_1, T_event_2) → خطي
  ...

للبحث عن T_final:
  لكل مقطع خطي: نتحقق هل H_total ∈ [H_lo, H_hi]
  لكل نقطة تحول: نتحقق هل H_total ∈ [H_before, H_after]
"""

from substance import Substance, PhysicalState
from typing import List, Tuple


class ThermalMixer:
    """يحسب نتيجة خلط عدة مواد حرارياً مع التحولات الطورية."""

    def __init__(self, substances: List[Substance]):
        if not substances:
            raise ValueError("يجب توفير مادة واحدة على الأقل!")
        self.substances = substances
        self._initial_mix_temp: float = None
        self._final_mix_temp: float = None
        self._phase_log: List[str] = []

    # ══════════════════════════════════════════════════════════════════
    # الخطوة 1: T_mix الأولية (بدون تحولات طورية)
    # ══════════════════════════════════════════════════════════════════
    def calculate_initial_mix_temp(self) -> float:
        """T_mix = Σ(m·c·T) / Σ(m·c) — بدون تحولات طورية"""
        num = sum(s.heat_content() for s in self.substances)
        den = sum(s.thermal_capacity() for s in self.substances)
        if den == 0:
            raise ValueError("مجموع (mc) = 0!")
        self._initial_mix_temp = num / den
        return self._initial_mix_temp

    # ══════════════════════════════════════════════════════════════════
    # دالة الإنثالبي التراكمي H(T) - مرجع: T=0 في الحالة الصلبة
    # ══════════════════════════════════════════════════════════════════
    def _H(self, s: Substance, T: float) -> float:
        """
        الإنثالبي لمادة واحدة عند T (مرجع 0°C صلب).
        دالة مستمرة تصاعدية، تقفز بمقدار L_f عند T_melt وL_v عند T_boil.
        """
        mp = s.melting_point
        bp = s.boiling_point
        mc = s.thermal_capacity()

        if T <= mp:
            return mc * T
        elif T <= bp:
            # فوق نقطة الانصهار: صلب→سائل قد حدث
            return mc * mp + s.latent_heat_fusion_total() + mc * (T - mp)
        else:
            # فوق نقطة الغليان
            return (mc * mp
                    + s.latent_heat_fusion_total()
                    + mc * (bp - mp)
                    + s.latent_heat_vapor_total()
                    + mc * (T - bp))

    def _H_system(self, T: float) -> float:
        """H الكلي للنظام عند T (مجموع H لكل مادة)"""
        return sum(self._H(s, T) for s in self.substances)

    # ══════════════════════════════════════════════════════════════════
    # الخطوة 2: إيجاد T_final
    # ══════════════════════════════════════════════════════════════════
    def calculate_final_state(self) -> float:
        """
        يجد T_final حيث H_system(T_final) = H_total_initial.

        الخوارزمية بالمقاطع:
        ─────────────────────────────────────────────────────────────
        - نبني قائمة "أحداث" مرتبة بـ T، كل حدث إما:
            * مقطع خطي: (T_lo, T_hi) → خطي بميل Σmc
            * نقطة تحول: T_event, H_before=H(T_event-ε), H_after=H(T_event+ε)

        - نمسح من الأقل للأعلى حتى نجد الفترة التي يقع فيها H_total
        - نحسب T_final بالاستيفاء الخطي داخل الفترة
        ─────────────────────────────────────────────────────────────
        """
        if self._initial_mix_temp is None:
            self.calculate_initial_mix_temp()

        self._phase_log = []

        # ── الإنثالبي الكلي الابتدائي ─────────────────────────────────────
        H_total = sum(self._H(s, s.initial_temp) for s in self.substances)

        # ── جمع نقاط التحول (T_melt, T_boil لكل مادة) ───────────────────
        transition_temps = set()
        for s in self.substances:
            transition_temps.add(s.melting_point)
            transition_temps.add(s.boiling_point)
        transition_temps = sorted(transition_temps)

        # ── بناء قائمة المقاطع للمسح ──────────────────────────────────────
        # كل نقطة تحول تنشئ "فجوة" في الإنثالبي (قفز بالحرارة الكامنة)
        # نمثّل ذلك بثلاثة نقاط: T-ε, T, T+ε
        EPS = 1e-9

        # نقاط المسح (درجات حرارة)
        scan_points = [-1000.0]  # نقطة ابتداء بعيدة
        for T_ev in transition_temps:
            scan_points.append(T_ev - EPS)  # قبل التحول
            scan_points.append(T_ev)         # عند التحول (قبل الحرارة الكامنة)
            scan_points.append(T_ev + EPS)  # بعد التحول (بعد الحرارة الكامنة)
        scan_points.append(10000.0)  # نقطة نهاية بعيدة

        T_final = None

        for i in range(len(scan_points) - 1):
            T_lo = scan_points[i]
            T_hi = scan_points[i + 1]
            H_lo = self._H_system(T_lo)
            H_hi = self._H_system(T_hi)

            if H_total < H_lo:
                # T_final أقل من هذه الفترة
                # (لن يحدث إذا رتّبنا المسح بشكل صحيح، إلا في البداية)
                if T_lo == -1000.0:
                    # T_final أقل من -1000 → نحسبها
                    mc = sum(s.thermal_capacity() for s in self.substances)
                    T_final = T_lo + (H_total - H_lo) / mc if mc > 0 else T_lo
                    break
                continue

            if H_lo <= H_total <= H_hi:
                # T_final في هذه الفترة
                delta_H = H_hi - H_lo
                if delta_H < 1e-10:
                    # فترة الحرارة الكامنة (مرحلة التحول) → T_final = T_lo (أو T_hi، متساويان)
                    T_final = T_lo
                else:
                    # استيفاء خطي
                    T_final = T_lo + (T_hi - T_lo) * (H_total - H_lo) / delta_H
                break

        if T_final is None:
            # H_total أكبر من H_system عند أقصى نقطة → T_final عالٍ جداً
            H_max = self._H_system(scan_points[-1])
            mc = sum(s.thermal_capacity() for s in self.substances)
            T_final = scan_points[-1] + (H_total - H_max) / mc if mc > 0 else scan_points[-1]

        # تنظيف: إذا T_final أقرب لـ EPS من نقطة تحول → اجعلها نقطة التحول
        for T_ev in transition_temps:
            if abs(T_final - T_ev) < 1e-6:
                T_final = T_ev
                break

        # ── تحديد الحالة النهائية لكل مادة ──────────────────────────────
        final_states = {s.name: s._determine_state(T_final) for s in self.substances}

        # ── تسجيل التحولات الطورية ────────────────────────────────────────
        self._build_phase_log(T_final, final_states)

        # ── تعيين النتائج ─────────────────────────────────────────────────
        self._final_mix_temp = T_final
        for s in self.substances:
            s.final_state = final_states[s.name]
            s.final_temp  = T_final

        return T_final

    # ══════════════════════════════════════════════════════════════════
    # تسجيل التحولات الطورية
    # ══════════════════════════════════════════════════════════════════
    def _build_phase_log(self, T_final: float, final_states: dict):
        """يقارن الحالة الابتدائية بالنهائية ويبني سجل التحولات"""
        self._phase_log = []
        TOL = 0.02

        for s in self.substances:
            init  = s.initial_state
            final = final_states[s.name]
            T_mp  = s.melting_point
            T_bp  = s.boiling_point

            at_mp = abs(T_final - T_mp) < TOL
            at_bp = abs(T_final - T_bp) < TOL

            # ───── صلب → سائل (انصهار) ─────
            if init == PhysicalState.SOLID and final == PhysicalState.LIQUID:
                if at_mp:
                    self._phase_log.append(
                        f"  🔥 '{s.name}': ينصهر جزئياً عند {T_mp:.2f}°C"
                    )
                else:
                    self._phase_log.append(
                        f"  🔥 '{s.name}': انصهر تماماً عند {T_mp:.2f}°C"
                        f"  |  Q_f = {s.latent_heat_fusion_total():,.0f} J"
                    )

            # ───── سائل → صلب (تجمد) ─────
            if init == PhysicalState.LIQUID and final == PhysicalState.SOLID:
                if at_mp:
                    self._phase_log.append(
                        f"  🧊 '{s.name}': يتجمد جزئياً عند {T_mp:.2f}°C"
                    )
                else:
                    self._phase_log.append(
                        f"  🧊 '{s.name}': تجمّد تماماً عند {T_mp:.2f}°C"
                        f"  |  Q_f = {s.latent_heat_fusion_total():,.0f} J (محرَّرة)"
                    )

            # ───── سائل → غاز (تبخر) ─────
            if init == PhysicalState.LIQUID and final == PhysicalState.GAS:
                if at_bp:
                    self._phase_log.append(
                        f"  ♨️  '{s.name}': يتبخر جزئياً عند {T_bp:.2f}°C"
                    )
                else:
                    self._phase_log.append(
                        f"  💨 '{s.name}': تبخّر تماماً عند {T_bp:.2f}°C"
                        f"  |  Q_v = {s.latent_heat_vapor_total():,.0f} J"
                    )

            # ───── صلب → غاز (تسامي) ─────
            if init == PhysicalState.SOLID and final == PhysicalState.GAS:
                if at_bp:
                    self._phase_log.append(
                        f"  ♨️  '{s.name}': يتسامى جزئياً عند {T_bp:.2f}°C"
                    )
                else:
                    self._phase_log.append(
                        f"  💨 '{s.name}': تسامى تماماً عند {T_bp:.2f}°C"
                        f"  |  Q_v = {s.latent_heat_vapor_total():,.0f} J"
                    )

            # ───── غاز → سائل (تكثف) ─────
            if init == PhysicalState.GAS and final == PhysicalState.LIQUID:
                if at_bp:
                    self._phase_log.append(
                        f"  🌫️  '{s.name}': يتكثف جزئياً عند {T_bp:.2f}°C"
                    )
                else:
                    self._phase_log.append(
                        f"  🌫️  '{s.name}': تكثّف تماماً عند {T_bp:.2f}°C"
                        f"  |  Q_v = {s.latent_heat_vapor_total():,.0f} J (محرَّرة)"
                    )

            # ───── غاز → صلب (ترسب) ─────
            if init == PhysicalState.GAS and final == PhysicalState.SOLID:
                self._phase_log.append(
                    f"  ❄️  '{s.name}': ترسّب (غاز→صلب) عند {T_bp:.2f}°C"
                )

    # ══════════════════════════════════════════════════════════════════
    # عرض النتائج
    # ══════════════════════════════════════════════════════════════════
    def display_initial_result(self):
        sep = "═" * 72
        print(f"\n{sep}")
        print("  🌡️  نتيجة الخلط الأولية (بتجاهل التحولات الطورية)")
        print(sep)
        print(f"\n  📐 القانون: T_mix = Σ(m·c·T) / Σ(m·c)\n")
        print(f"  {'المادة':<22} | {'m (kg)':<10} | {'c (J/kg°C)':<12} | {'T_i (°C)':<12} | {'m·c·T (J)'}")
        print(f"  {'-'*22}-+-{'-'*10}-+-{'-'*12}-+-{'-'*12}-+-{'-'*16}")
        for s in self.substances:
            print(f"  {s.name:<22} | {s.mass:<10,.3f} | {s.specific_heat:<12,.1f} | "
                  f"{s.initial_temp:<12,.2f} | {s.heat_content():>16,.2f}")
        total_mc  = sum(s.thermal_capacity() for s in self.substances)
        total_mct = sum(s.heat_content()     for s in self.substances)
        print(f"\n  {'─'*72}")
        print(f"  Σ(m·c)   = {total_mc:>25,.4f}  J/°C")
        print(f"  Σ(m·c·T) = {total_mct:>25,.4f}  J")
        print(f"\n  ⭐ T_mix الأولية = {self._initial_mix_temp:.6f} °C")
        print(f"{sep}")

    def display_phase_log(self):
        sep = "═" * 72
        if not self._phase_log:
            print(f"\n{sep}")
            print("  ✅ لم تحدث أي تحولات طورية.")
            print(sep)
            return
        print(f"\n{sep}")
        print("  🔄 التحولات الطورية التي حدثت:")
        print(sep)
        for log in self._phase_log:
            print(log)
        print(sep)

    def display_final_result(self):
        sep = "═" * 72
        print(f"\n{sep}")
        print("  🎯 النتائج النهائية بعد التحولات الطورية")
        print(sep)
        print(f"\n  🌡️  درجة الحرارة النهائية: {self._final_mix_temp:.6f} °C\n")
        print(f"  {'المادة':<22} | {'m (kg)':<12} | {'T_final (°C)':<18} | الحالة")
        print(f"  {'-'*22}-+-{'-'*12}-+-{'-'*18}-+-{'-'*20}")
        for s in self.substances:
            st = s.final_state.value if s.final_state else "—"
            print(f"  {s.name:<22} | {s.mass:<12,.3f} | {s.final_temp:<18.6f} | {st}")
        print(f"\n{sep}")

    @property
    def initial_mix_temp(self) -> float:
        return self._initial_mix_temp

    @property
    def final_mix_temp(self) -> float:
        return self._final_mix_temp
