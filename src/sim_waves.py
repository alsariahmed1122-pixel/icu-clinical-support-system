from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd

def _gauss(x: float, mu: float, sigma: float) -> float:
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)

def synth_ecg(t: float, hr_bpm: float, scenario: str = "", life_state: str = "ALIVE", map_mmHg: float = 80.0) -> float:
    if life_state == "DEAD":
        return 0.0
    if life_state == "ARREST":
        return 0.012 * math.sin(2 * math.pi * t * 0.9)
    hr_bpm = max(18.0, min(220.0, hr_bpm))
    period = 60.0 / hr_bpm
    phase = (t % period) / period
    scenario = scenario or ""
    p_amp, r_amp, t_amp = 0.18, 1.25, 0.35
    q_amp, s_amp = -0.25, -0.35
    q_sigma, r_sigma, s_sigma = 0.010, 0.012, 0.012
    if life_state == "PRE_ARREST":
        r_amp *= 0.55
        t_amp *= 0.40
        q_sigma *= 1.5
        r_sigma *= 1.7
        s_sigma *= 1.6
    if "Shock" in scenario or map_mmHg < 60:
        r_amp *= 0.85
    if "Mild Airway Obstruction" in scenario or "Hypoxemia" in scenario:
        t_amp *= 0.9
    if hr_bpm > 140:
        r_sigma *= 0.85
        t_amp *= 0.85
    p = p_amp * _gauss(phase, 0.18, 0.035)
    q = q_amp * _gauss(phase, 0.36, q_sigma)
    r = r_amp * _gauss(phase, 0.38, r_sigma)
    s = s_amp * _gauss(phase, 0.41, s_sigma)
    tw = t_amp * _gauss(phase, 0.66, 0.060)
    wander = 0.025 * math.sin(2 * math.pi * (t / 6.0))
    if life_state == "PRE_ARREST":
        wander += 0.03 * math.sin(2 * math.pi * t * 3.1)
    noise = 0.01 * math.sin(2 * math.pi * t * 7.0)
    return float(p + q + r + s + tw + wander + noise)

def synth_pleth(t: float, hr_bpm: float, amp: float = 1.0, life_state: str = "ALIVE") -> float:
    if life_state == "DEAD":
        return 0.0
    hr_bpm = max(18.0, min(220.0, hr_bpm))
    period = 60.0 / hr_bpm
    phase = (t % period) / period
    up = _gauss(phase, 0.18, 0.06)
    notch = 0.25 * _gauss(phase, 0.45, 0.05)
    tail = 0.55 * _gauss(phase, 0.62, 0.14)
    base = (up + tail - notch)
    noise = 0.01 * math.sin(2 * math.pi * t * 1.3)
    if life_state == "PRE_ARREST":
        noise += 0.02 * math.sin(2 * math.pi * t * 4.2)
    return float(max(0.0, amp) * (base + noise))

def synth_resp(t: float, rr: float, amp: float = 1.0, scenario: str = "", life_state: str = "ALIVE") -> float:
    if life_state == "DEAD":
        return 0.0
    rr = max(0.0, min(60.0, rr))
    if rr <= 0.0:
        return 0.0
    f = rr / 60.0
    scenario = scenario or ""
    base = math.sin(2 * math.pi * f * t)
    harmonic = 0.25 * math.sin(2 * math.pi * f * 2 * t)
    if "Obstruction" in scenario:
        harmonic += 0.18 * math.sin(2 * math.pi * f * 3 * t)
    if life_state == "PRE_ARREST":
        amp *= 0.45
        harmonic += 0.08 * math.sin(2 * math.pi * f * 4 * t)
    elif life_state == "ARREST":
        amp *= 0.08
        harmonic *= 0.15
    return float(max(0.0, amp) * (0.6 * base + harmonic))

@dataclass
class WaveBuffer:
    sample_hz: int = 60
    max_points: int = 12000
    t: float = 0.0
    rows: List[Dict] = None

    def __post_init__(self):
        if self.rows is None:
            self.rows = []

    def append(self, dt_sec: float, hr: float, rr: float, spo2: float = 98.0, sbp: float = 120.0, dbp: float = 80.0, scenario: str = "", life_state: str = "ALIVE") -> None:
        n = int(max(1, round(self.sample_hz * dt_sec)))
        dt = 1.0 / float(self.sample_hz)
        t0 = self.t
        map_mmHg = (float(sbp) + 2.0 * float(dbp)) / 3.0
        pleth_amp = 0.30 + 0.75 * max(0.0, min(1.0, (map_mmHg - 40.0) / 55.0))
        pleth_amp *= 0.85 + 0.15 * max(0.0, min(1.0, (float(spo2) - 70.0) / 30.0))
        resp_amp = 0.80
        if "Hypoxemia" in scenario or "Pneumonia" in scenario or "Pulmonary Edema" in scenario:
            resp_amp = 1.05
        if life_state == "PRE_ARREST":
            pleth_amp *= 0.35
            resp_amp *= 0.45
        elif life_state == "ARREST":
            pleth_amp *= 0.08
            resp_amp *= 0.08
        if life_state == "DEAD":
            pleth_amp = 0.0
            resp_amp = 0.0
        for i in range(n):
            tt = t0 + i * dt
            self.rows.append({
                "t": tt,
                "ecg": synth_ecg(tt, hr, scenario=scenario, life_state=life_state, map_mmHg=map_mmHg),
                "pleth": synth_pleth(tt, hr, amp=pleth_amp, life_state=life_state),
                "resp": synth_resp(tt, rr, amp=resp_amp, scenario=scenario, life_state=life_state),
            })
        self.t = t0 + n * dt
        if len(self.rows) > self.max_points:
            self.rows = self.rows[-self.max_points:]

    def tail_df(self, seconds: float = 8.0) -> pd.DataFrame:
        need = int(max(2, round(seconds * self.sample_hz)))
        tail = self.rows[-need:] if self.rows else [{"t": 0.0, "ecg": 0.0, "pleth": 0.0, "resp": 0.0}]
        df = pd.DataFrame(tail)
        base = float(df["t"].min())
        df["t"] = df["t"] - base
        return df