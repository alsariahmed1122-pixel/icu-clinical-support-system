from __future__ import annotations
import time
import math
from datetime import datetime
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from ui_style import CSS, MANUFACTURER
from ui_components import pill_choice, drip_css
from sim_vitals import VitalsSim, SimProfile
from sim_waves import WaveBuffer
from engine import (
    ICUSettings,
    PatientProfile,
    ClinicalSupportEngine,
    InfusionPumpSim,
    OxygenControllerSim,
    PumpCommand,
    OxygenCommand,
)
import base64
import io
import struct
import wave

APP_VERSION = "v5.0 Professional Simulation"

# Removed trailing spaces from scenario names to avoid logic bugs
SCENARIO_GROUPS = {
    "IV Pump Scenarios": [
        "Severe Dehydration",
        "Hypovolemic Shock",
        "Septic Shock",
        "Hemodynamic Instability",
    ],
    "Oxygen Scenarios": [
        "Acute Hypoxemia",
        "Pneumonia / Oxygenation Drop",
        "Pulmonary Edema",
        "Respiratory Failure",
    ],
}

# Moved DEVICE_VISUAL_UPGRADE_CSS here (before init_app) so it's defined when used
DEVICE_VISUAL_UPGRADE_CSS = """
<style>
.iv-assembly{position:relative;margin-top:16px;height:168px;border-radius:22px;border:1px solid rgba(145,230,255,.14);background:linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.015));overflow:hidden;}
.iv-rail{position:absolute;left:20px;top:8px;width:2px;height:132px;background:linear-gradient(180deg, rgba(255,255,255,.55), rgba(255,255,255,.08));box-shadow:0 0 14px rgba(255,255,255,.12);}
.iv-hook{position:absolute;left:9px;top:4px;width:24px;height:14px;border:2px solid rgba(225,247,255,.82);border-bottom:none;border-radius:16px 16px 0 0;}
.iv-bag{position:absolute;left:38px;top:14px;width:94px;height:118px;border-radius:20px 20px 16px 16px;background:linear-gradient(180deg, rgba(227,248,255,.92), rgba(181,224,242,.92));border:1px solid rgba(255,255,255,.5);box-shadow:inset 0 2px 0 rgba(255,255,255,.7), inset 0 -14px 22px rgba(56,130,170,.12), 0 16px 28px rgba(0,0,0,.16);overflow:hidden;}
.iv-bag:before{content:"";position:absolute;left:50%;top:-11px;transform:translateX(-50%);width:26px;height:18px;border-radius:0 0 12px 12px;background:linear-gradient(180deg,#dff8ff,#9dd6ea);border:1px solid rgba(255,255,255,.55);}
.iv-bag:after{content:"";position:absolute;left:50%;bottom:-10px;transform:translateX(-50%);width:16px;height:16px;border-radius:999px;background:#b5ecff;box-shadow:0 0 0 3px rgba(181,236,255,.1);}
.iv-bag-shine{position:absolute;inset:0;background:linear-gradient(105deg, rgba(255,255,255,.78) 0%, rgba(255,255,255,.08) 26%, transparent 44%);pointer-events:none;}
.iv-bag-fill{position:absolute;left:8px;right:8px;bottom:8px;border-radius:14px 14px 12px 12px;background:linear-gradient(180deg, rgba(118,255,171,.96), rgba(35,197,154,.92));box-shadow:inset 0 1px 0 rgba(255,255,255,.35), 0 0 22px rgba(118,255,171,.22);overflow:hidden;}
.iv-bag-fill:before{content:"";position:absolute;inset:0;background:linear-gradient(90deg, transparent 0%, rgba(255,255,255,.24) 50%, transparent 100%);animation:shimmerMove 2.8s linear infinite;}
.iv-mark{position:absolute;right:10px;top:18px;bottom:18px;width:14px;display:flex;flex-direction:column;justify-content:space-between;opacity:.42;}
.iv-mark span{display:block;height:2px;border-radius:999px;background:rgba(20,87,115,.46);}
.drip-chamber{position:absolute;left:124px;top:104px;width:22px;height:40px;border-radius:12px;background:linear-gradient(180deg, rgba(231,248,255,.9), rgba(177,220,238,.84));border:1px solid rgba(255,255,255,.42);box-shadow:inset 0 1px 0 rgba(255,255,255,.62), inset 0 -8px 16px rgba(50,118,155,.12);overflow:hidden;}
.drip-liquid{position:absolute;left:4px;right:4px;bottom:4px;height:44%;border-radius:8px;background:linear-gradient(180deg, rgba(118,255,171,.95), rgba(37,196,155,.9));}
.drip-drop{position:absolute;left:50%;top:6px;transform:translateX(-50%);width:8px;height:12px;border-radius:60% 60% 70% 70%;background:linear-gradient(180deg, rgba(168,250,255,1), rgba(91,226,255,.82));animation:ivDrop 1.4s infinite ease-in;}
.iv-tube-main{position:absolute;left:82px;top:132px;width:3px;height:28px;background:rgba(182,234,250,.92);}
.iv-tube-run{position:absolute;left:137px;top:141px;width:58%;height:16px;border-bottom:4px solid rgba(193,240,255,.82);border-radius:0 0 24px 24px;}
.iv-tube-run:before{content:"";position:absolute;left:0;top:10px;width:100%;height:4px;border-radius:999px;background:linear-gradient(90deg, rgba(118,255,171,0) 0%, rgba(118,255,171,.95) 22%, rgba(193,255,227,.95) 50%, rgba(118,255,171,.95) 78%, rgba(118,255,171,0) 100%);animation:flowTube 1.35s linear infinite;}
.iv-pump-face{position:absolute;right:20px;bottom:20px;width:128px;height:86px;border-radius:18px;background:linear-gradient(180deg, rgba(241,249,255,.98), rgba(192,216,230,.92));border:1px solid rgba(255,255,255,.46);box-shadow:0 14px 24px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.72), inset 0 -10px 14px rgba(88,148,180,.12);}
.iv-pump-face:before{content:"";position:absolute;left:12px;right:12px;top:10px;height:28px;border-radius:10px;background:linear-gradient(180deg,#07131e,#05101a);border:1px solid rgba(105,224,255,.18);box-shadow:inset 0 0 18px rgba(103,239,255,.08);}
.iv-pump-face:after{content:"";position:absolute;left:14px;bottom:14px;width:54px;height:18px;border-radius:999px;background:linear-gradient(90deg,#d8effa,#b1d3e7);box-shadow:60px 0 0 0 rgba(177,211,231,.9);}
.iv-pump-led{position:absolute;right:14px;top:16px;width:10px;height:10px;border-radius:999px;background:#7dff93;box-shadow:0 0 15px rgba(125,255,147,.62);}
.oxy-assembly{position:relative;margin-top:16px;height:168px;border-radius:22px;border:1px solid rgba(145,230,255,.14);background:linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.015));overflow:hidden;}
.oxy-cylinder{position:absolute;left:18px;bottom:16px;width:84px;height:134px;border-radius:30px 30px 18px 18px;background:linear-gradient(180deg, #9be9ff 0%, #4dbde8 36%, #1490c7 100%);box-shadow:inset 0 2px 0 rgba(255,255,255,.55), inset -12px 0 18px rgba(0,0,0,.12), 0 18px 30px rgba(0,0,0,.18);}
.oxy-cylinder:before{content:"";position:absolute;left:22px;top:-18px;width:40px;height:24px;border-radius:12px 12px 6px 6px;background:linear-gradient(180deg,#dff5ff,#9acfe2);border:1px solid rgba(255,255,255,.46);}
.oxy-cylinder:after{content:"";position:absolute;left:12px;right:12px;top:18px;height:16px;border-radius:999px;background:rgba(255,255,255,.22);}
.oxy-regulator{position:absolute;left:86px;top:34px;width:44px;height:44px;border-radius:50%;background:linear-gradient(180deg,#eef8ff,#b5d3e4);border:1px solid rgba(255,255,255,.5);box-shadow:0 8px 14px rgba(0,0,0,.16);}
.oxy-regulator:before{content:"";position:absolute;inset:8px;border-radius:50%;background:radial-gradient(circle at 50% 50%, #ffffff 0%, #eaf6fc 55%, #b8d8ea 100%);}
.oxy-regulator:after{content:"";position:absolute;left:50%;top:8px;width:2px;height:12px;background:#1a678f;transform:translateX(-50%) rotate(35deg);transform-origin:bottom center;}
.flowmeter{position:absolute;left:138px;top:26px;width:36px;height:92px;border-radius:18px;background:linear-gradient(180deg, rgba(234,249,255,.92), rgba(175,219,236,.86));border:1px solid rgba(255,255,255,.44);overflow:hidden;box-shadow:inset 0 1px 0 rgba(255,255,255,.62), 0 8px 16px rgba(0,0,0,.12);}
.flowmeter-fill{position:absolute;left:7px;right:7px;bottom:7px;border-radius:12px;background:linear-gradient(180deg, rgba(102,223,255,.98), rgba(27,160,214,.86));}
.flowmeter-bubble{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.92);animation:oxyBubble 1.6s infinite ease-in;}
.oxy-patient-line{position:absolute;left:172px;top:72px;width:50%;height:48px;border-top:4px solid rgba(193,240,255,.86);border-right:4px solid rgba(193,240,255,.86);border-radius:0 24px 24px 0;}
.oxy-patient-line:before{content:"";position:absolute;left:0;top:-4px;width:100%;height:4px;border-radius:999px;background:linear-gradient(90deg, rgba(102,223,255,0) 0%, rgba(102,223,255,.96) 25%, rgba(255,255,255,.24) 50%, rgba(102,223,255,.96) 75%, rgba(102,223,255,0) 100%);animation:flowTube 1.6s linear infinite;}
.oxy-nasal{position:absolute;right:18px;top:80px;width:74px;height:44px;border:4px solid rgba(193,240,255,.78);border-left:none;border-radius:0 24px 24px 0;opacity:.84;}
.oxy-nasal:before,.oxy-nasal:after{content:"";position:absolute;width:14px;height:14px;border-radius:50%;background:rgba(193,240,255,.78);top:14px;}
.oxy-nasal:before{left:-9px;}
.oxy-nasal:after{left:10px;}
.oxy-pulse{position:absolute;right:26px;bottom:18px;display:flex;gap:8px;align-items:flex-end;height:40px;}
.oxy-pulse span{display:block;width:10px;border-radius:999px;background:linear-gradient(180deg, rgba(102,223,255,.95), rgba(38,167,214,.8));animation:oxyPulse 1.2s ease-in-out infinite;}
.oxy-pulse span:nth-child(1){height:16px;animation-delay:0s;}
.oxy-pulse span:nth-child(2){height:30px;animation-delay:.14s;}
.oxy-pulse span:nth-child(3){height:22px;animation-delay:.28s;}
.oxy-pulse span:nth-child(4){height:36px;animation-delay:.42s;}
.oxy-pulse span:nth-child(5){height:18px;animation-delay:.56s;}
@keyframes ivDrop{0%{transform:translateX(-50%) translateY(0);opacity:.1;}25%{opacity:1;}100%{transform:translateX(-50%) translateY(18px);opacity:.15;}}
@keyframes flowTube{0%{transform:translateX(-120%);}100%{transform:translateX(120%);}}
@keyframes oxyBubble{0%{transform:translateX(-50%) translateY(0) scale(.65);opacity:.25;}40%{opacity:.95;}100%{transform:translateX(-50%) translateY(-54px) scale(1);opacity:.12;}}
@keyframes oxyPulse{0%,100%{transform:scaleY(.55);opacity:.35;}50%{transform:scaleY(1);opacity:1;}}
</style>
"""

# Fixed all broken CSS spaces (f ont-weight -> font-weight, etc.)
CLEAR_UI = """
<style>

/* ===== GENERAL LABELS ===== */
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stToggle"] label,
[data-testid="stCheckbox"] label,
label {
color: #eaf4ff !important;
font-weight: 900 !important;
letter-spacing: .35px !important;
}

/* ===== CLOSED SELECT BOX ===== */
div[data-baseweb="select"] > div {
background: #0b1328 !important;
border: 1px solid rgba(68,215,255,.52) !important;
border-radius: 14px !important;
min-height: 48px !important;
color: #ffffff !important;
font-weight: 800 !important;
box-shadow: 0 0 0 1px rgba(0,0,0,.10), 0 8px 24px rgba(0,0,0,.24) !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input,
div[data-baseweb="select"] div {
color: #ffffff !important;
font-weight: 800 !important;
opacity: 1 !important;
text-shadow: none !important;
}

div[data-baseweb="select"] svg {
fill: #44d7ff !important;
color: #44d7ff !important;
}

/* ===== DROPDOWN POPUP ===== */
div[data-baseweb="popover"] {
z-index: 999999 !important;
opacity: 1 !important;
}
div[data-baseweb="popover"] * {
opacity: 1 !important;
}

/* ===== DROPDOWN MENU PANEL ===== */
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
div[role="listbox"],
ul[role="listbox"] {
background: #f7f9fc !important;
border: 1px solid #c9d4e5 !important;
border-radius: 12px !important;
box-shadow: 0 16px 36px rgba(0,0,0,.45) !important;
overflow: hidden !important;
}

/* ===== MENU OPTIONS ===== */
div[role="option"],
li[role="option"],
div[data-baseweb="menu"] ul li,
div[data-baseweb="menu"] div[role="option"] {
background: #f7f9fc !important;
color: #0b1328 !important;
font-weight: 800 !important;
opacity: 1 !important;
text-shadow: none !important;
border: none !important;
}

div[role="option"] *,
li[role="option"] *,
div[data-baseweb="menu"] *,
div[data-baseweb="menu"] span,
div[data-baseweb="menu"] p,
div[data-baseweb="menu"] div,
div[role="listbox"] div,
div[role="listbox"] span {
color: #0b1328 !important;
opacity: 1 !important;
text-shadow: none !important;
fill: #0b1328 !important;
}

div[role="option"]:hover,
li[role="option"]:hover,
div[data-baseweb="menu"] ul li:hover {
background: #d9ecff !important;
color: #08111f !important;
}

div[role="option"]:hover *,
li[role="option"]:hover *,
div[data-baseweb="menu"] ul li:hover * {
color: #08111f !important;
}

div[role="option"][aria-selected="true"],
li[role="option"][aria-selected="true"] {
background: #bfe6ff !important;
color: #06111d !important;
}

div[role="option"][aria-selected="true"] *,
li[role="option"][aria-selected="true"] * {
color: #06111d !important;
}

/* ===== SLIDERS ===== */
[data-testid="stSlider"] p,
[data-testid="stSlider"] span,
[data-testid="stSlider"] div {
color: #f8fbff !important;
font-weight: 700 !important;
}

[data-testid="stSlider"] div[role="slider"] {
background: #ff5252 !important;
border: 2px solid #ffffff !important;
box-shadow: 0 0 10px rgba(255,82,82,.45) !important;
}

/* ===== BUTTONS ===== */
div.stButton > button,
[data-testid="stButton"] button {
width: 100% !important;
border-radius: 16px !important;
border: 1px solid rgba(68,215,255,.36) !important;
background: linear-gradient(180deg, #132344, #0a1326) !important;
color: #f7fbff !important;
font-weight: 1000 !important;
letter-spacing: .4px !important;
min-height: 48px !important;
box-shadow: 0 8px 22px rgba(0,0,0,.22) !important;
}

div.stButton > button:hover,
[data-testid="stButton"] button:hover {
border: 1px solid rgba(68,215,255,.78) !important;
box-shadow: 0 0 0 1px rgba(68,215,255,.16), 0 8px 24px rgba(0,0,0,.28) !important;
}

/* ===== TEXT / NUMBER INPUTS ===== */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
input {
background: #0b1328 !important;
color: #ffffff !important;
border: 1px solid rgba(68,215,255,.40) !important;
border-radius: 10px !important;
}

/* ===== BOOT ===== */
.boot-wrap {
margin-top: 80px;
text-align: center;
}
.boot-title {
font-size: 30px;
font-weight: 1000;
color: #00e5ff;
letter-spacing: 1px;
text-shadow: 0 0 20px rgba(0,229,255,.18);
}
.boot-sub {
margin-top: 12px;
color: #bceeff;
font-size: 15px;
}

/* ===== BANNER ===== */
.device-banner {
display:flex;
justify-content:space-between;
align-items:center;
gap:12px;
background:linear-gradient(180deg,#101a33,#0a1122);
border:1px solid rgba(68,215,255,.18);
border-radius:16px;
padding:10px 14px;
margin-bottom:10px;
}
.device-banner .left {
color:#f4fbff;
font-weight:900;
}
.device-banner .right {
color:#9ccfe4;
font-size:13px;
text-align:right;
}

/* ===== RISK ===== */
.risk-bar {
margin-top:10px;
border-radius:14px;
padding:12px 14px;
font-weight:1000;
text-align:center;
font-size:14px;
letter-spacing:.6px;
background:#09111d;
}

/* ===== ALARM ===== */
.alarm-strip {
margin-top: 10px;
border: 1px solid rgba(255, 64, 64, 0.52);
background: linear-gradient(180deg, rgba(78,8,12,0.86), rgba(28,6,10,0.76));
border-radius: 18px;
padding: 14px 16px;
display: flex;
align-items: center;
justify-content: space-between;
gap: 16px;
}
.alarm-title {
color: #ff9d9d;
font-weight: 1000;
letter-spacing: 1px;
font-size: 12px;
text-transform: uppercase;
}
.alarm-problem {
color: #ffffff;
font-weight: 1000;
font-size: 22px;
line-height: 1.1;
}
.alarm-msg {
color: #ffe7e7;
font-weight: 800;
font-size: 13px;
margin-top: 6px;
}
.timer-box {
flex: 0 0 auto;
min-width: 160px;
text-align: center;
border: 1px solid rgba(0,255,255,0.25);
background: rgba(0,0,0,0.40);
border-radius: 16px;
padding: 12px 10px;
}
.timer-label {
color: #96f7ff;
font-size: 11px;
font-weight: 900;
letter-spacing: 1px;
text-transform: uppercase;
}
.timer-digi {
margin-top: 5px;
font-family: ui-monospace, Consolas, monospace;
font-size: 42px;
font-weight: 1000;
line-height: 1;
color: #00f5ff;
text-shadow: 0 0 8px rgba(0,245,255,0.40), 0 0 18px rgba(0,245,255,0.28);
}
.timer-red {
color: #ff5d73 !important;
text-shadow: 0 0 8px rgba(255,93,115,0.40), 0 0 18px rgba(255,93,115,0.28) !important;
}
.badge-auto,
.badge-latched,
.badge-highbp {
display:inline-block;
margin-top:8px;
padding:4px 8px;
border-radius:999px;
font-size:11px;
font-weight:900;
letter-spacing:.6px;
}
.badge-auto {
background:rgba(255,255,255,0.08);
color:#ffd7d7;
}
.badge-latched {
margin-left:8px;
background:rgba(255,93,115,0.16);
color:#ffd8df;
border:1px solid rgba(255,93,115,0.28);
}
.badge-highbp {
margin-left:8px;
background:rgba(255,196,0,0.14);
color:#ffe9a6;
border:1px solid rgba(255,196,0,0.24);
}

/* ===== SUMMARY ===== */
.summary-card {
background:linear-gradient(180deg,#10192d,#0a1120);
border:1px solid rgba(68,215,255,.14);
border-radius:16px;
padding:14px 16px;
color:#eef9ff;
margin-bottom:10px;
}
.summary-title {
color:#96f7ff;
font-weight:1000;
font-size:13px;
letter-spacing:.8px;
text-transform:uppercase;
margin-bottom:8px;
}
.summary-grid {
display:grid;
grid-template-columns:1fr 1fr;
gap:8px 14px;
font-size:13px;
}
.summary-grid div span {
color:#98b7c9;
}

/* ===== COMPACT ACTION BAR ===== */
.compact-action-bar{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px;}
.compact-action-bar .action-chip{padding:12px 14px;border-radius:16px;border:1px solid rgba(68,215,255,.18);background:linear-gradient(180deg,#101a33,#0a1122);color:#effbff;font-weight:900;text-align:center;font-size:13px;}
.alarm-row {display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}
.control-screen{background:linear-gradient(180deg,#09111d,#07101a);border:1px solid rgba(94,224,255,.14);border-radius:18px;padding:14px;box-shadow:inset 0 1px 0 rgba(255,255,255,.05);}
.control-title{color:#9eefff;font-size:12px;font-weight:1000;letter-spacing:.8px;text-transform:uppercase;margin-bottom:10px;}
.control-foot{color:#9cb8c8;font-size:12px;margin-top:8px;}

/* ===== FINAL CLINICAL POLISH ===== */
.scenario-mini-title{color:#9eefff;font-weight:1000;font-size:12px;letter-spacing:.8px;text-transform:uppercase;margin:8px 0 6px;}
.scenario-note{color:#aac7d6;font-size:12px;margin-top:8px;line-height:1.45;}
.clinical-response-panel{margin-top:12px;margin-bottom:12px;border-radius:18px;border:1px solid rgba(94,224,255,.26);background:linear-gradient(180deg,rgba(10,23,42,.96),rgba(5,13,26,.96));box-shadow:inset 0 1px 0 rgba(255,255,255,.05),0 12px 26px rgba(0,0,0,.20);padding:14px 16px;color:#eefbff;}
.crp-head{display:flex;justify-content:space-between;align-items:center;gap:12px;border-bottom:1px solid rgba(255,255,255,.08);padding-bottom:9px;margin-bottom:10px;}
.crp-title{color:#9eefff;font-size:12px;font-weight:1000;letter-spacing:.9px;text-transform:uppercase;}
.crp-status{font-size:12px;font-weight:1000;border-radius:999px;padding:5px 10px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);}
.crp-grid{display:grid;grid-template-columns:1.2fr .9fr;gap:10px 16px;align-items:start;}
.crp-main{font-size:18px;font-weight:1000;color:#fff;line-height:1.25;}
.crp-msg{font-size:13px;color:#d7edf7;margin-top:7px;line-height:1.45;}
.crp-meta{font-size:13px;line-height:1.75;color:#dff7ff;}
.crp-meta span{color:#91b4c8;font-weight:800;}
.crp-monitoring{border-color:rgba(34,255,85,.30)}
.crp-warning{border-color:rgba(255,216,77,.45)}
.crp-auto{border-color:rgba(255,154,60,.55)}
.crp-critical{border-color:rgba(255,77,77,.62)}
.crp-ack{border-color:rgba(74,255,169,.50)}
div[data-testid="stExpander"]{border:1px solid rgba(68,215,255,.20)!important;border-radius:16px!important;background:linear-gradient(180deg,#0d172d,#071022)!important;overflow:hidden!important;margin-bottom:8px!important;}
div[data-testid="stExpander"] summary{color:#eaf9ff!important;font-weight:1000!important;}
div[data-testid="stExpander"] div{color:#eaf9ff!important;}
</style>
"""


def now_hhmm() -> str:
    return datetime.now().strftime("%H:%M")


def _encode_wav(samples, sample_rate: int = 22050) -> str:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = [struct.pack("<h", max(-32767, min(32767, int(s)))) for s in samples]
        wf.writeframes(b"".join(frames))
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _seq_wav_base64(events, total_dur: float, sample_rate: int = 22050) -> str:
    total_n = max(1, int(sample_rate * total_dur))
    samples = [0.0] * total_n
    for ev in events:
        start = int(sample_rate * max(0.0, ev.get("start", 0.0)))
        dur = max(0.01, float(ev.get("dur", 0.08)))
        amp = max(0.0, min(1.0, float(ev.get("amp", 0.35))))
        freq = max(40.0, float(ev.get("freq", 800.0)))
        n = min(total_n - start, int(sample_rate * dur))
        if n <= 0:
            continue
        attack = max(1, int(sample_rate * 0.004))
        release = max(1, int(sample_rate * 0.012))
        second_freq = float(ev.get("freq2", 0.0) or 0.0)
        for i in range(n):
            idx = start + i
            t = i / sample_rate
            env_in = min(1.0, i / attack)
            env_out = min(1.0, (n - i) / release)
            env = env_in * env_out
            s = math.sin(2 * math.pi * freq * t)
            if second_freq > 0.0:
                s = 0.62 * s + 0.38 * math.sin(2 * math.pi * second_freq * t)
            samples[idx] += 32767.0 * amp * env * s
    return _encode_wav(samples, sample_rate=sample_rate)


def _monitor_wav_base64(hr: float, spo2: float, total_dur: float = 2.8, sample_rate: int = 22050) -> str:
    hr = max(35.0, min(160.0, float(hr)))
    spo2 = max(50.0, min(100.0, float(spo2)))
    beat_period = 60.0 / hr
    pitch = 780.0 + (spo2 - 85.0) * 13.5
    events = []
    t = 0.0
    while t < total_dur:
        events.append({"start": t, "dur": 0.030, "freq": pitch + 180.0, "freq2": pitch + 60.0, "amp": 0.22})
        events.append({"start": t + 0.045, "dur": 0.045, "freq": pitch, "amp": 0.16})
        t += beat_period
    return _seq_wav_base64(events, total_dur=total_dur, sample_rate=sample_rate)


def _alert_wav_base64(total_dur: float = 2.2, sample_rate: int = 22050) -> str:
    events = [
        {"start": 0.00, "dur": 0.11, "freq": 1220, "freq2": 980, "amp": 0.34},
        {"start": 0.19, "dur": 0.11, "freq": 1220, "freq2": 980, "amp": 0.34},
        {"start": 1.15, "dur": 0.11, "freq": 1220, "freq2": 980, "amp": 0.34},
        {"start": 1.34, "dur": 0.11, "freq": 1220, "freq2": 980, "amp": 0.34},
    ]
    return _seq_wav_base64(events, total_dur=total_dur, sample_rate=sample_rate)


def _critical_wav_base64(total_dur: float = 1.8, sample_rate: int = 22050) -> str:
    events = [
        {"start": 0.00, "dur": 0.14, "freq": 1560, "freq2": 1180, "amp": 0.42},
        {"start": 0.20, "dur": 0.14, "freq": 980, "freq2": 760, "amp": 0.42},
        {"start": 0.72, "dur": 0.14, "freq": 1560, "freq2": 1180, "amp": 0.42},
        {"start": 0.92, "dur": 0.14, "freq": 980, "freq2": 760, "amp": 0.42},
    ]
    return _seq_wav_base64(events, total_dur=total_dur, sample_rate=sample_rate)


def _death_wav_base64(total_dur: float = 2.0, sample_rate: int = 22050) -> str:
    total_n = max(1, int(sample_rate * total_dur))
    samples = []
    freq = 1040.0
    for i in range(total_n):
        t = i / sample_rate
        env = min(1.0, i / max(1, int(sample_rate * 0.02)))
        env *= 0.96 + 0.04 * math.sin(2 * math.pi * 0.8 * t)
        s = 0.88 * math.sin(2 * math.pi * freq * t) + 0.12 * math.sin(2 * math.pi * (freq * 2.0) * t)
        samples.append(32767.0 * 0.18 * env * s)
    return _encode_wav(samples, sample_rate=sample_rate)


def render_audio_alarm(mode: str, hr: float = 80.0, spo2: float = 98.0) -> None:
    presets = {
        "monitor": _monitor_wav_base64(hr=hr, spo2=spo2),
        "alert": _alert_wav_base64(),
        "critical": _critical_wav_base64(),
        "death": _death_wav_base64(),
    }
    b64 = presets.get(mode)
    if not b64:
        return
    st.markdown(
        f"""
<audio autoplay loop style="display:none">
<source src="data:audio/wav;base64,{b64}" type="audio/wav">
</audio>
""",
        unsafe_allow_html=True,
    )


def render_doctor_call_strip(title: str, message: str) -> None:
    st.markdown(
        f"""
<div class="alarm-strip" style="border-color:rgba(255,96,96,.72); background:linear-gradient(180deg, rgba(64,10,16,.86), rgba(20,6,10,.78));">
<div class="alarm-left">
<div class="alarm-title">{title}</div>
<div class="alarm-problem">CALL PHYSICIAN NOW</div>
<div class="alarm-msg" style="font-size:14px;">{message}</div>
<div class="badge-auto" style="background:rgba(255,255,255,.10);">Dr. Ahmed Mohamed Aljak</div>
<span class="badge-latched" style="font-size:14px;padding:6px 10px;">0903600668</span>
</div>
<div class="timer-box" style="min-width:220px;">
<div class="timer-label">Emergency Contact</div>
<div class="timer-digi timer-red" style="font-size:34px;">0903600668</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _alt_wave(df: pd.DataFrame, y: str, color: str, height: int = 90) -> alt.Chart:
    if df.empty:
        df = pd.DataFrame({"t": [0.0], y: [0.0]})
    d = df[["t", y]].copy()
    d["t"] = pd.to_numeric(d["t"], errors="coerce")
    d[y] = pd.to_numeric(d[y], errors="coerce")
    d = d.dropna()
    base = pd.Timestamp.now()
    d["T"] = [base + pd.Timedelta(seconds=float(x)) for x in d["t"].tolist()]
    ch = (
        alt.Chart(d)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("T:T", title=None, axis=alt.Axis(labels=False, ticks=False, grid=False)),
            y=alt.Y(f"{y}:Q", title=None, axis=alt.Axis(labels=False, ticks=False, grid=False)),
        )
        .properties(height=height)
        .configure_view(strokeOpacity=0)
        .configure(background="rgba(0,0,0,0)")
    )
    return ch.encode(color=alt.value(color))


def boot_screen():
    if "boot_done" not in st.session_state:
        st.session_state.boot_done = False
    if not st.session_state.boot_done:
        st.markdown(CLEAR_UI, unsafe_allow_html=True)
        st.markdown(
            """
<div class="boot-panel">
<div class="boot-chip">ADVANCED ICU PLATFORM</div>
<div class="boot-wrap">
<div class="boot-title">ICU INTELLIGENT CLINICAL SUPPORT SYSTEM</div>
<div class="boot-sub">Boot sequence • Sensor check • Controller check • Alarm bus check</div>
<div class="boot-line"></div>
</div>
</div>
""",
            unsafe_allow_html=True,
        )
        progress = st.progress(0)
        status = st.empty()
        steps = [
            "Initializing UI engine",
            "Checking waveform buffers",
            "Checking infusion pump",
            "Checking oxygen controller",
            "Loading clinical logic",
            "Final integrity check",
        ]
        for i, step in enumerate(steps, start=1):
            status.info(step)
            for p in range((i - 1) * 16, i * 16):
                progress.progress(min(p + 1, 100))
            time.sleep(0.08)
        progress.progress(100)
        st.markdown('<div class="boot-ready">Clinical system synchronized • Ready for simulation</div>', unsafe_allow_html=True)
        status.success("System ready.")
        time.sleep(0.25)
        st.session_state.boot_done = True
        st.rerun()


def init_app():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(CLEAR_UI, unsafe_allow_html=True)
    st.markdown(DEVICE_VISUAL_UPGRADE_CSS, unsafe_allow_html=True)
    if "sim" not in st.session_state:
        st.session_state.sim = VitalsSim()
    if "waves" not in st.session_state:
        st.session_state.waves = WaveBuffer(sample_hz=60)
    if "engine" not in st.session_state:
        st.session_state.engine = ClinicalSupportEngine(ICUSettings())
    if "pump" not in st.session_state:
        st.session_state.pump = InfusionPumpSim(max_flow_mlh=ICUSettings().max_flow_mlh)
    if "oxygen_dev" not in st.session_state:
        st.session_state.oxygen_dev = OxygenControllerSim()
    if "running" not in st.session_state:
        st.session_state.running = False
    if "tick" not in st.session_state:
        st.session_state.tick = 1.0
    if "scenario_group" not in st.session_state:
        st.session_state.scenario_group = "IV Pump Scenarios"
    if "scenario" not in st.session_state:
        st.session_state.scenario = "Normal ICU Monitoring"
    if "active_scenario_snapshot" not in st.session_state:
        st.session_state.active_scenario_snapshot = st.session_state.scenario
    if "patients" not in st.session_state:
        st.session_state.patients = {
            "Current Case": PatientProfile(patient_id="Current Case", sex="M", age=51, weight_kg=74.0),
        }
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = "Current Case"
    if "auto_armed" not in st.session_state:
        st.session_state.auto_armed = True
    if "approval_required" not in st.session_state:
        st.session_state.approval_required = False
    if "manual_override" not in st.session_state:
        st.session_state.manual_override = False
    if "ack_pressed" not in st.session_state:
        st.session_state.ack_pressed = False


def current_profile() -> PatientProfile:
    return st.session_state.patients["Current Case"]


def support_display(name: str) -> str:
    text = (name or " ").lower()
    if any(k in text for k in ["ringer", "saline", "crystalloid", "plasma"]):
        return "Simulated Fluid Support"
    if any(k in text for k in ["norad", "dopamine", "vasopressor"]):
        return "Simulated Vasopressor Support"
    if any(k in text for k in ["furosemide", "diuretic", "fluid-overload"]):
        return "Simulated Fluid-Overload Support"
    if any(k in text for k in ["labetalol", "hydralazine", "bp control"]):
        return "Simulated BP Control Support"
    if any(k in text for k in ["o2", "oxygen", "high o2"]):
        return "Simulated Oxygen Support"
    if not name or name == "Monitoring":
        return "Monitoring Only"
    return name


def recommended_therapy(scenario: str) -> str:
    mapping = {
        "Severe Dehydration": "Simulated Fluid Support",
        "Hypovolemic Shock": "Simulated Fluid Support",
        "Septic Shock": "Simulated Vasopressor Support",
        "Hemodynamic Instability": "Simulated Vasopressor Support",
        "Acute Hypoxemia": "Simulated Oxygen Support",
        "Pneumonia / Oxygenation Drop": "Simulated Oxygen Support",
        "Pulmonary Edema": "Simulated Oxygen Support + Fluid-Overload Support",
        "Respiratory Failure": "Simulated Oxygen Support",
        "Normal ICU Monitoring": "Monitoring Only",
    }
    return mapping.get(scenario, support_display(scenario))


def compute_risk(v) -> tuple[str, str]:
    score = 0
    if v.hr > 120 or v.hr < 45:
        score += 2
    if v.spo2 < 90:
        score += 3
    if v.sbp < 90:
        score += 3
    if v.sbp > 180:
        score += 2
    if v.rr > 30 or v.rr < 8:
        score += 2
    if score <= 2:
        return "STABLE", "#22ff55"
    if score <= 5:
        return "MODERATE RISK", "#ffd84d"
    if score <= 7:
        return "HIGH RISK", "#ff9a3c"
    return "CRITICAL", "#ff4d4d"


def ack_stop_auto_devices():
    pump = st.session_state.pump
    oxygen_dev = st.session_state.oxygen_dev
    ps = pump.get_status()
    if ps.running and ps.auto_started:
        pump.apply(PumpCommand("STOP", ps.drug, 0.0, 0.0, "ACK pressed.", False))
    os_ = oxygen_dev.get_status()
    if os_.running and os_.auto_started:
        oxygen_dev.apply(OxygenCommand("STOP", os_.mode, 0.0, 0.21, 0.0, "ACK pressed.", False))


def render_alarm_strip(title: str, problem: str, msg: str, pending: bool, pending_left: float, latched: bool, last_state: str):
    timer_class = "timer-digi timer-red" if (pending or latched) else "timer-digi"
    extra_badge = ""
    if latched:
        badge = "AUTO ACTIVE"
        extra_badge = '<span class="badge-latched">ACK REQUIRED</span>'
        display_timer = "ACK!"
    elif pending:
        badge = "COUNTDOWN ACTIVE"
        display_timer = f"{pending_left:04.1f}s"
    elif last_state in ("HIGH_BP", "HYPERTENSIVE_CRISIS"):
        badge = "MANUAL REVIEW"
        extra_badge = '<span class="badge-highbp">CONTROLLED SUPPORT</span>'
        display_timer = "--.--"
    else:
        badge = "MONITORING"
        display_timer = "--.--"
    st.markdown(
        f"""
<div class="alarm-strip">
<div class="alarm-left">
<div class="alarm-title">{title}</div>
<div class="alarm-problem">{problem}</div>
<div class="alarm-msg">{msg}</div>
<div class="badge-auto">{badge}</div>{extra_badge}
</div>
<div class="timer-box">
<div class="timer-label">Countdown</div>
<div class="{timer_class}">{display_timer}</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_summary_card(profile: PatientProfile, scenario: str):
    st.markdown(
        f"""
<div class="summary-card">
<div class="summary-title">Patient Clinical Summary</div>
<div class="summary-grid">
<div><span>ID:</span> {profile.patient_id}</div>
<div><span>Scenario:</span> {scenario}</div>
<div><span>Sex:</span> {profile.sex}</div>
<div><span>Age:</span> {profile.age}</div>
<div><span>Weight:</span> {profile.weight_kg:.1f} kg</div>
<div><span>Clinician:</span> Dr. Ahmed Mohamed Aljak</div>
<div><span>Contact:</span> 0903600668</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _reset_for_new_scenario(scenario: str) -> None:
    st.session_state.active_scenario_snapshot = scenario
    st.session_state.sim.force_scenario(scenario)
    st.session_state.waves = WaveBuffer(sample_hz=60)
    st.session_state.engine.reset()
    st.session_state.pump = InfusionPumpSim(max_flow_mlh=ICUSettings().max_flow_mlh)
    st.session_state.oxygen_dev = OxygenControllerSim()
    st.session_state.manual_override = False
    st.session_state.auto_armed = True
    st.session_state.approval_required = False


def render_scenario_expanders() -> None:
    st.markdown("<div class='scenario-mini-title'>Clinical Scenarios</div>", unsafe_allow_html=True)
    for group_name, options in SCENARIO_GROUPS.items():
        with st.expander(group_name, expanded=(st.session_state.scenario_group == group_name)):
            for scenario in options:
                active = scenario == st.session_state.scenario
                label = ("● " if active else "○ ") + scenario
                if st.button(label, key=f"scenario_btn_{group_name}_{scenario}", use_container_width=True):
                    st.session_state.scenario_group = group_name
                    st.session_state.scenario = scenario
                    _reset_for_new_scenario(scenario)
                    st.rerun()


def render_clinical_response_panel(v, engine, ps, os_, risk_text: str, any_pending: bool, any_latched: bool, any_running_auto: bool, ack: bool) -> None:
    bp = engine.channels["bp"]
    spo2 = engine.channels["spo2"]
    pending_left = max(float(bp.pending_left or 0.0), float(spo2.pending_left or 0.0))
    if ack:
        css_class = "crp-ack"
        status = "CLINICIAN ACKNOWLEDGED"
        main = "Control returned to clinician"
        msg = "Automatic support is stopped and the system returns to monitoring only."
        response = "ACKNOWLEDGED"
    elif any_running_auto:
        css_class = "crp-auto"
        status = "LIMITED EMERGENCY SUPPORT"
        main = "Temporary partial stabilization in progress"
        msg = "Simulated support is active. Target is about 80% stabilization, not complete treatment."
        response = "NOT DETECTED"
    elif any_pending or any_latched:
        css_class = "crp-warning"
        status = "AWAITING RESPONSE"
        main = "Clinician response required"
        problems = []
        if bp.problem and bp.problem != "Normal":
            problems.append(bp.problem)
        if spo2.problem and spo2.problem != "Normal":
            problems.append(spo2.problem)
        msg = " / ".join(problems) if problems else "Abnormal vital signs detected."
        response = "PENDING"
    elif risk_text == "CRITICAL":
        css_class = "crp-critical"
        status = "CRITICAL CONDITION"
        main = "Critical physiology detected"
        msg = "Continuous monitoring active. Prepare escalation if the response window starts."
        response = "REQUIRED"
    else:
        css_class = "crp-monitoring"
        status = "MONITORING ONLY"
        main = "No active emergency support"
        msg = "Vital signs are being monitored. Auto support remains on standby until a critical event is detected."
        response = "STANDBY"
    pump_state = "AUTO ACTIVE" if (ps.running and ps.auto_started) else ("RUNNING" if ps.running else "STANDBY")
    oxy_state = "AUTO ACTIVE" if (os_.running and os_.auto_started) else ("RUNNING" if os_.running else "STANDBY")
    timer = f"{pending_left:04.1f}s" if (any_pending or any_latched) else "--.--"
    st.markdown(
        f"""
<div class="clinical-response-panel {css_class}">
<div class="crp-head">
<div class="crp-title">Clinical Response Panel</div>
<div class="crp-status">{status}</div>
</div>
<div class="crp-grid">
<div>
<div class="crp-main">{main}</div>
<div class="crp-msg">{msg}</div>
</div>
<div class="crp-meta">
<div><span>Assigned Clinician:</span> Dr. Ahmed Mohamed Aljak</div>
<div><span>Contact:</span> 0903600668</div>
<div><span>Response Window:</span> {timer}</div>
<div><span>Response:</span> {response}</div>
<div><span>IV Pump:</span> {pump_state}</div>
<div><span>Oxygen:</span> {oxy_state}</div>
</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


WELCOME_CSS = """
<style>
header, footer, #MainMenu {visibility:hidden !important;}
.block-container{padding:0 !important;max-width:none !important;}
.exact-welcome-wrap{width:100vw;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#061221;overflow:hidden;}
.exact-welcome-frame{position:relative;width:min(1536px,100vw);aspect-ratio:16/9;background-image:url("data:image/png;base64,__WELCOME_IMAGE_B64__");background-size:cover;background-position:center center;background-repeat:no-repeat;overflow:hidden;}
.exact-welcome-hitbox{position:absolute;left:35.45%;top:78.65%;width:27.8%;height:11.1%;border-radius:999px;display:block;background:transparent;z-index:40;}
</style>
"""


def _welcome_image_b64() -> str:
    img_path = Path(__file__).with_name("welcome_exact.png")
    if not img_path.exists():
        return ""
    return base64.b64encode(img_path.read_bytes()).decode("ascii")


def welcome_gate():
    qp = st.query_params
    if qp.get("enter_app") == "1":
        st.session_state.entered_app = True
        try:
            del st.query_params["enter_app"]
        except Exception:
            pass
    if st.session_state.get("entered_app", False):
        return
    _b64 = _welcome_image_b64()
    if _b64:
        st.markdown(WELCOME_CSS.replace("__WELCOME_IMAGE_B64__", _b64), unsafe_allow_html=True)
        st.markdown(
            '<div class="exact-welcome-wrap"><div class="exact-welcome-frame">'
            '<a class="exact-welcome-hitbox" href="?enter_app=1" aria-label="Start Simulation"></a>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        st.stop()
    st.markdown(CLEAR_UI, unsafe_allow_html=True)
    st.markdown('<div class="boot-wrap"><div class="boot-title">ICU INTELLIGENT CLINICAL SUPPORT SYSTEM</div><div class="boot-sub">Original welcome image missing from project folder; place welcome_exact.png beside app_streamlit.py to restore the exact same start screen.</div></div>', unsafe_allow_html=True)
    if st.button("START SIMULATION", use_container_width=True):
        st.session_state.entered_app = True
        st.rerun()
    st.stop()


def main():
    st.set_page_config(page_title="ICU Professional Simulation", layout="wide")
    welcome_gate()
    boot_screen()
    init_app()
    st.markdown('<div class="device">', unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="topbar">
<div>
<div class="brand">ICU SMART MONITOR — Intelligent ICU Monitoring & Emergency Support Simulation</div>
<div class="sub">Hemodynamic • Oxygenation • Scenario-driven monitor • Tick {st.session_state.tick:.2f}s • Manufacturer: {MANUFACTURER}</div>
</div>
<div class="sub">Local time: <b>{now_hhmm()}</b> • Version: <b>{APP_VERSION}</b></div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="device-banner">
<div class="left">Device ID: ICU-SIM-01 • Network: ONLINE</div>
<div class="right">Manual Override: <b>{'ON' if st.session_state.manual_override else 'OFF'}</b><br><span style='font-size:12px;color:#dff7ff;'>Physician: <b>Ahmed Mohamed Aljak</b> • 0903600668</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    c0, c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.2, 1.2, 1.2], gap="small")
    with c0:
        if st.button("🟢 START", use_container_width=True):
            st.session_state.running = True
    with c1:
        if st.button("⏸ PAUSE", use_container_width=True):
            st.session_state.running = False
    with c2:
        if st.button("🔁 RESET", use_container_width=True):
            st.session_state.running = False
            st.session_state.sim.reset()
            st.session_state.waves = WaveBuffer(sample_hz=60)
            st.session_state.engine.reset()
            st.session_state.pump = InfusionPumpSim(max_flow_mlh=ICUSettings().max_flow_mlh)
            st.session_state.oxygen_dev = OxygenControllerSim()
            st.session_state.manual_override = False
            st.session_state.auto_armed = True
            st.session_state.approval_required = False
            st.session_state.ack_pressed = False
    with c3:
        if st.button("🔔 ACK", use_container_width=True, type="primary"):
            st.session_state.ack_pressed = True
            st.session_state.manual_override = True
            st.session_state.auto_armed = False
            ack_stop_auto_devices()
    with c4:
        st.session_state.tick = st.slider("Tick (sec)", 0.10, 1.00, float(st.session_state.tick), 0.05)
    with c5:
        st.session_state.auto_armed = st.toggle("Auto Armed", value=bool(st.session_state.auto_armed))
    st.session_state.approval_required = False
    if st.session_state.ack_pressed:
        st.session_state.ack_pressed = False
    st.write("")
    left, right = st.columns([1.00, 1.70], gap="large")
    with left:
        st.markdown('<div class="device">', unsafe_allow_html=True)
        prof = current_profile()
        st.markdown("<div class='summary-card'><div class='summary-title'>Active Case</div><div style='color:#e8f8ff;font-weight:900;font-size:18px;'>Single Patient Session</div><div style='color:#9fc7d8;font-size:13px;margin-top:6px;'>Focused simulation workflow without multi-patient switching.</div></div>", unsafe_allow_html=True)
        render_summary_card(prof, st.session_state.scenario)
        st.markdown("**Patient Profile**")
        pcols = st.columns(3, gap="small")
        with pcols[0]:
            prof.sex = pill_choice("Sex", ["M", "F"], key="sex_choice", columns=2)
        with pcols[1]:
            prof.age = int(st.slider("Age", 1, 100, int(prof.age), 1))
        with pcols[2]:
            prof.weight_kg = float(st.slider("Weight (kg)", 20.0, 160.0, float(prof.weight_kg), 0.5))
        st.divider()
        render_scenario_expanders()
        st.divider()
        st.markdown("<div class='control-screen'><div class='control-title'>Manual Pump Settings</div>", unsafe_allow_html=True)
        ps = st.session_state.pump.get_status()
        mp1, mp2, mp3 = st.columns(3, gap="small")
        with mp1:
            manual_pump_therapy = st.selectbox("Therapy", ["0.9% Normal Saline", "Ringer Lactate", "Balanced Crystalloid", "Dopamine", "Noradrenaline", "Labetalol", "Hydralazine", "Furosemide inj"], key="manual_pump_therapy")
        with mp2:
            manual_pump_rate = st.number_input("Rate (mL/h)", min_value=0.0, max_value=1000.0, value=float(ps.rate_mlh) if ps.running else 0.0, step=10.0, key="manual_pump_rate")
        with mp3:
            manual_pump_duration = st.number_input("Duration (min)", min_value=0.0, max_value=120.0, value=float(ps.duration_min) if ps.running else 10.0, step=1.0, key="manual_pump_duration")
        mp_btn1, mp_btn2 = st.columns(2, gap="small")
        if mp_btn1.button("START PUMP", use_container_width=True):
            st.session_state.pump.apply(PumpCommand("START", manual_pump_therapy, manual_pump_rate, manual_pump_duration, "Manual pump command.", False))
        if mp_btn2.button("STOP PUMP", use_container_width=True):
            st.session_state.pump.apply(PumpCommand("STOP", ps.drug, 0.0, 0.0, "Manual pump stop.", False))
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='control-screen'><div class='control-title'>Manual Oxygen Settings</div>", unsafe_allow_html=True)
        os_ = st.session_state.oxygen_dev.get_status()
        mo1, mo2, mo3 = st.columns(3, gap="small")
        with mo1:
            manual_oxy_mode = st.selectbox("Mode", ["O2 Boost (SIM)", "High O2 Support (SIM)", "Controlled Wean (SIM)"], key="manual_oxy_mode")
        with mo2:
            manual_oxy_flow = st.number_input("Flow (L/min)", min_value=0.0, max_value=15.0, value=float(os_.flow_l_min) if os_.running else 0.0, step=0.5, key="manual_oxy_flow")
        with mo3:
            manual_oxy_fio2 = st.number_input("FiO2", min_value=0.21, max_value=1.0, value=float(os_.fio2) if os_.running else 0.21, step=0.01, key="manual_oxy_fio2")
        mo_btn1, mo_btn2 = st.columns(2, gap="small")
        if mo_btn1.button("START O2", use_container_width=True):
            st.session_state.oxygen_dev.apply(OxygenCommand("START", manual_oxy_mode, manual_oxy_flow, manual_oxy_fio2, 10.0, "Manual oxygen command.", False))
        if mo_btn2.button("STOP O2", use_container_width=True):
            st.session_state.oxygen_dev.apply(OxygenCommand("STOP", os_.mode, 0.0, 0.21, 0.0, "Manual oxygen stop.", False))
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="monitor">', unsafe_allow_html=True)
        st.markdown(
            f"""
<div class="mon-head">
<div class="mon-title">ICU Monitor</div>
<div class="mon-meta">{now_hhmm()} | 3 Waves</div>
</div>
""",
            unsafe_allow_html=True,
        )
        dt = float(st.session_state.tick)
        stepped = False
        if st.session_state.running:
            st_autorefresh(interval=int(dt * 1000), key="tick_loop")
            stepped = True
        sim = st.session_state.sim
        engine = st.session_state.engine
        pump = st.session_state.pump
        oxygen_dev = st.session_state.oxygen_dev
        v = sim.tick(dt=dt, scenario=st.session_state.scenario) if stepped else sim.v
        ps_pre = pump.get_status()
        os_pre = oxygen_dev.get_status()
        events, cmds = engine.step(
            profile=prof,
            scenario=st.session_state.scenario,
            vitals={
                "sbp": float(v.sbp),
                "dbp": float(v.dbp),
                "spo2": float(v.spo2),
                "hr": float(v.hr),
                "rr": float(v.rr),
                "temp": float(v.temp),
            },
            ack_pressed=False,
            auto_armed=bool(st.session_state.auto_armed),
            approval_required=bool(st.session_state.approval_required),
            approve_auto=False,
            cancel_auto=False,
            dt_sec=dt,
            manual_override=bool(st.session_state.manual_override),
            pump_status=ps_pre,
            oxygen_status=os_pre,
        )
        if cmds["pump"] is not None:
            pump.apply(cmds["pump"])
        if cmds["oxygen"] is not None:
            oxygen_dev.apply(cmds["oxygen"])
        pump.tick(dt_sec=dt)
        oxygen_dev.tick(dt_sec=dt)
        ps = pump.get_status()
        os_ = oxygen_dev.get_status()
        if ps.running:
            sim.apply_pump_effect(dt=dt, rate_mlh=ps.rate_mlh, therapy=ps.drug, auto_generated=ps.auto_started)
        if os_.running:
            sim.apply_oxygen_effect(dt=dt, flow_l_min=os_.flow_l_min, fio2=os_.fio2, mode=os_.mode, auto_generated=os_.auto_started)
        # evaluate_global_state is now called only once here (removed duplicate from tick())
        sim.evaluate_global_state(dt, auto_active=bool((ps.running and ps.auto_started) or (os_.running and os_.auto_started)))
        v = sim.v
        if sim.life_state == "DEAD":
            st.session_state.running = False
        risk_text, risk_color = compute_risk(v)
        any_pending = (
            engine.channels["bp"].pending
            or engine.channels["spo2"].pending
        )
        any_latched = (
            engine.channels["bp"].latched
            or engine.channels["spo2"].latched
        )
        any_running_auto = (
            (ps.running and ps.auto_started)
            or (os_.running and os_.auto_started)
        )
        audio_mode = None
        if sim.life_state == "DEAD":
            audio_mode = "death"
        elif sim.life_state in {"PRE_ARREST", "ARREST"} or sim.doctor_call_required:
            audio_mode = "critical"
        elif any_pending or any_latched:
            audio_mode = "alert"
        elif st.session_state.running:
            audio_mode = "monitor"
        if audio_mode:
            render_audio_alarm(audio_mode, hr=float(v.hr), spo2=float(v.spo2))
        st.markdown(
            f"""
<div class="risk-bar" style="border:1px solid {risk_color}; color:{risk_color};">
CLINICAL RISK LEVEL : {risk_text}
</div>
""",
            unsafe_allow_html=True,
        )
        st.session_state.waves.append(dt_sec=dt if stepped else 0.01, hr=v.hr, rr=v.rr, spo2=v.spo2, sbp=v.sbp, dbp=v.dbp, scenario=st.session_state.scenario, life_state=sim.life_state)
        wdf = st.session_state.waves.tail_df(seconds=8.0)
        map_v = (v.sbp + 2.0 * v.dbp) / 3.0
        st.markdown('<div class="biggrid">', unsafe_allow_html=True)
        st.markdown('<div class="waves">', unsafe_allow_html=True)
        st.markdown("<div class='sub'>II</div>", unsafe_allow_html=True)
        st.altair_chart(_alt_wave(wdf, "ecg", "#22ff55", height=84), use_container_width=True)
        st.markdown("<div class='sub'>Pleth</div>", unsafe_allow_html=True)
        st.altair_chart(_alt_wave(wdf, "pleth", "#44d7ff", height=74), use_container_width=True)
        st.markdown("<div class='sub'>Resp</div>", unsafe_allow_html=True)
        st.altair_chart(_alt_wave(wdf, "resp", "#ffd84d", height=74), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="vitals">', unsafe_allow_html=True)
        st.markdown(
            f"""
<div class="vrow">
<div class="vcard">
<div class="vlabel">HR</div>
<div class="digi big c-ecg">{int(round(v.hr))}</div>
<div class="small">Pulse</div>
</div>
<div class="vcard">
<div class="vlabel">SpO₂</div>
<div class="digi big c-pleth">{int(round(v.spo2))}</div>
<div class="small">%</div>
</div>
</div>
<div class="vrow" style="margin-top:10px;">
<div class="vcard">
<div class="vlabel">RR</div>
<div class="digi big c-resp">{int(round(v.rr))}</div>
<div class="small">/min</div>
</div>
<div class="vcard">
<div class="vlabel">Temp</div>
<div class="digi mid c-temp">{v.temp:.1f}</div>
<div class="small">°C</div>
</div>
</div>
<div class="vrow" style="margin-top:10px;">
<div class="vcard">
<div class="vlabel">NBP</div>
<div class="digi big c-bp">{int(round(v.sbp))}/{int(round(v.dbp))}</div>
<div class="small">MAP {int(round(map_v))}</div>
</div>
<div class="vcard">
<div class="vlabel">EtCO₂</div>
<div class="digi mid c-temp">{v.etco2:.0f}</div>
<div class="small">mmHg</div>
</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='alarm-row'>", unsafe_allow_html=True)
        ac1, ac2 = st.columns(2, gap="small")
        with ac1:
            render_alarm_strip(
                "Hemodynamic Alarm",
                engine.channels["bp"].problem,
                engine.channels["bp"].message,
                engine.channels["bp"].pending,
                engine.channels["bp"].pending_left,
                engine.channels["bp"].latched,
                engine.channels["bp"].state,
            )
        with ac2:
            render_alarm_strip(
                "Oxygenation Alarm",
                engine.channels["spo2"].problem,
                engine.channels["spo2"].message,
                engine.channels["spo2"].pending,
                engine.channels["spo2"].pending_left,
                engine.channels["spo2"].latched,
                engine.channels["spo2"].state,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        render_clinical_response_panel(v, engine, ps, os_, risk_text, bool(any_pending), bool(any_latched), bool(any_running_auto), False)
        if sim.doctor_call_required or sim.life_state in {"PRE_ARREST", "ARREST", "DEAD"}:
            title = "Critical Clinical Escalation" if sim.life_state != "DEAD" else "No Vital Signs"
            render_doctor_call_strip(title, sim.doctor_message or "Call Dr. Ahmed Mohamed Aljak immediately.")
        if sim.manual_error_flag and sim.last_manual_reason:
            st.markdown(f"<div class='summary-card'><div class='summary-title'>Manual Intervention Review</div><div style='color:#ffd9d9;font-weight:900;'>Unsafe manual setting detected</div><div style='margin-top:8px;color:#eef9ff;font-size:13px;'>{sim.last_manual_reason}</div></div>", unsafe_allow_html=True)
        if sim.life_state == "PRE_ARREST":
            st.markdown("<div class='summary-card'><div class='summary-title'>Death Scenario State</div><div style='color:#ffb3b3;font-weight:1000;'>PRE-ARREST</div><div style='margin-top:8px;color:#eef9ff;font-size:13px;'>Severe deterioration is progressing toward cardiac arrest unless corrected immediately.</div></div>", unsafe_allow_html=True)
        elif sim.life_state == "ARREST":
            st.markdown("<div class='summary-card'><div class='summary-title'>Death Scenario State</div><div style='color:#ff9fa8;font-weight:1000;'>CARDIAC ARREST</div><div style='margin-top:8px;color:#eef9ff;font-size:13px;'>Pulseless arrest is active. ECG, pleth and respiration are collapsing toward a flat line.</div></div>", unsafe_allow_html=True)
        elif sim.life_state == "DEAD":
            st.markdown("<div class='summary-card'><div class='summary-title'>Death Scenario State</div><div style='color:#ff7c8e;font-weight:1000;'>NO VITAL SIGNS / FLATLINE</div><div style='margin-top:8px;color:#eef9ff;font-size:13px;'>All displayed vital signs have reached zero and the monitor has transitioned to a continuous flatline tone.</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.write("")
    ps = st.session_state.pump.get_status()
    os_ = st.session_state.oxygen_dev.get_status()
    bottom1, bottom2 = st.columns(2, gap="large")
    with bottom1:
        rate = float(ps.rate_mlh)
        speed = max(0.25, min(7.0, rate / 110.0 if rate > 0 else 0.25))
        pos = (time.time() * speed) % 1.0
        left_pct = pos * 94.0
        infused_pct = max(8.0, min(92.0, (ps.infused_ml / max(1.0, ps.infused_ml + 60.0)) * 100.0)) if ps.running or ps.infused_ml > 0 else 10.0
        bag_fill_pct = max(16.0, min(88.0, 92.0 - (infused_pct * 0.72)))
        pump_badge = "AUTO ACTIVE" if ps.auto_started else ("RUNNING" if ps.running else "STANDBY")
        pump_status_class = "" if ps.running else "stop"
        st.markdown(
            f"""
<div class="device-card pump-card">
<div class="device-head">
<div>
<div class="device-kicker">Hemodynamic Therapy</div>
<div class="device-name">Infusion Pump</div>
</div>
<div class="device-badge">{pump_badge}</div>
</div>
<div class="device-shell">
<div class="device-screen">
<div class="screen-topline">{support_display(ps.drug)}</div>
<div class="screen-rule"></div>
<div class="numeric-grid">
<div>
<div class="minor-label">Rate</div>
<div class="big-reading">{int(round(ps.rate_mlh))}</div>
<div class="unit-label">mL/hr</div>
</div>
<div>
<div class="minor-label">Time Left</div>
<div class="minor-value">{int(ps.time_left_sec//60):02d}:{int(ps.time_left_sec%60):02d}</div>
<div class="minor-label" style="margin-top:10px;">Infused</div>
<div class="minor-value">{ps.infused_ml:.1f} mL</div>
</div>
</div>
<div class="device-status-line">
<span class="status-pill"><span class="status-dot {pump_status_class}"></span>{'RUN' if ps.running else 'STOP'}</span>
<span class="status-pill">{('Auto command' if ps.auto_started else 'Manual control')}</span>
</div>
<div class="infused-bar">
<div class="infused-label">Fluid Chamber</div>
<div class="infused-fill" style="height:{infused_pct:.1f}%;"></div>
</div>
<div class="droplet-rail"><div class="droplet" style="left:{left_pct:.1f}%;"></div></div>
<div class="iv-assembly">
<div class="iv-hook"></div>
<div class="iv-rail"></div>
<div class="iv-bag">
<div class="iv-bag-shine"></div>
<div class="iv-mark"><span></span><span></span><span></span><span></span><span></span></div>
<div class="iv-bag-fill" style="height:{bag_fill_pct:.1f}%;"></div>
</div>
<div class="iv-tube-main"></div>
<div class="drip-chamber">
<div class="drip-drop"></div>
<div class="drip-liquid"></div>
</div>
<div class="iv-tube-run"></div>
<div class="iv-pump-face"><div class="iv-pump-led"></div></div>
</div>
<div class="device-footnote">{support_display(ps.last_msg) if ps.auto_started else ps.last_msg}</div>
</div>
</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='control-screen'><div class='control-title'>IV Pump Auto Support</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='control-foot'><b>Mode:</b> Scenario-driven automatic support &nbsp;|&nbsp; <b>Recommended:</b> {recommended_therapy(st.session_state.scenario)} &nbsp;|&nbsp; <b>Status:</b> {pump_badge}</div>",
            unsafe_allow_html=True,
        )
        pc1, pc2 = st.columns(2, gap="small")
        if pc1.button("PUMP STANDBY", use_container_width=True):
            ps_now = st.session_state.pump.get_status()
            st.session_state.pump.apply(PumpCommand("STOP", ps_now.drug, 0.0, 0.0, "Pump placed on standby by operator.", False))
        if pc2.button("AUTO READY", use_container_width=True, key="pump_auto_ready"):
            st.session_state.auto_armed = True
            st.session_state.manual_override = False
        st.markdown("</div>", unsafe_allow_html=True)
    with bottom2:
        fio2_pct = int(round(os_.fio2 * 100))
        ring_fill = max(8, min(100, fio2_pct))
        oxy_badge = "AUTO ACTIVE" if os_.auto_started else ("RUNNING" if os_.running else "STANDBY")
        oxy_status_class = "" if os_.running else "warn"
        ring_style = f"background: conic-gradient(#66dfff 0% {ring_fill}%, rgba(255,255,255,0.10) {ring_fill}% 100%);"
        flow_fill_pct = max(16, min(88, int((os_.flow_l_min / 15.0) * 100)))
        st.markdown(
            f"""
<div class="device-card oxy-card">
<div class="device-head">
<div>
<div class="device-kicker">Oxygenation Support</div>
<div class="device-name">Oxygen Controller</div>
</div>
<div class="device-badge">{oxy_badge}</div>
</div>
<div class="device-shell">
<div class="device-screen">
<div class="screen-topline">{support_display(os_.mode)}</div>
<div class="screen-rule"></div>
<div class="numeric-grid">
<div>
<div class="minor-label">Flow</div>
<div class="big-reading">{os_.flow_l_min:.1f}</div>
<div class="unit-label">L/min</div>
</div>
<div class="oxy-ring-wrap">
<div class="oxy-ring" style="{ring_style}">
<div class="oxy-ring-center">
<div class="oxy-ring-val">{fio2_pct}%</div>
<div class="oxy-ring-sub">FiO₂</div>
</div>
</div>
</div>
</div>
<div class="device-status-line">
<span class="status-pill"><span class="status-dot {oxy_status_class}"></span>{'RUN' if os_.running else 'STANDBY'}</span>
<span class="status-pill">Time {int(os_.time_left_sec//60):02d}:{int(os_.time_left_sec%60):02d}</span>
</div>
<div class="oxy-flow-line"></div>
<div class="oxy-assembly">
<div class="oxy-cylinder"></div>
<div class="oxy-regulator"></div>
<div class="flowmeter">
<div class="flowmeter-fill" style="height:{flow_fill_pct}%;"></div>
<div class="flowmeter-bubble"></div>
</div>
<div class="oxy-patient-line"></div>
<div class="oxy-nasal"></div>
<div class="oxy-pulse"><span></span><span></span><span></span><span></span><span></span></div>
</div>
<div class="device-footnote">{support_display(os_.last_msg) if os_.auto_started else os_.last_msg}</div>
</div>
</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='control-screen'><div class='control-title'>Oxygen Auto Support</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='control-foot'><b>Mode:</b> Scenario-driven automatic support &nbsp;|&nbsp; <b>Recommended:</b> {recommended_therapy(st.session_state.scenario)} &nbsp;|&nbsp; <b>Status:</b> {oxy_badge}</div>",
            unsafe_allow_html=True,
        )
        oc1, oc2 = st.columns(2, gap="small")
        if oc1.button("O₂ STANDBY", use_container_width=True):
            os_now = st.session_state.oxygen_dev.get_status()
            st.session_state.oxygen_dev.apply(OxygenCommand("STOP", os_now.mode, 0.0, 0.21, 0.0, "Oxygen placed on standby by operator.", False))
        if oc2.button("AUTO READY", use_container_width=True, key="oxygen_auto_ready"):
            st.session_state.auto_armed = True
            st.session_state.manual_override = False
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()