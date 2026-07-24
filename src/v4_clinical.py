from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Tuple
import random


@dataclass
class V4State:
    lactate: float = 1.4
    sepsis_risk: str = "LOW"
    escalation: str = "ROUTINE"
    case_status: str = "STABLE"
    rationale: str = "No active advanced clinical concern."
    sensor_fault: str = "NONE"


def clamp(x: float, a: float, b: float) -> float:
    return max(a, min(b, x))


def compute_shock_index(hr: float, sbp: float) -> float:
    if sbp <= 0:
        return 0.0
    return hr / sbp


def compute_news_like(vitals: Dict[str, float]) -> int:
    rr = float(vitals["rr"])
    spo2 = float(vitals["spo2"])
    sbp = float(vitals["sbp"])
    hr = float(vitals["hr"])
    temp = float(vitals["temp"])

    score = 0

    if rr >= 25:
        score += 3
    elif rr >= 21:
        score += 2
    elif rr <= 8:
        score += 3

    if spo2 <= 91:
        score += 3
    elif spo2 <= 93:
        score += 2
    elif spo2 <= 95:
        score += 1

    if sbp <= 90:
        score += 3
    elif sbp <= 100:
        score += 2

    if hr >= 131:
        score += 3
    elif hr >= 111:
        score += 2
    elif hr >= 91:
        score += 1
    elif hr <= 40:
        score += 3

    if temp >= 39.1:
        score += 2
    elif temp <= 35.0:
        score += 3

    return int(score)


def compute_lactate(
    scenario: str,
    hr: float,
    sbp: float,
    spo2: float,
    rr: float,
    prev_lactate: float,
    dt: float,
) -> float:
    dt = max(0.05, float(dt))
    lactate = float(prev_lactate)

    shock_index = compute_shock_index(hr, sbp)

    septic_like = scenario in {
        "Early Sepsis",
        "Septic Shock",
        "Pneumonia / Oxygenation Drop",
    }

    perfusion_stress = 0.0
    if sbp < 90:
        perfusion_stress += 0.08
    if spo2 < 90:
        perfusion_stress += 0.05
    if rr > 24:
        perfusion_stress += 0.03
    if shock_index > 0.9:
        perfusion_stress += 0.06
    if septic_like:
        perfusion_stress += 0.06

    recovery = 0.0
    if sbp >= 100 and spo2 >= 94 and rr <= 22 and shock_index < 0.8:
        recovery = 0.04

    lactate += (perfusion_stress - recovery) * dt
    return round(clamp(lactate, 0.8, 8.0), 2)


def compute_sepsis_risk(scenario: str, temp: float, hr: float, rr: float, sbp: float, lactate: float) -> str:
    points = 0

    if scenario in {"Early Sepsis", "Septic Shock", "Pneumonia / Oxygenation Drop"}:
        points += 2
    if temp >= 38.0 or temp <= 36.0:
        points += 1
    if hr >= 100:
        points += 1
    if rr >= 22:
        points += 1
    if sbp <= 100:
        points += 1
    if lactate >= 2.0:
        points += 2

    if points >= 6:
        return "HIGH"
    if points >= 3:
        return "MODERATE"
    return "LOW"


def compute_escalation(news: int, shock_index: float, lactate: float, any_alarm_latched: bool) -> str:
    if any_alarm_latched or news >= 7 or shock_index >= 1.0 or lactate >= 4.0:
        return "CRITICAL"
    if news >= 5 or shock_index >= 0.9 or lactate >= 2.5:
        return "URGENT"
    if news >= 3:
        return "WATCH"
    return "ROUTINE"


def compute_case_status(any_pending: bool, any_latched: bool, any_running_auto: bool, manual_override: bool) -> str:
    if manual_override:
        return "MANUAL OVERRIDE"
    if any_latched and any_running_auto:
        return "AUTO INTERVENTION"
    if any_pending:
        return "ALARM ACTIVE"
    if any_latched:
        return "ESCALATED"
    return "STABLE"


def compute_rationale(
    scenario: str,
    shock_index: float,
    news: int,
    lactate: float,
    sepsis_risk: str,
    any_pending: bool,
    any_latched: bool,
) -> str:
    reasons: List[str] = []

    if shock_index >= 0.9:
        reasons.append(f"shock index elevated ({shock_index:.2f})")
    if news >= 5:
        reasons.append(f"NEWS-like score elevated ({news})")
    if lactate >= 2.0:
        reasons.append(f"lactate rising ({lactate:.1f} mmol/L)")
    if sepsis_risk in {"MODERATE", "HIGH"}:
        reasons.append(f"sepsis risk {sepsis_risk.lower()}")
    if any_pending:
        reasons.append("response window active")
    if any_latched:
        reasons.append("alarm latched until ACK")

    if not reasons:
        return f"{scenario}: stable advanced assessment."
    return f"{scenario}: " + ", ".join(reasons) + "."


def maybe_sensor_fault(scenario: str) -> str:
    if scenario == "Normal ICU Monitoring":
        if random.random() < 0.01:
            return random.choice([
                "SpO2 Probe Low Signal",
                "BP Cuff Retry Required",
            ])
    else:
        if random.random() < 0.02:
            return random.choice([
                "SpO2 Probe Motion Artifact",
                "BP Cuff Noise",
            ])
    return "NONE"


def apply_sensor_fault_overlay(vitals: Dict[str, float], fault: str) -> Dict[str, float]:
    out = dict(vitals)

    if fault == "SpO2 Probe Low Signal":
        out["spo2"] = max(70.0, out["spo2"] - 3.0)
    elif fault == "SpO2 Probe Motion Artifact":
        out["spo2"] = max(68.0, out["spo2"] - 5.0)
    elif fault == "BP Cuff Retry Required":
        out["sbp"] = out["sbp"] + 4.0
        out["dbp"] = out["dbp"] + 3.0
    elif fault == "BP Cuff Noise":
        out["sbp"] = out["sbp"] + 7.0
        out["dbp"] = out["dbp"] + 5.0

    return out


def update_v4_state(
    prev: V4State,
    scenario: str,
    vitals: Dict[str, float],
    dt: float,
    any_pending: bool,
    any_latched: bool,
    any_running_auto: bool,
    manual_override: bool,
) -> Tuple[V4State, Dict[str, float]]:
    fault = maybe_sensor_fault(scenario)

    sensed = apply_sensor_fault_overlay(vitals, fault)

    shock_index = compute_shock_index(sensed["hr"], sensed["sbp"])
    news = compute_news_like(sensed)
    lactate = compute_lactate(
        scenario=scenario,
        hr=sensed["hr"],
        sbp=sensed["sbp"],
        spo2=sensed["spo2"],
        rr=sensed["rr"],
        prev_lactate=prev.lactate,
        dt=dt,
    )
    sepsis_risk = compute_sepsis_risk(
        scenario=scenario,
        temp=sensed["temp"],
        hr=sensed["hr"],
        rr=sensed["rr"],
        sbp=sensed["sbp"],
        lactate=lactate,
    )
    escalation = compute_escalation(news, shock_index, lactate, any_latched)
    case_status = compute_case_status(any_pending, any_latched, any_running_auto, manual_override)
    rationale = compute_rationale(scenario, shock_index, news, lactate, sepsis_risk, any_pending, any_latched)

    new_state = V4State(
        lactate=lactate,
        sepsis_risk=sepsis_risk,
        escalation=escalation,
        case_status=case_status,
        rationale=rationale,
        sensor_fault=fault,
    )

    metrics = {
        "shock_index": round(shock_index, 2),
        "news_like": news,
    }

    return new_state, metrics


def timeline_add(timeline: List[dict], event: str) -> List[dict]:
    timeline.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
    })
    return timeline[-200:]


def replay_dataframe(timeline: List[dict]):
    try:
        import pandas as pd
        return pd.DataFrame(timeline)
    except Exception:
        return None


def export_v4_snapshot(v4_state: V4State, metrics: Dict[str, float]) -> Dict[str, object]:
    out = asdict(v4_state)
    out.update(metrics)
    return out