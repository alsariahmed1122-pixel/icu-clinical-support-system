from __future__ import annotations
from dataclasses import dataclass
import math
import random
from typing import Dict, Tuple, Optional

@dataclass
class SimProfile:
    """Patient profile without CHF, CKD, Hypercapnia risk"""
    sex: str = "M"
    age: int = 45
    weight_kg: float = 70.0

@dataclass
class VitalFrame:
    hr: float = 80.0
    sbp: float = 120.0
    dbp: float = 78.0
    spo2: float = 98.0
    rr: float = 16.0
    temp: float = 37.0
    etco2: float = 36.0

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))

class VitalsSim:
    def __init__(self, profile: Optional[SimProfile] = None) -> None:
        self._rng = random.Random(42)
        self._scenario = "Normal ICU Monitoring"
        self._time_s = 0.0
        self._pump_memory_s = 0.0
        self._oxygen_memory_s = 0.0
        self._manual_harm = 0.0
        self._untreated_harm = 0.0
        self._death_progress = 0.0
        self._recovery_buffer = 0.0
        self._arrest_elapsed = 0.0
        self.life_state = "ALIVE"
        self.doctor_call_required = False
        self.doctor_message = ""
        self.last_clinical_note = ""
        self.manual_error_flag = False
        self.last_manual_reason = ""
        self.v = VitalFrame()
        self.target = VitalFrame()
        self.profile = profile or SimProfile()
        self.reset()

    def reset(self) -> None:
        """Reset to Normal ICU Monitoring scenario"""
        self._time_s = 0.0
        self._pump_memory_s = 0.0
        self._oxygen_memory_s = 0.0
        self._manual_harm = 0.0
        self._untreated_harm = 0.0
        self._death_progress = 0.0
        self._recovery_buffer = 0.0
        self._arrest_elapsed = 0.0
        self.life_state = "ALIVE"
        self.doctor_call_required = False
        self.doctor_message = ""
        self.last_clinical_note = "Monitoring."
        self.manual_error_flag = False
        self.last_manual_reason = ""
        self.force_scenario("Normal ICU Monitoring")

    def force_scenario(self, scenario: str) -> None:
        self._scenario = str(scenario)
        base = self._scenario_baseline(self._scenario)
        self.v = VitalFrame(**base)
        self.target = VitalFrame(**base)
        self._manual_harm = 0.0
        self._untreated_harm = 0.0
        self._death_progress = 0.0
        self._recovery_buffer = 0.0
        self._arrest_elapsed = 0.0
        self.life_state = "ALIVE"
        self.doctor_call_required = False
        self.doctor_message = ""
        self.last_clinical_note = f"Scenario loaded: {self._scenario}"
        self.manual_error_flag = False
        self.last_manual_reason = ""

    def _scenario_baseline(self, scenario: str) -> Dict[str, float]:
        table: Dict[str, Dict[str, float]] = {
            "Normal ICU Monitoring": dict(hr=82, sbp=122, dbp=78, spo2=98, rr=16, temp=37.0, etco2=36),
            "Severe Dehydration": dict(hr=118, sbp=92, dbp=58, spo2=95, rr=22, temp=37.4, etco2=33),
            "Hypovolemic Shock": dict(hr=132, sbp=78, dbp=46, spo2=94, rr=26, temp=36.9, etco2=30),
            "Gastroenteritis Dehydration": dict(hr=110, sbp=96, dbp=60, spo2=96, rr=20, temp=37.8, etco2=34),
            "Early Sepsis": dict(hr=112, sbp=102, dbp=62, spo2=94, rr=24, temp=38.5, etco2=33),
            "Septic Shock": dict(hr=128, sbp=84, dbp=50, spo2=91, rr=28, temp=39.0, etco2=31),
            "Hemodynamic Instability": dict(hr=124, sbp=86, dbp=52, spo2=93, rr=25, temp=37.2, etco2=31),
            "Cardiogenic Shock": dict(hr=126, sbp=82, dbp=54, spo2=89, rr=28, temp=36.8, etco2=30),
            "Anaphylactic Shock": dict(hr=132, sbp=78, dbp=46, spo2=86, rr=30, temp=36.9, etco2=29),
            "Heat Exhaustion / Volume Loss": dict(hr=116, sbp=94, dbp=58, spo2=96, rr=22, temp=38.6, etco2=33),
            "Orthostatic / Volume Depletion": dict(hr=104, sbp=98, dbp=60, spo2=97, rr=18, temp=37.1, etco2=35),
            "Diuretic Overuse / Volume Depletion": dict(hr=108, sbp=96, dbp=60, spo2=96, rr=20, temp=37.0, etco2=34),
            "Adrenal Crisis": dict(hr=122, sbp=86, dbp=52, spo2=94, rr=24, temp=37.3, etco2=32),
            "Hypertensive Urgency": dict(hr=94, sbp=184, dbp=112, spo2=98, rr=18, temp=37.0, etco2=36),
            "Hypertensive Emergency": dict(hr=106, sbp=206, dbp=126, spo2=96, rr=24, temp=37.1, etco2=35),
            "Sympathetic Surge Hypertension": dict(hr=118, sbp=190, dbp=116, spo2=98, rr=24, temp=37.3, etco2=34),
            "Pulmonary Edema / Fluid Overload": dict(hr=118, sbp=168, dbp=98, spo2=86, rr=30, temp=37.0, etco2=32),
            "Pulmonary Edema": dict(hr=118, sbp=168, dbp=98, spo2=86, rr=30, temp=37.0, etco2=32),
            "Acute Hypoxemia": dict(hr=116, sbp=118, dbp=74, spo2=84, rr=30, temp=37.1, etco2=31),
            "Pneumonia / Oxygenation Drop": dict(hr=112, sbp=104, dbp=64, spo2=88, rr=28, temp=38.3, etco2=32),
            "Post-extubation Desaturation": dict(hr=108, sbp=114, dbp=70, spo2=87, rr=26, temp=37.0, etco2=33),
            "Mild Airway Obstruction": dict(hr=98, sbp=122, dbp=78, spo2=92, rr=24, temp=37.0, etco2=39),
            "V/Q Mismatch Event": dict(hr=110, sbp=118, dbp=72, spo2=86, rr=28, temp=37.1, etco2=32),
            "Respiratory Failure": dict(hr=122, sbp=112, dbp=70, spo2=80, rr=34, temp=37.4, etco2=30),
        }
        return table.get(scenario, table["Normal ICU Monitoring"]).copy()

    def _scenario_needs(self, scenario: str) -> Dict[str, object]:
        return {
            "pump": {
                "Severe Dehydration": "fluid",
                "Hypovolemic Shock": "fluid",
                "Gastroenteritis Dehydration": "fluid",
                "Heat Exhaustion / Volume Loss": "fluid",
                "Orthostatic / Volume Depletion": "fluid",
                "Diuretic Overuse / Volume Depletion": "fluid",
                "Adrenal Crisis": "fluid",
                "Early Sepsis": "fluid",
                "Septic Shock": "pressor",
                "Hemodynamic Instability": "pressor",
                "Cardiogenic Shock": "pressor",
                "Anaphylactic Shock": "pressor",
                "Hypertensive Urgency": "bp_control",
                "Hypertensive Emergency": "bp_control",
                "Sympathetic Surge Hypertension": "bp_control",
                "Pulmonary Edema / Fluid Overload": "diuretic",
                "Pulmonary Edema": "diuretic",
            }.get(scenario, "none"),
            "oxygen": {
                "Acute Hypoxemia": "oxygen",
                "Pneumonia / Oxygenation Drop": "oxygen",
                "Post-extubation Desaturation": "oxygen",
                "Mild Airway Obstruction": "oxygen",
                "V/Q Mismatch Event": "oxygen",
                "Pulmonary Edema / Fluid Overload": "oxygen",
                "Pulmonary Edema": "oxygen",
                "Respiratory Failure": "oxygen",
                "Anaphylactic Shock": "oxygen",
                "Cardiogenic Shock": "oxygen",
            }.get(scenario, "none"),
            "high_flow_ok": scenario in {"Acute Hypoxemia", "Pulmonary Edema / Fluid Overload", "Pulmonary Edema", "Respiratory Failure", "V/Q Mismatch Event", "Anaphylactic Shock", "Cardiogenic Shock"},
        }

    def _therapy_kind(self, therapy: str) -> str:
        name = (therapy or "").lower()
        if any(k in name for k in ["saline", "ringer", "balanced", "plasma"]):
            return "fluid"
        if any(k in name for k in ["norad", "norepi", "dopamine"]):
            return "pressor"
        if any(k in name for k in ["labetalol", "hydralazine"]):
            return "bp_control"
        if "furosemide" in name:
            return "diuretic"
        return "other"

    def _map(self) -> float:
        return (self.v.sbp + 2.0 * self.v.dbp) / 3.0

    def _age_factor(self) -> float:
        """Age factor: older patients respond slower - now uses actual patient age"""
        if self._time_s == 0:
            return 1.0
        age = self.profile.age
        return max(0.7, min(1.0, 1.0 - (age - 45) * 0.003))

    def _scenario_drift(self, dt: float) -> None:
        s = self._scenario
        base = self._scenario_baseline(s)
        self.target = VitalFrame(**base)
        if self.life_state == "DEAD":
            self.target = VitalFrame(hr=0.0, sbp=0.0, dbp=0.0, spo2=0.0, rr=0.0, temp=self.v.temp, etco2=0.0)
        elif self.life_state == "ARREST":
            self.target = VitalFrame(
                hr=max(0.0, self.v.hr - 12.0 * dt),
                sbp=max(0.0, self.v.sbp - 14.0 * dt),
                dbp=max(0.0, self.v.dbp - 10.0 * dt),
                spo2=max(0.0, self.v.spo2 - 5.0 * dt),
                rr=max(0.0, self.v.rr - 4.0 * dt),
                temp=self.v.temp,
                etco2=max(0.0, self.v.etco2 - 3.5 * dt),
            )
        elif s in {"Severe Dehydration", "Hypovolemic Shock", "Gastroenteritis Dehydration", "Orthostatic / Volume Depletion", "Diuretic Overuse / Volume Depletion", "Adrenal Crisis"}:
            self.target.hr += min(12.0, self._time_s * 0.02)
            self.target.sbp -= min(12.0, self._time_s * 0.03)
            self.target.dbp -= min(8.0, self._time_s * 0.02)
        elif s in {"Early Sepsis", "Septic Shock", "Hemodynamic Instability"}:
            self.target.hr += min(16.0, self._time_s * 0.03)
            self.target.sbp -= min(18.0, self._time_s * 0.035)
            self.target.spo2 -= min(5.0, self._time_s * 0.012)
            self.target.rr += min(7.0, self._time_s * 0.018)
        elif s in {"Cardiogenic Shock", "Anaphylactic Shock"}:
            self.target.hr += min(14.0, self._time_s * 0.025)
            self.target.sbp -= min(20.0, self._time_s * 0.036)
            self.target.spo2 -= min(7.0, self._time_s * 0.014)
            self.target.rr += min(7.0, self._time_s * 0.018)
        elif s in {"Acute Hypoxemia", "Pneumonia / Oxygenation Drop", "Post-extubation Desaturation", "Mild Airway Obstruction", "V/Q Mismatch Event", "Pulmonary Edema / Fluid Overload", "Pulmonary Edema", "Respiratory Failure"}:
            self.target.spo2 -= min(6.0, self._time_s * 0.022)
            self.target.rr += min(6.0, self._time_s * 0.018)
            self.target.hr += min(10.0, self._time_s * 0.015)
            self.target.etco2 += 1.5 if s == "Mild Airway Obstruction" else -1.0
        elif s in {"Hypertensive Urgency", "Hypertensive Emergency", "Sympathetic Surge Hypertension"}:
            self.target.sbp += 0.5 * math.sin(self._time_s / 6.0)
            self.target.dbp += 0.5 * math.sin(self._time_s / 7.0)
        
        # Illness burden and untreated deterioration
        if self.v.spo2 < 88:
            self._untreated_harm += 0.25 * dt
        if self._map() < 60:
            self._untreated_harm += 0.28 * dt
        if self.v.sbp > 205:
            self._untreated_harm += 0.18 * dt
        if self.v.rr > 34 or self.v.rr < 7:
            self._untreated_harm += 0.12 * dt
        
        # Manual harm directly bends target away from safety
        harm = self._manual_harm
        if harm > 0.0:
            self.target.spo2 -= min(10.0, harm * 0.10)
            self.target.sbp -= min(18.0, harm * 0.12)
            self.target.dbp -= min(10.0, harm * 0.08)
            self.target.hr += min(22.0, harm * 0.10)
            self.target.rr += min(10.0, harm * 0.06)
            self.target.etco2 += min(8.0, harm * 0.05)
        
        # Pre-arrest drift
        if self.life_state == "PRE_ARREST":
            self.target.hr = max(18.0, self.v.hr - 8.0 * dt)
            self.target.sbp = max(35.0, self.v.sbp - 10.0 * dt)
            self.target.dbp = max(15.0, self.v.dbp - 6.0 * dt)
            self.target.spo2 = max(35.0, self.v.spo2 - 4.0 * dt)
            self.target.rr = max(2.0, self.v.rr - 3.0 * dt)
            self.target.etco2 = max(8.0, self.v.etco2 - 2.0 * dt)
        
        # Apply age factor to response speed
        age_factor = self._age_factor()
        alpha = min(1.0, 0.20 * dt * age_factor)
        for attr in ("hr", "sbp", "dbp", "spo2", "rr", "temp", "etco2"):
            current = getattr(self.v, attr)
            desired = getattr(self.target, attr)
            noise = self._rng.uniform(-1.0, 1.0)
            if attr in {"temp", "spo2"}:
                noise *= 0.06
            elif attr == "etco2":
                noise *= 0.12
            else:
                noise *= 0.28
            setattr(self.v, attr, current + (desired - current) * alpha + noise)

    def _judge_pump(self, therapy: str, rate_mlh: float) -> Tuple[bool, float, str]:
        need = self._scenario_needs(self._scenario)["pump"]
        kind = self._therapy_kind(therapy)
        rate = max(0.0, float(rate_mlh))
        if need == "none":
            if rate == 0:
                return True, 0.0, "No pump therapy required."
            return False, 0.8, "Unnecessary pump therapy for this scenario."
        correct = kind == need
        if need == "fluid" and correct:
            if rate < 60:
                return False, 0.3, "Manual fluid too low for circulatory support."
            if rate > 260:
                return False, 0.8, "Manual fluid too aggressive and may worsen the case."
            return True, 0.8, "Manual fluid support appropriate."
        if need == "pressor" and correct:
            if rate < 6:
                return False, 0.3, "Manual vasopressor too low."
            if rate > 22:
                return False, 0.9, "Manual vasopressor too high and unsafe."
            return True, 0.9, "Manual vasopressor support appropriate."
        if need == "bp_control" and correct:
            if rate < 4:
                return False, 0.3, "Manual antihypertensive too low."
            if rate > 16:
                return False, 0.8, "Manual antihypertensive too aggressive."
            return True, 0.85, "Manual blood-pressure control appropriate."
        if need == "diuretic" and correct:
            if rate < 3:
                return False, 0.3, "Manual diuretic support too low."
            if rate > 12:
                return False, 0.7, "Manual diuretic too aggressive."
            return True, 0.8, "Manual diuretic support appropriate."
        severe = 1.1 if self._scenario in {"Cardiogenic Shock", "Pulmonary Edema / Fluid Overload", "Hypertensive Emergency", "Septic Shock", "Anaphylactic Shock"} else 0.8
        return False, severe, f"Wrong manual pump therapy: expected {need}, received {kind}."

    def _judge_oxygen(self, flow_l_min: float, fio2: float) -> Tuple[bool, float, str]:
        need = self._scenario_needs(self._scenario)["oxygen"]
        flow = max(0.0, float(flow_l_min))
        fio2 = max(0.21, min(1.0, float(fio2)))
        if need == "none":
            if flow <= 0.0:
                return True, 0.0, "No oxygen support required."
            if fio2 > 0.50 or flow > 8.0:
                return False, 0.8, "Unnecessary high oxygen may worsen a non-hypoxemic patient."
            return False, 0.35, "Unnecessary manual oxygen support."
        if flow < 1.5 or fio2 < 0.26:
            return False, 0.5, "Manual oxygen support too low for the current hypoxemia."
        if self._scenario_needs(self._scenario)["high_flow_ok"]:
            if flow > 12.0 or fio2 > 0.80:
                return False, 0.7, "Manual oxygen excessive for the current scenario."
        else:
            if flow > 8.0 or fio2 > 0.60:
                return False, 0.6, "Manual oxygen higher than needed."
        return True, 0.9, "Manual oxygen support appropriate."

    def apply_pump_effect(self, dt: float, rate_mlh: float, therapy: str, auto_generated: bool = False) -> None:
        rate = max(0.0, float(rate_mlh))
        if rate <= 0.0 or self.life_state == "DEAD":
            return
        self._pump_memory_s = min(180.0, self._pump_memory_s + dt)
        tscale = min(1.0, self._pump_memory_s / 12.0)
        kind = self._therapy_kind(therapy)
        if auto_generated:
            correct, strength, note = True, 1.0, "Limited emergency pump support active; partial stabilization target."
        else:
            correct, strength, note = self._judge_pump(therapy, rate)
        self.last_clinical_note = note
        if not auto_generated:
            self.manual_error_flag = not correct
            self.last_manual_reason = note if not correct else ""
        if correct:
            self._manual_harm = max(0.0, self._manual_harm - 0.8 * dt)
            self._recovery_buffer += 0.4 * dt
        else:
            self._manual_harm += strength * 2.4 * dt
            if not auto_generated:
                self.doctor_call_required = True
                self.doctor_message = f"Wrong manual pump setting detected. Call Dr. Ahmed Mohamed Aljak • 0903600668"
        # Reduced coefficients for smoother response
        if kind == "fluid":
            vol = min(1.0, rate / 180.0) * tscale * strength
            if correct:
                self.v.sbp += 0.95 * vol * dt
                self.v.dbp += 0.65 * vol * dt
                self.v.hr -= 0.45 * vol * dt
                self._untreated_harm = max(0.0, self._untreated_harm - 0.18 * dt)
            else:
                self.v.spo2 -= 0.30 * vol * dt
                self.v.rr += 0.18 * vol * dt
                self.v.sbp -= 0.15 * vol * dt
        elif kind == "pressor":
            press = min(1.0, rate / 18.0) * tscale * strength
            if correct:
                self.v.sbp += 1.10 * press * dt
                self.v.dbp += 0.70 * press * dt
                self._untreated_harm = max(0.0, self._untreated_harm - 0.16 * dt)
                self.v.hr -= 0.10 * press * dt if self.v.hr > 120 else 0.0
            else:
                self.v.hr += 0.40 * press * dt
                self.v.spo2 -= 0.10 * press * dt
                self.v.sbp += 0.25 * press * dt if self._scenario.startswith("Hypertensive") else -0.20 * press * dt
        elif kind == "bp_control":
            anti = min(1.0, rate / 12.0) * tscale * strength
            if correct:
                self.v.sbp -= 0.85 * anti * dt
                self.v.dbp -= 0.60 * anti * dt
                self._untreated_harm = max(0.0, self._untreated_harm - 0.12 * dt)
                self.v.hr -= 0.10 * anti * dt
            else:
                self.v.sbp -= 0.60 * anti * dt
                self.v.dbp -= 0.35 * anti * dt
                self.v.hr += 0.25 * anti * dt
                self.v.spo2 -= 0.10 * anti * dt
        elif kind == "diuretic":
            diur = min(1.0, rate / 10.0) * tscale * strength
            if correct:
                self.v.spo2 += 0.20 * diur * dt
                self.v.rr -= 0.20 * diur * dt
                self._untreated_harm = max(0.0, self._untreated_harm - 0.10 * dt)
                self.v.sbp -= 0.10 * diur * dt
            else:
                self.v.sbp -= 0.42 * diur * dt
                self.v.dbp -= 0.26 * diur * dt
                self.v.hr += 0.22 * diur * dt
        else:
            if not correct:
                self._manual_harm += 0.5 * dt

    def apply_oxygen_effect(self, dt: float, flow_l_min: float, fio2: float, mode: str, auto_generated: bool = False) -> None:
        flow = max(0.0, float(flow_l_min))
        fio2 = max(0.21, min(1.0, float(fio2)))
        if flow <= 0.0 or self.life_state == "DEAD":
            return
        self._oxygen_memory_s = min(180.0, self._oxygen_memory_s + dt)
        tscale = min(1.0, self._oxygen_memory_s / 8.0)
        if auto_generated:
            correct, strength, note = True, 1.0, "Limited emergency oxygen support active; partial stabilization target."
        else:
            correct, strength, note = self._judge_oxygen(flow, fio2)
        self.last_clinical_note = note
        if not auto_generated:
            self.manual_error_flag = self.manual_error_flag or (not correct)
            if not correct:
                self.last_manual_reason = note
        if correct:
            self._manual_harm = max(0.0, self._manual_harm - 0.6 * dt)
            self._recovery_buffer += 0.45 * dt
        else:
            self._manual_harm += strength * 2.1 * dt
            if not auto_generated:
                self.doctor_call_required = True
                self.doctor_message = f"Wrong manual oxygen setting detected. Call Dr. Ahmed Mohamed Aljak • 0903600668"
        support = min(1.0, ((flow / 4.0) + ((fio2 - 0.21) / 0.15)) / 2.0) * tscale * strength
        if correct:
            self.v.spo2 += 0.45 * support * dt  # Reduced from 1.50 for more realistic response
            self.v.rr -= 0.30 * support * dt
            self._untreated_harm = max(0.0, self._untreated_harm - 0.14 * dt)
            self.v.hr -= 0.12 * support * dt if self.v.hr > 105 else 0.0
            self.v.etco2 -= 0.08 * support * dt
        else:
            self.v.spo2 -= 0.25 * support * dt
            self.v.rr += 0.18 * support * dt
            self.v.etco2 += 0.18 * support * dt

    def evaluate_global_state(self, dt: float, auto_active: bool = False) -> None:
        severe = 0.0
        if self.v.spo2 < 82:
            severe += 1.2
        elif self.v.spo2 < 88:
            severe += 0.4
        if self._map() < 55:
            severe += 1.3
        elif self._map() < 65:
            severe += 0.4
        if self.v.hr < 35 or self.v.hr > 170:
            severe += 1.0
        if self.v.rr < 6 or self.v.rr > 38:
            severe += 0.6
        
        # Auto rescue should protect rather than harm
        if auto_active:
            self._untreated_harm = max(0.0, self._untreated_harm - 0.25 * dt)
            if severe > 0.0:
                self._death_progress = max(0.0, self._death_progress - 0.08 * dt)
        
        burden = severe + self._manual_harm * 0.18 + self._untreated_harm * 0.10
        
        # Death from manual harm > 2.0 OR untreated harm > 3.0 (patient dies without treatment)
        if self._manual_harm > 2.0 or self._untreated_harm > 3.0:
            self._death_progress += burden * 0.12 * dt
        else:
            self._death_progress = max(0.0, self._death_progress - 0.05 * dt)
        
        if self._manual_harm > 4.0 and self.life_state == "ALIVE":
            self.doctor_call_required = True
            if not self.doctor_message:
                self.doctor_message = "Manual treatment is worsening the patient. Call Dr. Ahmed Mohamed Aljak • 0903600668"
        
        if self._death_progress >= 5.6 and self.life_state == "ALIVE":
            self.life_state = "PRE_ARREST"
            self.doctor_call_required = True
            self.doctor_message = "Pre-arrest deterioration. Call Dr. Ahmed Mohamed Aljak • 0903600668"
            self.last_clinical_note = "Critical deterioration with imminent arrest."
        
        if self._death_progress >= 9.4 and self.life_state in {"ALIVE", "PRE_ARREST"}:
            self.life_state = "ARREST"
            self._arrest_elapsed = 0.0
            self.doctor_call_required = True
            self.doctor_message = "Cardiac arrest in progress. Call Dr. Ahmed Mohamed Aljak • 0903600668"
            self.last_clinical_note = "Cardiac arrest is active; monitor is collapsing to flatline."
        
        if self.life_state == "PRE_ARREST":
            self.v.hr = max(14.0, self.v.hr - 2.8 * dt)
            self.v.sbp = max(28.0, self.v.sbp - 3.8 * dt)
            self.v.dbp = max(10.0, self.v.dbp - 2.4 * dt)
            self.v.spo2 = max(30.0, self.v.spo2 - 1.8 * dt)
            self.v.rr = max(1.0, self.v.rr - 1.4 * dt)
            self.v.etco2 = max(6.0, self.v.etco2 - 1.1 * dt)
        elif self.life_state == "ARREST":
            self._arrest_elapsed += dt
            self.v.hr = max(0.0, self.v.hr - 7.0 * dt)
            self.v.sbp = max(0.0, self.v.sbp - 8.5 * dt)
            self.v.dbp = max(0.0, self.v.dbp - 6.0 * dt)
            self.v.rr = max(0.0, self.v.rr - 2.4 * dt)
            self.v.etco2 = max(0.0, self.v.etco2 - 2.1 * dt)
            self.v.spo2 = max(0.0, self.v.spo2 - 3.2 * dt)
            if self._arrest_elapsed >= 4.0:
                self.life_state = "DEAD"
                self.v.hr = 0.0
                self.v.sbp = 0.0
                self.v.dbp = 0.0
                self.v.rr = 0.0
                self.v.spo2 = 0.0
                self.v.etco2 = 0.0
                self.doctor_call_required = True
                self.doctor_message = "No vital signs. Call Dr. Ahmed Mohamed Aljak • 0903600668"
                self.last_clinical_note = "Cardiac arrest completed; flatline / no vital signs."
        elif self.life_state == "DEAD":
            self.v.hr = 0.0
            self.v.sbp = 0.0
            self.v.dbp = 0.0
            self.v.rr = 0.0
            self.v.etco2 = max(0.0, self.v.etco2 - 2.4 * dt)
            self.v.spo2 = max(0.0, self.v.spo2 - 6.0 * dt)

    def _finalize(self) -> None:
        if self.life_state != "DEAD":
            if self.v.spo2 < 90:
                self.v.hr += 0.5
                self.v.rr += 0.4
            if self._map() < 90:
                self.v.hr += 0.25
            if self.v.rr > 30:
                self.v.etco2 -= 0.15
            if self.v.rr < 10:
                self.v.etco2 += 0.15
        self.v.hr = _clamp(self.v.hr, 0 if self.life_state == "DEAD" else 20, 220)
        self.v.sbp = _clamp(self.v.sbp, 0 if self.life_state == "DEAD" else 40, 240)
        self.v.dbp = _clamp(self.v.dbp, 0 if self.life_state == "DEAD" else 15, 150)
        self.v.spo2 = _clamp(self.v.spo2, 0, 100)
        self.v.rr = _clamp(self.v.rr, 0 if self.life_state == "DEAD" else 2, 50)
        self.v.temp = _clamp(self.v.temp, 34, 41)
        self.v.etco2 = _clamp(self.v.etco2, 0, 60)
        if self.life_state != "DEAD" and self.v.dbp > self.v.sbp - 8:
            self.v.dbp = max(20.0, self.v.sbp - 8.0)

    def tick(self, dt: float = 1.0, scenario: str | None = None) -> VitalFrame:
        """Default tick is 1.0 second"""
        dt = max(0.01, float(dt))
        if scenario is not None and str(scenario) != self._scenario:
            self.force_scenario(str(scenario))
        self._time_s += dt
        self._pump_memory_s = max(0.0, self._pump_memory_s - dt * 0.6)
        self._oxygen_memory_s = max(0.0, self._oxygen_memory_s - dt * 0.4)
        self._manual_harm = max(0.0, self._manual_harm - 0.03 * dt)
        self._scenario_drift(dt)
        # Removed duplicate evaluate_global_state call - it's called from app_streamlit.py
        self._finalize()
        return self.v