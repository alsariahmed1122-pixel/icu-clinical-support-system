from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class ICUSettings:
    target_map_mmHg: float = 65.0
    low_sbp_mmHg: float = 90.0
    low_dbp_mmHg: float = 60.0
    severe_sbp_mmHg: float = 80.0
    severe_dbp_mmHg: float = 50.0
    high_sbp_mmHg: float = 180.0
    high_dbp_mmHg: float = 110.0
    severe_high_sbp_mmHg: float = 200.0
    severe_high_dbp_mmHg: float = 120.0
    low_spo2_pct: float = 90.0
    severe_low_spo2_pct: float = 85.0
    auto_intervene_after_sec: float = 10.0
    min_auto_intervene_after_sec: float = 10.0
    max_auto_intervene_after_sec: float = 10.0
    trend_memory_points: int = 30
    max_flow_mlh: float = 1000.0
    conservative_o2_flow_limit: float = 8.0
    conservative_o2_fio2_limit: float = 0.50
    conservative_fluid_rate_limit: float = 220.0
    conservative_pressor_rate_limit: float = 20.0
    conservative_bp_control_rate_limit: float = 14.0
    recovery_watch_sec: float = 8.0
    oxygen_wean_step_sec: float = 4.0
    pump_wean_step_sec: float = 5.0
    oxygen_adjust_sec: float = 2.0
    pump_adjust_sec: float = 3.0

@dataclass
class PatientProfile:
    """Without CHF, CKD, Hypercapnia risk"""
    patient_id: str
    sex: str = "M"
    age: int = 45
    weight_kg: float = 70.0

@dataclass
class PumpCommand:
    action: str
    drug: str
    rate_mlh: float
    duration_min: float
    reason: str = ""
    auto_generated: bool = False

@dataclass
class PumpStatus:
    running: bool = False
    drug: str = "0.9% Normal Saline"
    rate_mlh: float = 0.0
    duration_min: float = 0.0
    time_left_sec: float = 0.0
    infused_ml: float = 0.0
    last_msg: str = "Pump ready."
    auto_started: bool = False

@dataclass
class OxygenCommand:
    action: str
    mode: str
    flow_l_min: float
    fio2: float
    duration_min: float
    reason: str = ""
    auto_generated: bool = False

@dataclass
class OxygenStatus:
    running: bool = False
    mode: str = "O2 Standby"
    flow_l_min: float = 0.0
    fio2: float = 0.21
    duration_min: float = 0.0
    time_left_sec: float = 0.0
    last_msg: str = "Oxygen controller ready."
    auto_started: bool = False

@dataclass
class AlertChannel:
    state: str = "NORMAL"
    problem: str = "No active alarm"
    message: str = "Monitoring."
    pending: bool = False
    pending_left: float = 0.0
    auto_executed: bool = False
    latched: bool = False
    latched_problem: str = ""
    latched_message: str = ""
    risk_score: float = 0.0
    confidence: float = 0.0
    dynamic_window: float = 0.0
    trend_hint: str = "stable"
    domain: str = ""
    recovery_watch: bool = False
    stable_for_sec: float = 0.0
    cooldown_sec: float = 0.0
    last_adjust_sec: float = 0.0

class InfusionPumpSim:
    def __init__(self, max_flow_mlh: float = 1000.0):
        self.max_flow_mlh = float(max_flow_mlh)
        self.drugs: Dict[str, Dict[str, float]] = {
            "0.9% Normal Saline": {"default_rate": 180.0, "default_duration": 16.0},
            "Ringer Lactate": {"default_rate": 180.0, "default_duration": 16.0},
            "Balanced Crystalloid": {"default_rate": 200.0, "default_duration": 16.0},
            "Plasma-Lyte A": {"default_rate": 190.0, "default_duration": 16.0},
            "Dopamine": {"default_rate": 14.0, "default_duration": 18.0},
            "Noradrenaline": {"default_rate": 16.0, "default_duration": 18.0},
            "Norepinephrine": {"default_rate": 16.0, "default_duration": 18.0},
            "Labetalol": {"default_rate": 8.0, "default_duration": 18.0},
            "Hydralazine": {"default_rate": 8.0, "default_duration": 18.0},
            "Furosemide inj": {"default_rate": 8.0, "default_duration": 16.0},
        }
        self.status = PumpStatus()

    def apply(self, cmd: PumpCommand) -> None:
        action = str(cmd.action).upper().strip()
        if action == "STOP":
            self.status.running = False
            self.status.rate_mlh = 0.0
            self.status.duration_min = 0.0
            self.status.time_left_sec = 0.0
            self.status.auto_started = False
            self.status.last_msg = "Pump stopped."
            return
        if action in ("START", "SET"):
            self.status.drug = cmd.drug
            self.status.rate_mlh = max(0.0, min(float(cmd.rate_mlh), self.max_flow_mlh))
            self.status.duration_min = max(0.0, float(cmd.duration_min))
            self.status.time_left_sec = self.status.duration_min * 60.0
            self.status.running = self.status.rate_mlh > 0.0 and self.status.time_left_sec > 0.0
            self.status.auto_started = bool(cmd.auto_generated)
            prefix = "AUTO" if cmd.auto_generated else action
            self.status.last_msg = f"{prefix}: {cmd.drug} @ {self.status.rate_mlh:.0f} mL/h for {self.status.duration_min:.0f} min. {cmd.reason}"

    def tick(self, dt_sec: float) -> None:
        if not self.status.running:
            return
        dt = max(0.0, float(dt_sec))
        self.status.infused_ml += (self.status.rate_mlh / 3600.0) * dt
        self.status.time_left_sec = max(0.0, self.status.time_left_sec - dt)
        if self.status.time_left_sec <= 0.0:
            self.status.running = False
            self.status.rate_mlh = 0.0
            self.status.duration_min = 0.0
            self.status.auto_started = False
            self.status.last_msg = "Pump program complete."

    def get_status(self) -> PumpStatus:
        return self.status

class OxygenControllerSim:
    def __init__(self):
        self.status = OxygenStatus()
        self.modes = {
            "O2 Boost (SIM)": {"flow": 4.0, "fio2": 0.36, "duration": 12.0},
            "High O2 Support (SIM)": {"flow": 7.0, "fio2": 0.50, "duration": 14.0},
            "Controlled Wean (SIM)": {"flow": 2.0, "fio2": 0.28, "duration": 10.0},
        }

    def apply(self, cmd: OxygenCommand) -> None:
        action = str(cmd.action).upper().strip()
        if action == "STOP":
            self.status.running = False
            self.status.flow_l_min = 0.0
            self.status.fio2 = 0.21
            self.status.duration_min = 0.0
            self.status.time_left_sec = 0.0
            self.status.auto_started = False
            self.status.last_msg = "Oxygen controller stopped."
            return
        if action in ("START", "SET"):
            self.status.mode = cmd.mode
            self.status.flow_l_min = max(0.0, float(cmd.flow_l_min))
            self.status.fio2 = max(0.21, min(float(cmd.fio2), 1.0))
            self.status.duration_min = max(0.0, float(cmd.duration_min))
            self.status.time_left_sec = self.status.duration_min * 60.0
            self.status.running = self.status.duration_min > 0.0 and self.status.flow_l_min > 0.0
            self.status.auto_started = bool(cmd.auto_generated)
            prefix = "AUTO" if cmd.auto_generated else action
            self.status.last_msg = f"{prefix}: {cmd.mode} • Flow {self.status.flow_l_min:.1f} L/min • FiO₂ {self.status.fio2:.2f} • {cmd.reason}"

    def tick(self, dt_sec: float) -> None:
        if not self.status.running:
            return
        dt = max(0.0, float(dt_sec))
        self.status.time_left_sec = max(0.0, self.status.time_left_sec - dt)
        if self.status.time_left_sec <= 0.0:
            self.status.running = False
            self.status.flow_l_min = 0.0
            self.status.fio2 = 0.21
            self.status.duration_min = 0.0
            self.status.auto_started = False
            self.status.last_msg = "Oxygen program complete."

    def get_status(self) -> OxygenStatus:
        return self.status

class ClinicalSupportEngine:
    def __init__(self, settings: ICUSettings):
        self.settings = settings
        self.reset()

    def reset(self) -> None:
        self.channels = {"bp": AlertChannel(domain="bp"), "spo2": AlertChannel(domain="spo2")}
        self.history: Dict[str, List[float]] = {"map": [], "spo2": [], "hr": [], "rr": []}

    @staticmethod
    def compute_map(sbp: float, dbp: float) -> float:
        return (float(sbp) + 2.0 * float(dbp)) / 3.0

    def _append_history(self, name: str, value: float) -> None:
        bucket = self.history.setdefault(name, [])
        bucket.append(float(value))
        keep = max(5, int(self.settings.trend_memory_points))
        if len(bucket) > keep:
            del bucket[:-keep]

    def _slope(self, name: str) -> float:
        values = self.history.get(name, [])
        if len(values) < 2:
            return 0.0
        window = values[-min(6, len(values)):]
        return float(window[-1] - window[0])

    def classify_bp(self, sbp: float, dbp: float) -> str:
        map_v = self.compute_map(sbp, dbp)
        if sbp <= self.settings.severe_sbp_mmHg or dbp <= self.settings.severe_dbp_mmHg or map_v < 55:
            return "SEVERE_HYPOTENSION"
        if sbp < self.settings.low_sbp_mmHg or dbp < self.settings.low_dbp_mmHg or map_v < self.settings.target_map_mmHg:
            return "LOW_BP"
        if sbp >= self.settings.severe_high_sbp_mmHg or dbp >= self.settings.severe_high_dbp_mmHg:
            return "HYPERTENSIVE_CRISIS"
        if sbp >= self.settings.high_sbp_mmHg or dbp >= self.settings.high_dbp_mmHg:
            return "HIGH_BP"
        return "NORMAL"

    def classify_spo2(self, spo2: float) -> str:
        if spo2 <= self.settings.severe_low_spo2_pct:
            return "SEVERE_HYPOXEMIA"
        if spo2 < self.settings.low_spo2_pct:
            return "LOW_SPO2"
        return "NORMAL"

    def therapy_for_scenario(self, scenario: str, domain: str, state: str) -> str:
        if domain == "bp":
            low_map = {
                "Severe Dehydration": "Ringer Lactate",
                "Hypovolemic Shock": "Ringer Lactate",
                "Gastroenteritis Dehydration": "Ringer Lactate",
                "Heat Exhaustion / Volume Loss": "Ringer Lactate",
                "Orthostatic / Volume Depletion": "0.9% Normal Saline",
                "Diuretic Overuse / Volume Depletion": "0.9% Normal Saline",
                "Early Sepsis": "Balanced Crystalloid",
                "Septic Shock": "Noradrenaline",
                "Hemodynamic Instability": "Noradrenaline",
                "Cardiogenic Shock": "Dopamine",
                "Anaphylactic Shock": "Noradrenaline",
                "Adrenal Crisis": "0.9% Normal Saline",
                "Hypertensive Urgency": "Labetalol",
                "Hypertensive Emergency": "Labetalol",
                "Sympathetic Surge Hypertension": "Hydralazine",
                "Pulmonary Edema / Fluid Overload": "Furosemide inj",
                "Pulmonary Edema": "Furosemide inj",
                "Acute Hypoxemia": "0.9% Normal Saline",
            }
            if state == "SEVERE_HYPOTENSION" and scenario not in low_map:
                return "Noradrenaline"
            return low_map.get(scenario, "Balanced Crystalloid")
        if domain == "spo2":
            spo2_map = {
                "Acute Hypoxemia": "O2 Boost (SIM)",
                "Pneumonia / Oxygenation Drop": "High O2 Support (SIM)",
                "Post-extubation Desaturation": "O2 Boost (SIM)",
                "Mild Airway Obstruction": "O2 Boost (SIM)",
                "V/Q Mismatch Event": "High O2 Support (SIM)",
                "Pulmonary Edema / Fluid Overload": "High O2 Support (SIM)",
                "Pulmonary Edema": "High O2 Support (SIM)",
                "Respiratory Failure": "High O2 Support (SIM)",
                "Anaphylactic Shock": "High O2 Support (SIM)",
                "Cardiogenic Shock": "High O2 Support (SIM)",
            }
            if state == "SEVERE_HYPOXEMIA":
                return "High O2 Support (SIM)"
            return spo2_map.get(scenario, "O2 Boost (SIM)")
        return "No therapy"

    def _profile_factor(self, profile: PatientProfile) -> float:
        """Age and sex factor, without CHF/CKD"""
        factor = max(0.75, min(1.15, float(profile.weight_kg) / 70.0))
        if profile.age >= 80:
            factor *= 0.75
        elif profile.age >= 70:
            factor *= 0.84
        elif profile.age >= 60:
            factor *= 0.92
        if str(profile.sex).upper() == "F":
            factor *= 0.98
        return factor

    def _bp_risk(self, vitals: Dict[str, float], state: str) -> Tuple[float, float, str]:
        map_v = self.compute_map(vitals["sbp"], vitals["dbp"])
        map_slope = self._slope("map")
        risk = 0.0
        confidence = 0.0
        trend_hint = "stable"
        if state == "LOW_BP":
            risk += 3.0; confidence += 2.0
        elif state == "SEVERE_HYPOTENSION":
            risk += 5.0; confidence += 3.0
        elif state == "HIGH_BP":
            risk += 2.0; confidence += 2.0
        elif state == "HYPERTENSIVE_CRISIS":
            risk += 4.0; confidence += 3.0
        hr = float(vitals.get("hr", 0.0)); rr = float(vitals.get("rr", 0.0))
        if map_v < 60 and hr > 110:
            risk += 2.0; confidence += 1.0
        if map_v < 55 and rr > 24:
            risk += 1.0; confidence += 1.0
        if map_slope <= -5.0:
            risk += 2.0; trend_hint = "falling_fast"
        elif map_slope <= -2.0:
            risk += 1.0; trend_hint = "falling"
        elif map_slope >= 4.0:
            trend_hint = "rising"
        return risk, confidence, trend_hint

    def _spo2_risk(self, vitals: Dict[str, float], state: str) -> Tuple[float, float, str]:
        spo2 = float(vitals["spo2"])
        spo2_slope = self._slope("spo2")
        risk = 0.0; confidence = 0.0; trend_hint = "stable"
        if state == "LOW_SPO2":
            risk += 3.0; confidence += 2.0
        elif state == "SEVERE_HYPOXEMIA":
            risk += 5.0; confidence += 3.0
        rr = float(vitals.get("rr", 0.0)); hr = float(vitals.get("hr", 0.0))
        if spo2 < 88 and rr > 24:
            risk += 1.5; confidence += 1.0
        if spo2 < 85 and hr > 120:
            risk += 1.0; confidence += 1.0
        if spo2_slope <= -3.0:
            risk += 2.0; trend_hint = "falling_fast"
        elif spo2_slope <= -1.5:
            risk += 1.0; trend_hint = "falling"
        elif spo2_slope >= 1.0:
            trend_hint = "recovering"
        return risk, confidence, trend_hint

    def _dynamic_window(self, risk: float, trend_hint: str) -> float:
        """Dynamic window based on risk level and trend"""
        base_window = 10.0
        if risk >= 7.0:
            base_window = 6.0
        elif risk >= 5.0:
            base_window = 8.0
        elif risk >= 3.0:
            base_window = 10.0
        else:
            base_window = 12.0
        
        if trend_hint == "falling_fast":
            base_window *= 0.7
        elif trend_hint == "falling":
            base_window *= 0.85
        elif trend_hint == "rising" or trend_hint == "recovering":
            base_window *= 1.2
        
        return max(6.0, min(15.0, base_window))

    def build_bp_command(self, profile: PatientProfile, scenario: str, state: str, current_rate: float = 0.0) -> PumpCommand:
        therapy = self.therapy_for_scenario(scenario, "bp", state)
        factor = self._profile_factor(profile)
        if therapy in {"Ringer Lactate", "0.9% Normal Saline", "Balanced Crystalloid", "Plasma-Lyte A"}:
            base_rate = 110.0 if state == "LOW_BP" else 150.0
            rate = base_rate * factor
            if current_rate > 0:
                rate = min(self.settings.conservative_fluid_rate_limit, max(current_rate + 20.0, rate))
            rate = max(60.0, min(rate, self.settings.conservative_fluid_rate_limit))
            duration = 8.0
        elif therapy in {"Dopamine", "Noradrenaline", "Norepinephrine"}:
            base_rate = 10.0 if state == "LOW_BP" else 14.0
            rate = base_rate * max(0.85, factor)
            if current_rate > 0:
                rate = min(self.settings.conservative_pressor_rate_limit, max(current_rate + 2.0, rate))
            rate = max(6.0, min(rate, self.settings.conservative_pressor_rate_limit))
            duration = 8.0
        elif therapy in {"Labetalol", "Hydralazine"}:
            base_rate = 6.0 if state == "HIGH_BP" else 8.0
            rate = base_rate * factor
            if current_rate > 0:
                rate = min(self.settings.conservative_bp_control_rate_limit, max(current_rate + 1.5, rate))
            rate = max(4.0, min(rate, self.settings.conservative_bp_control_rate_limit))
            duration = 8.0
        elif therapy == "Furosemide inj":
            rate = 6.0 if state == "HIGH_BP" else 8.0
            if current_rate > 0:
                rate = min(10.0, max(current_rate + 1.0, rate))
            duration = 8.0
        else:
            rate = 80.0; duration = 6.0
        return PumpCommand("START" if current_rate <= 0 else "SET", therapy, float(round(rate, 0)), float(round(duration, 0)), f"Adaptive conservative support for {scenario}.", True)

    def build_oxygen_command(self, profile: PatientProfile, scenario: str, state: str, current_flow: float = 0.0, current_fio2: float = 0.21) -> OxygenCommand:
        mode = self.therapy_for_scenario(scenario, "spo2", state)
        severe = state == "SEVERE_HYPOXEMIA"
        flow = 4.0 if not severe else 6.0
        fio2 = 0.34 if not severe else 0.45
        duration = 8.0
        if current_flow > 0:
            flow = max(flow, current_flow + 1.0)
            fio2 = max(fio2, round(current_fio2 + 0.04, 2))
        flow = max(2.0, min(flow, self.settings.conservative_o2_flow_limit))
        fio2 = max(0.24, min(fio2, self.settings.conservative_o2_fio2_limit))
        return OxygenCommand("START" if current_flow <= 0 else "SET", mode, float(round(flow, 1)), float(round(fio2, 2)), float(round(duration, 0)), "Adaptive conservative oxygen rescue.", True)

    def _clear_channel(self, ch: AlertChannel, message: str) -> None:
        domain = ch.domain
        ch.__dict__.update(AlertChannel(domain=domain).__dict__)
        ch.message = message

    def _manual_hold(self) -> None:
        for ch in self.channels.values():
            if ch.pending:
                ch.pending = False; ch.pending_left = 0.0; ch.auto_executed = False
            if not ch.latched:
                ch.message = "Manual override active. Monitoring only."

    def _therapy_kind(self, therapy: str) -> str:
        name = (therapy or "").lower()
        if any(k in name for k in ["saline", "ringer", "balanced", "plasma"]): return "fluid"
        if any(k in name for k in ["norad", "norepi", "dopamine"]): return "pressor"
        if any(k in name for k in ["labetalol", "hydralazine"]): return "bp_control"
        if "furosemide" in name: return "diuretic"
        return "other"

    def _recovery_ready_bp(self, vitals: Dict[str, float]) -> bool:
        map_v = self.compute_map(vitals["sbp"], vitals["dbp"])
        return map_v >= 70.0 and float(vitals["sbp"]) >= 100.0 and self._slope("map") >= -1.0

    def _recovery_ready_spo2(self, vitals: Dict[str, float]) -> bool:
        return float(vitals["spo2"]) >= 94.0 and float(vitals.get("rr", 0.0)) <= 24.0 and self._slope("spo2") >= -0.6

    def _update_recovery_clock(self, ch: AlertChannel, ready: bool, dt: float) -> None:
        ch.cooldown_sec = max(0.0, ch.cooldown_sec - dt)
        ch.last_adjust_sec = max(0.0, ch.last_adjust_sec - dt)
        if ready:
            ch.recovery_watch = True
            ch.stable_for_sec += dt
        else:
            ch.recovery_watch = False
            ch.stable_for_sec = 0.0
            ch.cooldown_sec = 0.0

    def _reduce_pump_command(self, status: PumpStatus) -> PumpCommand:
        kind = self._therapy_kind(status.drug)
        rate = float(status.rate_mlh)
        if kind == "fluid":
            new_rate = max(35.0, rate - 25.0)
            if rate <= 40.0: return PumpCommand("STOP", status.drug, 0.0, 0.0, "Auto recovery: support no longer required.", True)
        elif kind == "pressor":
            new_rate = max(4.0, rate - 2.0)
            if rate <= 6.0: return PumpCommand("STOP", status.drug, 0.0, 0.0, "Auto recovery: pressure stabilized.", True)
        elif kind == "bp_control":
            new_rate = max(2.0, rate - 2.0)
            if rate <= 4.0: return PumpCommand("STOP", status.drug, 0.0, 0.0, "Auto recovery: blood pressure normalized.", True)
        elif kind == "diuretic":
            new_rate = max(2.0, rate - 2.0)
            if rate <= 4.0: return PumpCommand("STOP", status.drug, 0.0, 0.0, "Auto recovery: volume status improved.", True)
        else:
            new_rate = max(0.0, rate - 10.0)
            if rate <= 10.0: return PumpCommand("STOP", status.drug, 0.0, 0.0, "Auto recovery complete.", True)
        return PumpCommand("SET", status.drug, round(new_rate, 0), 5.0, "Auto recovery: gradual wean while stable.", True)

    def _reduce_oxygen_command(self, status: OxygenStatus) -> OxygenCommand:
        flow = float(status.flow_l_min); fio2 = float(status.fio2)
        new_flow = max(2.0, flow - 1.0); new_fio2 = max(0.28, round(fio2 - 0.04, 2))
        if flow <= 2.1 and fio2 <= 0.29:
            return OxygenCommand("STOP", status.mode, 0.0, 0.21, 0.0, "Auto recovery: oxygen support no longer required.", True)
        return OxygenCommand("SET", "Controlled Wean (SIM)", round(new_flow, 1), new_fio2, 5.0, "Auto recovery: gradual oxygen wean while stable.", True)

    def _maybe_titrate_bp(self, profile: PatientProfile, scenario: str, vitals: Dict[str, float], bp_state: str, ch: AlertChannel, status: Optional[PumpStatus], cmds: Dict[str, Optional[object]], events: List[dict]) -> bool:
        if status is None or not status.running or not status.auto_started:
            return False
        if ch.recovery_watch:
            return False
        ch.last_adjust_sec = max(0.0, ch.last_adjust_sec)
        if ch.last_adjust_sec > 0.0:
            return True
        if bp_state in {"LOW_BP", "SEVERE_HYPOTENSION", "HIGH_BP", "HYPERTENSIVE_CRISIS"}:
            cmd = self.build_bp_command(profile, scenario, bp_state, current_rate=status.rate_mlh)
            if abs(cmd.rate_mlh - status.rate_mlh) >= 1.0 or cmd.drug != status.drug:
                cmds["pump"] = cmd
                ch.last_adjust_sec = self.settings.pump_adjust_sec
                ch.latched = True
                ch.state = "ALARM_LATCHED"
                ch.message = f"{ch.problem} • adaptive support titrated to {cmd.rate_mlh:.0f} mL/h"
                ch.latched_message = ch.message
                events.append({"type": "AUTO", "msg": f"Adaptive BP titration: {cmd.drug} -> {cmd.rate_mlh:.0f} mL/h"})
            return True
        return False

    def _maybe_titrate_spo2(self, profile: PatientProfile, scenario: str, vitals: Dict[str, float], spo2_state: str, ch: AlertChannel, status: Optional[OxygenStatus], cmds: Dict[str, Optional[object]], events: List[dict]) -> bool:
        if status is None or not status.running or not status.auto_started:
            return False
        if ch.recovery_watch:
            return False
        ch.last_adjust_sec = max(0.0, ch.last_adjust_sec)
        if ch.last_adjust_sec > 0.0:
            return True
        if spo2_state in {"LOW_SPO2", "SEVERE_HYPOXEMIA"}:
            cmd = self.build_oxygen_command(profile, scenario, spo2_state, current_flow=status.flow_l_min, current_fio2=status.fio2)
            if abs(cmd.flow_l_min - status.flow_l_min) >= 0.4 or abs(cmd.fio2 - status.fio2) >= 0.02 or cmd.mode != status.mode:
                cmds["oxygen"] = cmd
                ch.last_adjust_sec = self.settings.oxygen_adjust_sec
                ch.latched = True
                ch.state = "ALARM_LATCHED"
                ch.message = f"{ch.problem} • adaptive oxygen titrated to {cmd.flow_l_min:.1f} L/min"
                ch.latched_message = ch.message
                events.append({"type": "AUTO", "msg": f"Adaptive oxygen titration: {cmd.flow_l_min:.1f} L/min, FiO₂ {cmd.fio2:.2f}"})
            return True
        return False

    def _maybe_recover_bp(self, vitals: Dict[str, float], dt: float, ch: AlertChannel, status: Optional[PumpStatus], events: List[dict], cmds: Dict[str, Optional[object]]) -> bool:
        if status is None or not status.running or not status.auto_started:
            return False
        ready = self._recovery_ready_bp(vitals)
        self._update_recovery_clock(ch, ready, dt)
        if not ready:
            ch.latched = True; ch.state = "ALARM_LATCHED"
            ch.problem = ch.latched_problem or ch.problem or "Active hemodynamic alarm"
            ch.message = ch.latched_message or "Hemodynamic support still required."
            return False
        ch.latched = False; ch.pending = False; ch.auto_executed = True; ch.state = "RECOVERY_WATCH"; ch.problem = "Hemodynamic Recovery Watch"
        ch.message = f"Pressure stabilized • observing before auto wean ({ch.stable_for_sec:.1f}s stable)"
        if ch.stable_for_sec < self.settings.recovery_watch_sec or ch.cooldown_sec > 0.0:
            return True
        cmd = self._reduce_pump_command(status)
        cmds["pump"] = cmd
        ch.cooldown_sec = self.settings.pump_wean_step_sec
        if cmd.action == "STOP":
            events.append({"type": "AUTO", "msg": "Auto BP support stopped after sustained recovery."})
            self._clear_channel(ch, f"Monitoring. MAP {self.compute_map(vitals['sbp'], vitals['dbp']):.1f} mmHg")
        else:
            events.append({"type": "AUTO", "msg": f"Auto BP support reduced to {cmd.rate_mlh:.0f} mL/h after recovery."})
            ch.message = f"Hemodynamic recovery watch • support reduced gradually ({ch.stable_for_sec:.1f}s stable)"
        return True

    def _maybe_recover_spo2(self, vitals: Dict[str, float], dt: float, ch: AlertChannel, status: Optional[OxygenStatus], events: List[dict], cmds: Dict[str, Optional[object]]) -> bool:
        if status is None or not status.running or not status.auto_started:
            return False
        ready = self._recovery_ready_spo2(vitals)
        self._update_recovery_clock(ch, ready, dt)
        if not ready:
            ch.latched = True; ch.state = "ALARM_LATCHED"
            ch.problem = ch.latched_problem or ch.problem or "Active oxygenation alarm"
            ch.message = ch.latched_message or "Oxygen support still required."
            return False
        ch.latched = False; ch.pending = False; ch.auto_executed = True; ch.state = "RECOVERY_WATCH"; ch.problem = "Oxygen Recovery Watch"
        ch.message = f"SpO₂ stabilized • observing before auto wean ({ch.stable_for_sec:.1f}s stable)"
        if ch.stable_for_sec < self.settings.recovery_watch_sec or ch.cooldown_sec > 0.0:
            return True
        cmd = self._reduce_oxygen_command(status)
        cmds["oxygen"] = cmd
        ch.cooldown_sec = self.settings.oxygen_wean_step_sec
        if cmd.action == "STOP":
            events.append({"type": "AUTO", "msg": "Auto oxygen support stopped after sustained recovery."})
            self._clear_channel(ch, f"Monitoring. SpO₂ {vitals['spo2']:.0f}%")
        else:
            events.append({"type": "AUTO", "msg": f"Auto oxygen support reduced to {cmd.flow_l_min:.1f} L/min after recovery."})
            ch.message = f"Oxygen recovery watch • support reduced gradually ({ch.stable_for_sec:.1f}s stable)"
        return True

    def step(self, profile: PatientProfile, scenario: str, vitals: Dict[str, float], ack_pressed: bool, auto_armed: bool, approval_required: bool, approve_auto: bool, cancel_auto: bool, dt_sec: float, manual_override: bool = False, pump_status: Optional[PumpStatus] = None, oxygen_status: Optional[OxygenStatus] = None) -> Tuple[List[dict], Dict[str, Optional[object]]]:
        events: List[dict] = []
        cmds: Dict[str, Optional[object]] = {"pump": None, "oxygen": None}
        dt = max(0.0, float(dt_sec))
        map_v = self.compute_map(vitals["sbp"], vitals["dbp"])
        self._append_history("map", map_v)
        self._append_history("spo2", vitals["spo2"])
        self._append_history("hr", vitals.get("hr", 0.0))
        self._append_history("rr", vitals.get("rr", 0.0))
        bp_state = self.classify_bp(vitals["sbp"], vitals["dbp"])
        spo2_state = self.classify_spo2(vitals["spo2"])
        if ack_pressed or cancel_auto:
            for key, ch in self.channels.items():
                if ch.pending or ch.latched:
                    events.append({"type": "ACK", "msg": f"ACK received: {key} alarm cleared."})
                self._clear_channel(ch, "Monitoring.")
            return events, cmds
        if manual_override:
            self._manual_hold()
            return events, cmds
        self._process_bp_channel(profile, scenario, vitals, bp_state, auto_armed, approval_required, approve_auto, dt, events, cmds, pump_status)
        self._process_spo2_channel(profile, scenario, vitals, spo2_state, auto_armed, approval_required, approve_auto, dt, events, cmds, oxygen_status)
        return events, cmds

    def _process_bp_channel(self, profile: PatientProfile, scenario: str, vitals: Dict[str, float], bp_state: str, auto_armed: bool, approval_required: bool, approve_auto: bool, dt: float, events: List[dict], cmds: Dict[str, Optional[object]], pump_status: Optional[PumpStatus] = None) -> None:
        ch = self.channels["bp"]
        risk, confidence, trend_hint = self._bp_risk(vitals, bp_state)
        ch.risk_score = risk; ch.confidence = confidence; ch.trend_hint = trend_hint; ch.dynamic_window = self._dynamic_window(risk, trend_hint)
        if self._maybe_recover_bp(vitals, dt, ch, pump_status, events, cmds):
            return
        if self._maybe_titrate_bp(profile, scenario, vitals, bp_state, ch, pump_status, cmds, events):
            return
        if bp_state == "NORMAL":
            self._clear_channel(ch, f"Monitoring. MAP {self.compute_map(vitals['sbp'], vitals['dbp']):.1f} mmHg")
            return
        if bp_state == "LOW_BP":
            ch.state = bp_state; ch.problem = "Low Blood Pressure"; ch.message = f"Low blood pressure detected. MAP {self.compute_map(vitals['sbp'], vitals['dbp']):.1f} mmHg"
        elif bp_state == "SEVERE_HYPOTENSION":
            ch.state = bp_state; ch.problem = "Severe Hypotension"; ch.message = f"Severe hypotension detected. MAP {self.compute_map(vitals['sbp'], vitals['dbp']):.1f} mmHg"
        elif bp_state == "HIGH_BP":
            ch.state = bp_state; ch.problem = "High Blood Pressure"; ch.message = f"High blood pressure detected: {int(vitals['sbp'])}/{int(vitals['dbp'])}"
        elif bp_state == "HYPERTENSIVE_CRISIS":
            ch.state = bp_state; ch.problem = "Hypertensive Crisis"; ch.message = f"Hypertensive crisis detected: {int(vitals['sbp'])}/{int(vitals['dbp'])}"
        if not auto_armed:
            ch.pending = False; ch.pending_left = 0.0; ch.message += " • auto-rescue disarmed"; return
        if confidence < 2.0:
            ch.pending = False; ch.pending_left = 0.0; ch.message += " • monitoring for confirmation"; return
        if not ch.pending and not ch.auto_executed:
            ch.pending = True; ch.pending_left = ch.dynamic_window
            events.append({"type": "AUTO", "msg": f"BP alarm active: adaptive support in {ch.pending_left:.0f}s unless clinician responds."})
        if ch.pending:
            ch.pending_left = max(0.0, ch.pending_left - dt)
            ch.message = f"{ch.problem} • clinician response window • adaptive support in {ch.pending_left:.1f}s"
            if ch.pending_left <= 0.0:
                if approval_required and not approve_auto:
                    ch.message = "Adaptive support ready, waiting for approval."
                else:
                    cmd = self.build_bp_command(profile, scenario, bp_state, current_rate=0.0)
                    cmds["pump"] = cmd
                    ch.pending = False; ch.pending_left = 0.0; ch.auto_executed = True; ch.latched = True; ch.last_adjust_sec = self.settings.pump_adjust_sec
                    ch.latched_problem = ch.problem; ch.latched_message = f"{ch.problem} • adaptive support running • press ACK to clear alarm"
                    ch.state = "ALARM_LATCHED"; ch.message = ch.latched_message
                    events.append({"type": "AUTO", "msg": f"Adaptive auto BP support started: {cmd.drug}"})

    def _process_spo2_channel(self, profile: PatientProfile, scenario: str, vitals: Dict[str, float], spo2_state: str, auto_armed: bool, approval_required: bool, approve_auto: bool, dt: float, events: List[dict], cmds: Dict[str, Optional[object]], oxygen_status: Optional[OxygenStatus] = None) -> None:
        ch = self.channels["spo2"]
        risk, confidence, trend_hint = self._spo2_risk(vitals, spo2_state)
        ch.risk_score = risk; ch.confidence = confidence; ch.trend_hint = trend_hint; ch.dynamic_window = self._dynamic_window(risk, trend_hint)
        if self._maybe_recover_spo2(vitals, dt, ch, oxygen_status, events, cmds):
            return
        if self._maybe_titrate_spo2(profile, scenario, vitals, spo2_state, ch, oxygen_status, cmds, events):
            return
        if spo2_state == "NORMAL":
            self._clear_channel(ch, f"Monitoring. SpO₂ {vitals['spo2']:.0f}%")
            return
        if spo2_state == "LOW_SPO2":
            ch.state = spo2_state; ch.problem = "Low Oxygen Saturation"; ch.message = f"SpO₂ drop detected: {vitals['spo2']:.0f}%"
        elif spo2_state == "SEVERE_HYPOXEMIA":
            ch.state = spo2_state; ch.problem = "Severe Hypoxemia"; ch.message = f"Severe SpO₂ drop detected: {vitals['spo2']:.0f}%"
        if not auto_armed:
            ch.pending = False; ch.pending_left = 0.0; ch.message += " • auto-rescue disarmed"; return
        if confidence < 2.0:
            ch.pending = False; ch.pending_left = 0.0; ch.message += " • monitoring for confirmation"; return
        if not ch.pending and not ch.auto_executed:
            ch.pending = True; ch.pending_left = ch.dynamic_window
            events.append({"type": "AUTO", "msg": f"SpO₂ alarm active: adaptive oxygen support in {ch.pending_left:.0f}s unless clinician responds."})
        if ch.pending:
            ch.pending_left = max(0.0, ch.pending_left - dt)
            ch.message = f"{ch.problem} • clinician response window • adaptive oxygen in {ch.pending_left:.1f}s"
            if ch.pending_left <= 0.0:
                if approval_required and not approve_auto:
                    ch.message = "Adaptive oxygen support ready, waiting for approval."
                else:
                    cmd = self.build_oxygen_command(profile, scenario, spo2_state, current_flow=0.0, current_fio2=0.21)
                    cmds["oxygen"] = cmd
                    ch.pending = False; ch.pending_left = 0.0; ch.auto_executed = True; ch.latched = True; ch.last_adjust_sec = self.settings.oxygen_adjust_sec
                    ch.latched_problem = ch.problem; ch.latched_message = f"{ch.problem} • adaptive oxygen running • press ACK to clear alarm"
                    ch.state = "ALARM_LATCHED"; ch.message = ch.latched_message
                    events.append({"type": "AUTO", "msg": f"Adaptive auto oxygen support started: {cmd.mode}"})