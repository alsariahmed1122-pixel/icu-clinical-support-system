MANUFACTURER = "Ahmed Mohamed Aljak | أحمد محمد الجاك"

CSS = f"""
<style>
:root {{
  --bg0:#07111f;
  --bg1:#0a1728;
  --bg2:#101f35;
  --panel: rgba(255,255,255,0.08);
  --panel2: rgba(255,255,255,0.04);
  --stroke: rgba(171,240,255,0.18);
  --stroke2: rgba(118,221,255,0.34);
  --txt:#effcff;
  --muted:#b9d8eb;
  --mint:#64ffd8;
  --aqua:#66dfff;
  --sky:#7bb8ff;
  --gold:#ffd76a;
  --rose:#ff8da1;
  --ecg:#7bff86;
  --pleth:#5be2ff;
  --resp:#ffd76a;
  --bp:#ff7887;
  --temp:#8fffc0;
}}

html, body, [class*="css"]  {{
  font-family: Inter, "Segoe UI", Tahoma, Arial, sans-serif;
}}

.stApp {{
  background:
    radial-gradient(1200px 800px at 10% 10%, rgba(91,226,255,0.18), transparent 55%),
    radial-gradient(1000px 700px at 85% 18%, rgba(123,255,134,0.10), transparent 50%),
    radial-gradient(1000px 700px at 52% 100%, rgba(255,215,106,0.10), transparent 58%),
    linear-gradient(160deg, var(--bg0) 0%, var(--bg1) 46%, #08121f 100%);
  color: var(--txt);
}}

.block-container{{
  padding-top: .9rem;
  padding-bottom: 1.6rem;
  max-width: 1580px;
}}

label, .stMarkdown, .stText, p, div, span, h1,h2,h3,h4 {{
  color: var(--txt) !important;
}}

.stApp:before {{
  content:"{MANUFACTURER}";
  position: fixed;
  right: 18px;
  bottom: 12px;
  z-index: 9999;
  font-weight: 900;
  letter-spacing: 1px;
  font-size: 11px;
  color: rgba(239,252,255,0.20);
  pointer-events:none;
}}

.device {{
  border: 1px solid var(--stroke);
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.03)),
    linear-gradient(160deg, rgba(9,20,36,0.94), rgba(5,12,24,0.98));
  box-shadow:
    0 32px 90px rgba(0,0,0,0.55),
    inset 0 1px 0 rgba(255,255,255,0.12),
    inset 0 -20px 80px rgba(91,226,255,0.03);
  padding: 16px;
  backdrop-filter: blur(12px);
}}

.topbar {{
  display:flex; justify-content:space-between; align-items:center; gap:14px;
  padding: 14px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.10);
  background:
    linear-gradient(135deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
}}

.brand {{
  font-weight: 1000;
  letter-spacing: 0.8px;
  font-size: 20px;
  background: linear-gradient(90deg, #effcff, #8ef5ff, #95ffcb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}

.sub {{
  font-size: 12px;
  color: var(--muted) !important;
}}

.monitor {{
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 24px;
  background:
    radial-gradient(circle at 15% 10%, rgba(91,226,255,0.10), transparent 28%),
    linear-gradient(180deg, rgba(4,12,22,0.96), rgba(2,8,16,0.98));
  padding: 12px;
  box-shadow:
    0 26px 70px rgba(0,0,0,0.45),
    inset 0 1px 0 rgba(255,255,255,0.06);
}}

.mon-head {{
  display:flex; justify-content:space-between; align-items:center;
  padding: 10px 12px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 12px;
}}
.mon-title {{ font-weight: 900; letter-spacing: .8px; font-size: 12px; color: rgba(255,255,255,0.88) !important; }}
.mon-meta {{ font-weight: 800; font-size: 12px; color: rgba(255,255,255,0.68) !important; }}

.biggrid {{ display:grid; grid-template-columns: 1.35fr 0.95fr; gap: 12px; }}
.waves, .vitals {{
  border-radius: 18px;
  padding: 12px;
  background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}}
.vrow {{ display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.vcard {{
  border-radius: 18px;
  padding: 12px;
  min-height: 128px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}}
.vlabel {{ font-size: 12px; font-weight: 900; letter-spacing: .9px; color: rgba(255,255,255,0.64) !important; text-transform: uppercase; }}
.digi {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight: 1000; letter-spacing: 1px; line-height: 1.0; }}
.big {{ font-size: 68px; }}
.mid {{ font-size: 46px; }}
.small {{ font-size: 17px; color: rgba(255,255,255,0.74) !important; }}
.c-ecg{{ color: var(--ecg) !important; text-shadow: 0 0 22px rgba(123,255,134,0.28); }}
.c-pleth{{ color: var(--pleth) !important; text-shadow: 0 0 22px rgba(91,226,255,0.26); }}
.c-resp{{ color: var(--resp) !important; text-shadow: 0 0 22px rgba(255,215,106,0.22); }}
.c-bp{{ color: var(--bp) !important; text-shadow: 0 0 22px rgba(255,120,135,0.24); }}
.c-temp{{ color: var(--temp) !important; text-shadow: 0 0 22px rgba(143,255,192,0.20); }}

.device-banner {{
  display:flex; justify-content:space-between; align-items:center; gap:12px;
  background: linear-gradient(135deg, rgba(117,225,255,0.10), rgba(123,255,134,0.06));
  border:1px solid rgba(118,221,255,.18);
  border-radius:18px; padding:12px 14px; margin-bottom:12px;
}}
.device-banner .left {{ color:#f4fbff; font-weight:900; }}
.device-banner .right {{ color:#b5dff0; font-size:13px; text-align:right; }}

.risk-bar {{
  margin-top:10px; border-radius:16px; padding:13px 14px; font-weight:1000; text-align:center;
  font-size:14px; letter-spacing:.7px; background:#09131f; box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}}

.alarm-strip {{
  margin-top: 12px; border: 1px solid rgba(255, 120, 135, 0.42);
  background: linear-gradient(180deg, rgba(84,20,29,0.82), rgba(30,8,12,0.72));
  border-radius: 20px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; gap: 16px;
  box-shadow: 0 18px 32px rgba(0,0,0,0.20);
}}
.alarm-title {{ color: #ffb7c2; font-weight: 1000; letter-spacing: 1px; font-size: 12px; text-transform: uppercase; }}
.alarm-problem {{ color: #ffffff; font-weight: 1000; font-size: 22px; line-height: 1.1; }}
.alarm-msg {{ color: #ffe7e7; font-weight: 800; font-size: 13px; margin-top: 6px; }}
.timer-box {{ flex: 0 0 auto; min-width: 168px; text-align: center; border: 1px solid rgba(91,226,255,0.25); background: rgba(0,0,0,0.38); border-radius: 18px; padding: 12px 10px; }}
.timer-label {{ color: #9ef2ff; font-size: 11px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; }}
.timer-digi {{ margin-top: 5px; font-family: ui-monospace, Consolas, monospace; font-size: 42px; font-weight: 1000; line-height: 1; color: #67efff; text-shadow: 0 0 8px rgba(103,239,255,0.40), 0 0 18px rgba(103,239,255,0.28); }}
.timer-red {{ color: #ff7887 !important; text-shadow: 0 0 8px rgba(255,120,135,0.40), 0 0 18px rgba(255,120,135,0.28) !important; }}
.badge-auto,.badge-latched,.badge-highbp {{ display:inline-block; margin-top:8px; padding:4px 9px; border-radius:999px; font-size:11px; font-weight:900; letter-spacing:.6px; }}
.badge-auto {{ background:rgba(255,255,255,0.08); color:#ffd7d7; }}
.badge-latched {{ margin-left:8px; background:rgba(255,120,135,0.16); color:#ffd8df; border:1px solid rgba(255,120,135,0.28); }}
.badge-highbp {{ margin-left:8px; background:rgba(255,215,106,0.14); color:#ffe9a6; border:1px solid rgba(255,215,106,0.24); }}

.summary-card {{
  background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
  border:1px solid rgba(118,221,255,.12); border-radius:18px; padding:15px 16px; color:#eef9ff; margin-bottom:12px;
}}
.summary-title {{ color:#9df4ff; font-weight:1000; font-size:13px; letter-spacing:.8px; text-transform:uppercase; margin-bottom:8px; }}
.summary-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px 14px; font-size:13px; }}
.summary-grid div span {{ color:#98b7c9; }}

.pump {{
  border-radius: 24px;
  border: 1px solid rgba(255,255,255,0.12);
  background:
    radial-gradient(circle at 15% 10%, rgba(91,226,255,0.11), transparent 30%),
    linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  padding: 14px;
  box-shadow: 0 26px 70px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
}}

.pump-screen {{
  border-radius: 18px;
  background:
    radial-gradient(circle at 85% 10%, rgba(103,239,255,0.08), transparent 24%),
    linear-gradient(180deg, #071b2d, #04111d);
  border: 1px solid rgba(128,201,255,0.25);
  padding: 14px;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.05),
    inset 0 0 0 1px rgba(0,0,0,0.20),
    inset 0 0 35px rgba(103,239,255,0.05);
}}
.pump-screen .r {{ color: #ff8ea4 !important; text-shadow: 0 0 16px rgba(255,142,164,0.20); }}
.pump-screen .w {{ color: #d8f4ff !important; }}

.drip {{ height: 18px; margin-top: 12px; border-radius: 999px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); position: relative; overflow: hidden; }}
.drop {{ position:absolute; width: 14px; height: 14px; top: 1px; border-radius: 999px; background: linear-gradient(180deg, rgba(91,226,255,1), rgba(91,226,255,.65)); box-shadow: 0 0 18px rgba(91,226,255,0.40); }}

/* ===== NEXT-GEN DEVICE CARDS ===== */
.device-card {{
  position: relative;
  border-radius: 30px;
  border: 1px solid rgba(178,238,255,0.18);
  background:
    radial-gradient(120% 120% at 12% 12%, rgba(120, 229, 255, 0.18), transparent 36%),
    radial-gradient(90% 90% at 86% 8%, rgba(255,255,255,0.14), transparent 28%),
    linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03));
  padding: 16px;
  box-shadow:
    0 26px 72px rgba(0,0,0,0.42),
    inset 0 1px 0 rgba(255,255,255,0.14),
    inset 0 -18px 42px rgba(91,226,255,0.05);
  overflow: hidden;
}}
.device-card:before {{
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 30px;
  pointer-events: none;
  background: linear-gradient(135deg, rgba(255,255,255,0.08), transparent 28%, transparent 75%, rgba(255,255,255,0.05));
}}
.device-card.pump-card {{
  background:
    radial-gradient(130% 110% at 16% 85%, rgba(118,255,171,0.12), transparent 34%),
    radial-gradient(85% 85% at 15% 10%, rgba(91,226,255,0.16), transparent 34%),
    linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.03));
}}
.device-card.oxy-card {{
  background:
    radial-gradient(100% 90% at 82% 82%, rgba(123,184,255,0.16), transparent 30%),
    radial-gradient(85% 85% at 14% 10%, rgba(91,226,255,0.16), transparent 34%),
    linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.03));
}}
.device-head {{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
  margin-bottom:12px;
}}
.device-kicker {{
  font-size: 11px;
  font-weight: 1000;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: rgba(231,247,255,0.78) !important;
}}
.device-name {{
  font-size: 17px;
  font-weight: 1000;
  color: #f6fdff !important;
  margin-top: 4px;
}}
.device-badge {{
  flex: 0 0 auto;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 1000;
  letter-spacing: .8px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.07);
  color: #effcff !important;
}}
.device-shell {{
  position: relative;
  border-radius: 28px;
  background:
    radial-gradient(circle at 50% 0%, rgba(255,255,255,0.18), transparent 26%),
    linear-gradient(180deg, rgba(245,251,255,0.95), rgba(214,232,245,0.88) 35%, rgba(167,201,224,0.82) 100%);
  border: 1px solid rgba(255,255,255,0.35);
  padding: 16px;
  box-shadow:
    0 16px 45px rgba(0,0,0,0.24),
    inset 0 2px 0 rgba(255,255,255,0.65),
    inset 0 -10px 22px rgba(59,109,145,0.16);
}}
.device-shell:after {{
  content: "";
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: 6px;
  height: 16px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(91,226,255,0.45), rgba(91,226,255,0.16), rgba(123,184,255,0.45));
  filter: blur(0.6px);
}}
.device-screen {{
  position: relative;
  z-index: 2;
  border-radius: 22px;
  min-height: 264px;
  background:
    radial-gradient(circle at 85% 8%, rgba(103,239,255,0.14), transparent 22%),
    radial-gradient(circle at 18% 92%, rgba(118,255,171,0.12), transparent 24%),
    linear-gradient(180deg, #061423, #04101b 70%, #020c16 100%);
  border: 1px solid rgba(117,220,255,0.22);
  padding: 18px;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.05),
    inset 0 0 0 1px rgba(0,0,0,0.22),
    inset 0 0 40px rgba(103,239,255,0.06);
}}
.screen-topline {{
  font-size: 14px;
  font-weight: 900;
  color: #f4fbff !important;
}}
.screen-rule {{
  margin-top: 8px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(102,223,255,0.8), rgba(255,255,255,0.16));
}}
.numeric-grid {{
  display:grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 12px;
  align-items:end;
  margin-top: 16px;
}}
.big-reading {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 64px;
  line-height: .92;
  font-weight: 1000;
  letter-spacing: -1px;
  color: #8ef8ff !important;
  text-shadow: 0 0 18px rgba(103,239,255,0.24);
}}
.unit-label {{
  font-size: 18px;
  font-weight: 900;
  color: rgba(222,244,255,0.92) !important;
}}
.minor-label {{
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .7px;
  text-transform: uppercase;
  color: rgba(201,230,246,0.66) !important;
}}
.minor-value {{
  margin-top: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 32px;
  font-weight: 1000;
  color: #ffffff !important;
}}
.device-status-line {{
  margin-top: 12px;
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap:wrap;
}}
.status-pill {{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 1000;
  letter-spacing: .7px;
  text-transform: uppercase;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  color: #f5fcff !important;
}}
.status-dot {{
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #7dff93;
  box-shadow: 0 0 16px rgba(125,255,147,0.65);
}}
.status-dot.stop {{
  background: #ff7f8f;
  box-shadow: 0 0 14px rgba(255,127,143,0.55);
}}
.status-dot.warn {{
  background: #ffd76a;
  box-shadow: 0 0 14px rgba(255,215,106,0.45);
}}
.infused-bar {{
  position: relative;
  margin-top: 14px;
  height: 64px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(110,244,196,0.18);
  background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
}}
.infused-fill {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 14px;
  background:
    radial-gradient(circle at 20% 18%, rgba(255,255,255,0.18), transparent 18%),
    linear-gradient(180deg, rgba(118,255,171,0.96), rgba(36,197,154,0.86));
  box-shadow: 0 0 22px rgba(118,255,171,0.28);
}}
.infused-fill:before {{
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.22) 45%, transparent 100%);
  animation: shimmerMove 3.2s linear infinite;
}}
.infused-label {{
  position: absolute;
  top: 10px;
  left: 12px;
  z-index: 2;
  font-size: 11px;
  font-weight: 1000;
  letter-spacing: .7px;
  color: #eafcff !important;
  text-transform: uppercase;
}}
.droplet-rail {{
  margin-top: 14px;
  height: 16px;
  border-radius: 999px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(103,239,255,0.18);
  background: rgba(255,255,255,0.05);
}}
.droplet {{
  position: absolute;
  top: 1px;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(141,248,255,1), rgba(91,226,255,0.72));
  box-shadow: 0 0 18px rgba(91,226,255,0.46);
}}
.oxy-ring-wrap {{
  display:flex;
  justify-content:center;
  align-items:center;
}}
.oxy-ring {{
  width: 128px;
  height: 128px;
  border-radius: 50%;
  display:flex;
  align-items:center;
  justify-content:center;
  position: relative;
  box-shadow: 0 0 26px rgba(103,239,255,0.18);
}}
.oxy-ring:before {{
  content: "";
  position: absolute;
  inset: 11px;
  border-radius: 50%;
  background: linear-gradient(180deg, #08131f, #05101a);
  border: 1px solid rgba(255,255,255,0.06);
}}
.oxy-ring-center {{
  position: relative;
  z-index: 2;
  text-align:center;
}}
.oxy-ring-val {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 34px;
  line-height: .95;
  font-weight: 1000;
  color: #ffffff !important;
}}
.oxy-ring-sub {{
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .7px;
  color: rgba(201,230,246,0.74) !important;
  text-transform: uppercase;
}}
.oxy-flow-line {{
  margin-top: 14px;
  height: 14px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(103,239,255,0.18);
  position: relative;
}}
.oxy-flow-line:before {{
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(103,239,255,0.95) 20%, rgba(255,255,255,0.18) 50%, rgba(103,239,255,0.95) 80%, transparent 100%);
  animation: shimmerMove 2.4s linear infinite;
}}
.device-footnote {{
  margin-top: 10px;
  font-size: 12px;
  color: rgba(222,242,252,0.74) !important;
}}
@keyframes shimmerMove {{
  0% {{ transform: translateX(-100%); }}
  100% {{ transform: translateX(100%); }}
}}


div.stButton>button {{
  width: 100%; border-radius: 16px !important; padding: 0.74rem 1rem !important; font-weight: 900 !important;
  letter-spacing: .5px !important; border: 1px solid rgba(255,255,255,0.14) !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.06)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 14px 24px rgba(0,0,0,0.18) !important;
}}

div.stButton>button:hover {{
  background: linear-gradient(180deg, rgba(103,239,255,0.18), rgba(255,255,255,0.08)) !important;
  border-color: rgba(103,239,255,0.38) !important;
}}

.stSelectbox [data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
input {{
  background: rgba(9,19,34,0.92) !important;
  border: 1px solid rgba(118,221,255,0.24) !important;
  border-radius: 14px !important;
}}

[data-testid="stSlider"] div[role="slider"] {{
  background: linear-gradient(180deg, #67efff, #92ffd3) !important;
  border: 2px solid #ffffff !important;
  box-shadow: 0 0 10px rgba(103,239,255,.35) !important;
}}

.welcome-shell{{
  min-height:100vh; display:flex; align-items:center; justify-content:center;
  background:
    radial-gradient(1200px 700px at 16% 18%, rgba(91,226,255,.18), transparent 58%),
    radial-gradient(1000px 650px at 88% 14%, rgba(123,255,134,.10), transparent 52%),
    radial-gradient(1000px 700px at 50% 100%, rgba(255,215,106,.08), transparent 58%),
    linear-gradient(180deg, #07111f 0%, #040a13 100%);
}}
.welcome-card{{
  width:min(1100px, 94vw); padding:42px; border-radius:32px;
  border:1px solid rgba(118,221,255,.20);
  background:linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.03));
  box-shadow:0 34px 100px rgba(0,0,0,.50), inset 0 1px 0 rgba(255,255,255,.08);
  backdrop-filter: blur(16px);
}}
.welcome-kicker{{color:#9df4ff; font-weight:900; letter-spacing:1.6px; font-size:12px; text-transform:uppercase;}}
.welcome-title{{font-size:50px; font-weight:1000; line-height:1.02; color:#f3fbff; margin-top:12px; max-width:850px;}}
.welcome-title strong{{background:linear-gradient(90deg,#f3fbff,#8ef5ff,#9effd2); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}}
.welcome-desc{{font-size:17px; color:#c7def2; max-width:860px; margin-top:16px; line-height:1.6;}}
.welcome-grid{{display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin:24px 0;}}
.welcome-panel{{background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08); border-radius:20px; padding:18px; min-height:110px;}}
.welcome-panel b{{display:block; color:#f6fbff; margin-bottom:8px; font-size:14px;}}
.disclaimer-box{{border:1px solid rgba(255,215,106,.25); background:rgba(255,215,106,.08); color:#ffe9a6; border-radius:18px; padding:15px; font-size:14px;}}
@media (max-width: 900px) {{
  .welcome-grid {{ grid-template-columns:1fr; }}
  .biggrid {{ grid-template-columns:1fr; }}
  .pump-shell {{ grid-template-columns:1fr; }}
}}
</style>
"""
