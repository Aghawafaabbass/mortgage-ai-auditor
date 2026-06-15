import streamlit as st
import requests
import time
import json
from datetime import datetime

st.set_page_config(
    page_title="MortgageAI Auditor | Enterprise",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = "http://127.0.0.1:8000"

# ── Session defaults ──────────────────────────────────────────────────────────
defaults = {
    "audit_count": 0, "approved_count": 0, "escalated_count": 0,
    "audit_history": [], "last_result": None, "theme": "dark",
    "total_pages": 0, "total_time": 0.0, "show_raw": False,
    "app_loaded": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

theme = st.session_state.theme
is_dark = theme == "dark"

# ── Theme tokens ──────────────────────────────────────────────────────────────
if is_dark:
    BG       = "#07090f"
    BG2      = "#0d1120"
    BG3      = "#111827"
    BORDER   = "#1e293b"
    BORDER2  = "#243352"
    TEXT1    = "#f1f5f9"
    TEXT2    = "#94a3b8"
    TEXT3    = "#475569"
    ACCENT   = "#3b82f6"
    ACCENT2  = "#1d4ed8"
    GREEN    = "#10b981"
    AMBER    = "#f59e0b"
    RED      = "#ef4444"
    PURPLE   = "#8b5cf6"
    HERO_BG  = "linear-gradient(135deg, #080e1c 0%, #0f1e3c 50%, #080e1c 100%)"
    HERO_GLOW= "#1d4ed820"
    CARD_BG  = f"linear-gradient(135deg, {BG2}, {BG3})"
    SB_BG    = f"linear-gradient(180deg, {BG} 0%, #0a1020 100%)"
    INPUT_BG = BG2
    UPLOAD_BG= BG2
    UPLOAD_BD= f"{ACCENT}55"
    SHADOW   = "0 4px 24px rgba(0,0,0,0.5)"
else:
    BG       = "#f0f4ff"
    BG2      = "#ffffff"
    BG3      = "#f8faff"
    BORDER   = "#dde3f0"
    BORDER2  = "#b8c5e0"
    TEXT1    = "#0f172a"
    TEXT2    = "#334155"
    TEXT3    = "#64748b"
    ACCENT   = "#2563eb"
    ACCENT2  = "#1d4ed8"
    GREEN    = "#059669"
    AMBER    = "#d97706"
    RED      = "#dc2626"
    PURPLE   = "#7c3aed"
    HERO_BG  = "linear-gradient(135deg, #dbeafe 0%, #eff6ff 50%, #dbeafe 100%)"
    HERO_GLOW= "#3b82f620"
    CARD_BG  = f"linear-gradient(135deg, {BG2}, {BG3})"
    SB_BG    = f"linear-gradient(180deg, {BG2} 0%, #f0f4ff 100%)"
    INPUT_BG = BG3
    UPLOAD_BG= BG3
    UPLOAD_BD= f"{ACCENT}66"
    SHADOW   = "0 4px 24px rgba(37,99,235,0.1)"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    background: {BG} !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: {TEXT1} !important;
    transition: background 0.3s ease, color 0.3s ease;
}}

/* ── Loader overlay ── */
#loader-overlay {{
    position: fixed; inset: 0; z-index: 99999;
    background: {BG};
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    transition: opacity 0.6s ease;
}}
.loader-logo {{ font-size: 3.5rem; margin-bottom: 1rem; animation: pulse-icon 1.5s ease infinite; }}
.loader-title {{
    font-family: 'Sora', sans-serif;
    font-size: 1.6rem; font-weight: 800;
    color: {TEXT1}; margin-bottom: 0.4rem;
}}
.loader-sub {{ font-size: 0.85rem; color: {TEXT3}; margin-bottom: 2rem; }}
.loader-bar-outer {{
    width: 260px; height: 4px;
    background: {BORDER}; border-radius: 4px; overflow: hidden;
}}
.loader-bar-inner {{
    height: 4px; border-radius: 4px;
    background: linear-gradient(90deg, {ACCENT2}, {ACCENT}, #60a5fa);
    animation: loader-fill 2.2s ease forwards;
}}
@keyframes loader-fill {{
    0%   {{ width: 0%; }}
    60%  {{ width: 80%; }}
    100% {{ width: 100%; }}
}}
@keyframes pulse-icon {{ 0%,100% {{ transform:scale(1); }} 50% {{ transform:scale(1.1); }} }}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {ACCENT}55; border-radius: 3px; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {SB_BG} !important;
    border-right: 1px solid {BORDER} !important;
    min-width: 270px !important; max-width: 270px !important;
}}
section[data-testid="stSidebar"] > div {{ padding: 0 !important; }}

/* ── Main ── */
.main .block-container {{ padding: 1.5rem 2.2rem !important; max-width: 1400px !important; }}

/* ── Hero ── */
.hero-wrap {{
    background: {HERO_BG};
    border: 1px solid {BORDER2};
    border-radius: 22px; padding: 2.4rem 2.8rem;
    margin-bottom: 1.8rem; position: relative; overflow: hidden;
    box-shadow: {SHADOW};
}}
.hero-wrap::after {{
    content: '';
    position: absolute; top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, {HERO_GLOW} 0%, transparent 70%);
    border-radius: 50%; pointer-events: none;
}}
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.2em;
    color: {ACCENT}; text-transform: uppercase; margin-bottom: 0.7rem;
    display: flex; align-items: center; gap: 0.5rem;
}}
.hero-title {{
    font-family: 'Sora', sans-serif;
    font-size: 2.2rem; font-weight: 800; color: {TEXT1};
    line-height: 1.2; margin-bottom: 0.6rem;
}}
.hero-title .hl {{ color: {ACCENT}; }}
.hero-sub {{ color: {TEXT2}; font-size: 0.93rem; line-height: 1.65; max-width: 580px; }}
.hero-badges {{ display: flex; gap: 0.45rem; margin-top: 1.2rem; flex-wrap: wrap; }}
.hero-badge {{
    background: {"rgba(59,130,246,0.12)" if is_dark else "rgba(37,99,235,0.08)"};
    border: 1px solid {"#3b82f630" if is_dark else "#2563eb25"};
    color: {ACCENT}; font-size: 0.71rem; font-weight: 600;
    padding: 0.28rem 0.8rem; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace; letter-spacing: 0.04em;
    transition: all 0.2s;
}}
.hero-badge:hover {{ background: {"rgba(59,130,246,0.2)" if is_dark else "rgba(37,99,235,0.14)"}; }}

/* ── KPI cards ── */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 1.8rem; }}
.kpi-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 16px; padding: 1.3rem 1.5rem;
    position: relative; overflow: hidden;
    transition: transform 0.2s, border-color 0.2s;
    box-shadow: {SHADOW};
}}
.kpi-card:hover {{ transform: translateY(-3px); border-color: {BORDER2}; }}
.kpi-accent {{ position: absolute; top:0; left:0; width:3px; height:100%; border-radius:16px 0 0 16px; }}
.kpi-val {{
    font-family: 'Sora', sans-serif;
    font-size: 2.1rem; font-weight: 800; color: {TEXT1}; line-height: 1;
}}
.kpi-label {{ font-size: 0.73rem; color: {TEXT3}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.35rem; }}
.kpi-sub {{ font-size: 0.75rem; color: {TEXT3}; margin-top: 0.5rem; }}

/* ── Section head ── */
.sec-head {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.2em;
    color: {TEXT3}; text-transform: uppercase;
    border-bottom: 1px solid {BORDER}; padding-bottom: 0.5rem; margin-bottom: 1rem;
}}

/* ── Upload ── */
.upload-shell {{
    background: {UPLOAD_BG}; border: 1.5px dashed {UPLOAD_BD};
    border-radius: 16px; padding: 1.5rem;
    transition: border-color 0.2s, background 0.2s;
}}
.upload-shell:hover {{ border-color: {ACCENT}; }}
div[data-testid="stFileUploader"] label {{ color: {TEXT2} !important; font-size: 0.88rem !important; font-family:'Space Grotesk',sans-serif !important; }}
div[data-testid="stFileUploader"] section {{ background: transparent !important; border: none !important; }}
div[data-testid="stFileUploader"] button {{
    background: {"rgba(59,130,246,0.12)" if is_dark else "rgba(37,99,235,0.08)"} !important;
    color: {ACCENT} !important; border: 1px solid {BORDER2} !important;
    border-radius: 8px !important; font-size: 0.82rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}

/* ── File chips ── */
.file-chips {{ display:flex; flex-wrap:wrap; gap:0.5rem; margin: 0.8rem 0; }}
.file-chip {{
    background: {"rgba(59,130,246,0.1)" if is_dark else "#eff6ff"};
    border: 1px solid {BORDER2};
    border-radius: 8px; padding: 0.35rem 0.9rem;
    font-size: 0.78rem; color: {ACCENT};
    font-family: 'JetBrains Mono', monospace;
}}

/* ── Buttons ── */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {ACCENT2}, {ACCENT}) !important;
    color: white !important; font-weight: 700 !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.75rem 2rem !important; font-size: 0.92rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    box-shadow: 0 4px 20px {"#1d4ed850" if is_dark else "#2563eb35"} !important;
    transition: all 0.2s !important;
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px {"#2563eb60" if is_dark else "#2563eb45"} !important;
}}
.stButton > button:not([kind="primary"]) {{
    background: {"rgba(255,255,255,0.04)" if is_dark else BG3} !important;
    color: {TEXT2} !important; border: 1px solid {BORDER} !important;
    border-radius: 8px !important; font-size: 0.82rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: all 0.2s !important;
}}
.stButton > button:not([kind="primary"]):hover {{
    border-color: {ACCENT} !important; color: {ACCENT} !important;
}}

/* ── Result cards ── */
.result-card {{
    border-radius: 18px; padding: 2rem;
    margin: 1.2rem 0; position: relative; overflow: hidden;
    box-shadow: {SHADOW};
}}
.result-card.approved {{
    background: {"linear-gradient(135deg,#042715,#054d2a)" if is_dark else "linear-gradient(135deg,#f0fdf4,#dcfce7)"};
    border: 1.5px solid {"#10b98155" if is_dark else "#86efac"};
}}
.result-card.escalate {{
    background: {"linear-gradient(135deg,#1a0f00,#2d1a00)" if is_dark else "linear-gradient(135deg,#fffbeb,#fef3c7)"};
    border: 1.5px solid {"#f59e0b55" if is_dark else "#fcd34d"};
}}
.result-title {{
    font-family: 'Sora', sans-serif;
    font-size: 1.1rem; font-weight: 700; margin-bottom: 0.6rem;
}}
.result-card.approved .result-title {{ color: {"#34d399" if is_dark else "#059669"}; }}
.result-card.escalate .result-title {{ color: {"#fbbf24" if is_dark else "#d97706"}; }}
.result-body {{ color: {TEXT2}; font-size: 0.88rem; line-height: 1.85; white-space: pre-wrap; }}

/* ── Pill ── */
.pill {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.35rem 1.1rem; border-radius: 30px;
    font-size: 0.8rem; font-weight: 700; letter-spacing: 0.04em; margin-bottom: 1rem;
    font-family: 'Space Grotesk', sans-serif;
}}
.pill.green {{ background: {"#10b98122" if is_dark else "#d1fae5"}; color: {"#34d399" if is_dark else "#065f46"}; border: 1px solid {"#10b98155" if is_dark else "#6ee7b7"}; }}
.pill.amber {{ background: {"#f59e0b22" if is_dark else "#fef3c7"}; color: {"#fbbf24" if is_dark else "#92400e"}; border: 1px solid {"#f59e0b55" if is_dark else "#fcd34d"}; }}

/* ── Metric boxes ── */
.mbox-row {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 0.8rem; margin: 1.2rem 0; }}
.mbox {{
    background: {BG2}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 1rem; text-align: center;
    box-shadow: {SHADOW};
}}
.mbox .mv {{
    font-family: 'Sora', sans-serif;
    font-size: 1.6rem; font-weight: 800; color: {ACCENT};
}}
.mbox .ml {{ font-size: 0.68rem; color: {TEXT3}; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.2rem; }}

/* ── Conf bar ── */
.cbar-wrap {{ margin: 0.8rem 0; }}
.cbar-labels {{ display:flex; justify-content:space-between; font-size:0.75rem; color:{TEXT3}; margin-bottom:0.35rem; font-family:'JetBrains Mono',monospace; }}
.cbar-outer {{ background:{BORDER}; border-radius:10px; height:6px; overflow:hidden; }}
.cbar-inner {{ height:6px; border-radius:10px; transition: width 1s ease; }}

/* ── Flag ── */
.flag-item {{
    background: {"rgba(245,158,11,0.08)" if is_dark else "#fffbeb"};
    border-left: 3px solid {AMBER};
    border-radius: 0 8px 8px 0; padding: 0.65rem 1rem;
    margin-bottom: 0.5rem; font-size: 0.84rem;
    color: {"#fcd34d" if is_dark else "#92400e"};
}}

/* ── Check rows ── */
.chk-row {{ display:flex; align-items:center; gap:0.6rem; padding:0.3rem 0; font-size:0.82rem; color:{TEXT2}; }}
.chk-ok  {{ color:{GREEN}; font-weight:700; }}
.chk-no  {{ color:{RED};   font-weight:700; }}

/* ── History row ── */
.hist-row {{ display:grid; grid-template-columns:60px 1fr 100px 80px 70px; gap:0.5rem; padding:0.55rem 1rem; border-radius:8px; margin-bottom:0.25rem; font-size:0.79rem; align-items:center; }}
.hist-head {{ background:{BG2}; color:{TEXT3}; font-weight:700; font-size:0.69rem; text-transform:uppercase; letter-spacing:0.1em; border:1px solid {BORDER}; }}
.hist-body {{ background:{BG3}; border:1px solid {BORDER}; color:{TEXT2}; transition:background 0.15s; }}
.hist-body:hover {{ background:{BG2}; }}
.b-ok  {{ color:{GREEN}; font-weight:700; }}
.b-esc {{ color:{AMBER}; font-weight:700; }}

/* ── Sidebar elements ── */
.sb-wrap {{ padding:0; }}
.sb-logo {{ padding:1.5rem 1.2rem 1rem; border-bottom:1px solid {BORDER}; }}
.sb-logo-title {{ font-family:'Sora',sans-serif; font-size:1.05rem; font-weight:800; color:{TEXT1}; }}
.sb-logo-sub   {{ font-size:0.72rem; color:{TEXT3}; margin-top:0.2rem; }}
.sb-sec {{ padding:0.9rem 1.2rem; border-bottom:1px solid {"#1e293b22" if is_dark else "#dde3f066"}; }}
.sb-title {{ font-family:'JetBrains Mono',monospace; font-size:0.66rem; font-weight:700; color:{TEXT3}; text-transform:uppercase; letter-spacing:0.18em; margin-bottom:0.7rem; }}
.sb-row {{ display:flex; justify-content:space-between; align-items:center; padding:0.28rem 0; }}
.sb-lbl {{ font-size:0.8rem; color:{TEXT3}; }}
.sb-val {{ font-size:0.8rem; font-weight:700; color:{ACCENT}; font-family:'JetBrains Mono',monospace; }}
.sb-info {{ display:flex; align-items:flex-start; gap:0.45rem; padding:0.22rem 0; font-size:0.78rem; color:{TEXT3}; }}
.dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:0.35rem; }}
.dot.on  {{ background:{GREEN}; box-shadow:0 0 6px {GREEN}; }}
.dot.off {{ background:{RED};   box-shadow:0 0 6px {RED}; }}

/* ── Clock ── */
.clock-box {{
    background: {"rgba(59,130,246,0.08)" if is_dark else "#eff6ff"};
    border: 1px solid {BORDER2};
    border-radius: 10px; padding: 0.7rem 1rem;
    text-align: center; margin: 0.5rem 0;
}}
.clock-time {{ font-family:'JetBrains Mono',monospace; font-size:1.4rem; font-weight:700; color:{ACCENT}; letter-spacing:0.1em; }}
.clock-date {{ font-size:0.72rem; color:{TEXT3}; margin-top:0.15rem; }}

/* ── Info box ── */
.info-box {{
    background: {BG2}; border:1px solid {BORDER};
    border-radius:12px; padding:1rem 1.2rem;
    font-size:0.82rem; color:{TEXT2}; line-height:1.75;
    box-shadow: {SHADOW};
}}
.info-box b {{ color:{ACCENT}; }}

/* ── Raw ── */
.raw-out {{
    background:{BG}; border:1px solid {BORDER};
    border-radius:10px; padding:1.2rem;
    font-family:'JetBrains Mono',monospace;
    font-size:0.77rem; color:{TEXT2}; line-height:1.8;
    white-space:pre-wrap; max-height:280px; overflow-y:auto;
}}

/* ── Download buttons ── */
.stDownloadButton > button {{
    background: {"rgba(59,130,246,0.1)" if is_dark else "#eff6ff"} !important;
    color: {ACCENT} !important; border: 1px solid {BORDER2} !important;
    border-radius: 8px !important; font-size: 0.82rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    transition: all 0.2s !important;
}}
.stDownloadButton > button:hover {{ background: {ACCENT} !important; color:white !important; }}

/* ── Tabs ── */
div[data-baseweb="tab-list"] {{
    background: {BG2} !important; border-radius: 10px !important;
    border: 1px solid {BORDER} !important; padding: 3px !important;
}}
div[data-baseweb="tab"] {{ color: {TEXT3} !important; font-size: 0.82rem !important; font-weight: 600 !important; font-family:'Space Grotesk',sans-serif !important; }}
div[data-baseweb="tab"][aria-selected="true"] {{ color: {ACCENT} !important; background: {"rgba(59,130,246,0.15)" if is_dark else "#dbeafe"} !important; border-radius: 8px !important; }}
div[data-baseweb="tab-highlight"] {{ background: transparent !important; }}

/* ── Expander ── */
details {{ background: {BG2} !important; border: 1px solid {BORDER} !important; border-radius: 12px !important; }}
summary {{ color: {TEXT2} !important; font-size: 0.83rem !important; padding: 0.7rem 1rem !important; font-family:'Space Grotesk',sans-serif !important; }}

/* ── Checkbox ── */
.stCheckbox label {{ font-size:0.82rem !important; color:{TEXT2} !important; font-family:'Space Grotesk',sans-serif !important; }}

/* ── Spinner ── */
.stSpinner > div {{ border-top-color: {ACCENT} !important; }}

/* ── Footer ── */
.footer {{
    background: {BG2}; border-top: 1px solid {BORDER};
    border-radius: 16px; padding: 1.5rem 2rem;
    text-align: center; margin-top: 3rem;
    box-shadow: {SHADOW};
}}
.footer-name {{ font-family:'Sora',sans-serif; font-size:1rem; font-weight:800; color:{ACCENT}; }}
.footer-role {{ font-size:0.78rem; color:{TEXT3}; margin-top:0.25rem; }}
.footer-tags {{ display:flex; justify-content:center; gap:0.45rem; margin-top:0.7rem; flex-wrap:wrap; }}
.footer-tag {{
    background: {"rgba(59,130,246,0.08)" if is_dark else "#eff6ff"};
    border: 1px solid {BORDER2}; color: {TEXT3};
    font-size:0.68rem; padding:0.2rem 0.65rem;
    border-radius:10px; font-family:'JetBrains Mono',monospace;
}}

/* ── Hide defaults ── */
#MainMenu, footer, header {{ visibility: hidden !important; }}
.stDeployButton {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ── Loader (first load only) ──────────────────────────────────────────────────
if not st.session_state.app_loaded:
    st.markdown(f"""
    <div id="loader-overlay">
        <div class="loader-logo">🏦</div>
        <div class="loader-title">MortgageAI Auditor</div>
        <div class="loader-sub">Initializing enterprise compliance engine...</div>
        <div class="loader-bar-outer"><div class="loader-bar-inner"></div></div>
    </div>
    <script>
        setTimeout(function() {{
            var el = document.getElementById('loader-overlay');
            if(el) {{ el.style.opacity='0'; setTimeout(()=>el.remove(), 600); }}
        }}, 2400);
    </script>
    """, unsafe_allow_html=True)
    time.sleep(0.1)
    st.session_state.app_loaded = True

# ── Backend health ────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def check_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

health_data  = check_backend()
backend_ok   = health_data is not None
approval_rate = int((st.session_state.approved_count / st.session_state.audit_count) * 100) if st.session_state.audit_count > 0 else 0
avg_time      = (st.session_state.total_time / st.session_state.audit_count) if st.session_state.audit_count > 0 else 0.0

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div class="sb-logo">
        <div style="font-size:1.8rem;margin-bottom:0.4rem">🏦</div>
        <div class="sb-logo-title">MortgageAI Auditor</div>
        <div class="sb-logo-sub">Enterprise Compliance Engine v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    # Live clock
    now = datetime.now()
    st.markdown(f"""
    <div class="sb-sec">
        <div class="sb-title">System Clock</div>
        <div class="clock-box">
            <div class="clock-time">{now.strftime('%H:%M:%S')}</div>
            <div class="clock-date">{now.strftime('%A, %d %B %Y')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle
    st.markdown('<div class="sb-sec"><div class="sb-title">Appearance</div>', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🌙 Dark", use_container_width=True):
            st.session_state.theme = "dark"
            st.rerun()
    with col_t2:
        if st.button("☀️ Light", use_container_width=True):
            st.session_state.theme = "light"
            st.rerun()
    active_label = f"{'🌙 Dark' if is_dark else '☀️ Light'} mode active"
    st.markdown(f'<div style="font-size:0.72rem;color:{TEXT3};text-align:center;padding:0.3rem 0">{active_label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Backend status
    st.markdown('<div class="sb-sec"><div class="sb-title">System Status</div>', unsafe_allow_html=True)
    if backend_ok:
        st.markdown(f"""
        <div class="sb-row"><span class="sb-lbl"><span class="dot on"></span>Backend API</span><span class="sb-val" style="color:{GREEN}">ONLINE</span></div>
        <div class="sb-row"><span class="sb-lbl">Model</span><span class="sb-val">{health_data.get('model','grok-2')}</span></div>
        <div class="sb-row"><span class="sb-lbl">API Key</span><span class="sb-val" style="color:{GREEN}">✓ Loaded</span></div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="sb-row"><span class="sb-lbl"><span class="dot off"></span>Backend API</span><span class="sb-val" style="color:{RED}">OFFLINE</span></div>
        <div style="font-size:0.74rem;color:{RED}88;margin-top:0.4rem;padding:0.5rem;background:{"#1c000088" if is_dark else "#fee2e2"};border-radius:6px;">
        Run: <code>uvicorn main:app --reload</code>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Session stats
    st.markdown(f"""
    <div class="sb-sec">
        <div class="sb-title">Session Analytics</div>
        <div class="sb-row"><span class="sb-lbl">Total Audits</span><span class="sb-val">{st.session_state.audit_count}</span></div>
        <div class="sb-row"><span class="sb-lbl">✅ Approved</span><span class="sb-val" style="color:{GREEN}">{st.session_state.approved_count}</span></div>
        <div class="sb-row"><span class="sb-lbl">⚠️ Escalated</span><span class="sb-val" style="color:{AMBER}">{st.session_state.escalated_count}</span></div>
        <div class="sb-row"><span class="sb-lbl">Approval Rate</span><span class="sb-val">{approval_rate}%</span></div>
        <div class="sb-row"><span class="sb-lbl">Avg Speed</span><span class="sb-val">{avg_time:.1f}s</span></div>
        <div class="sb-row"><span class="sb-lbl">Pages Scanned</span><span class="sb-val">{st.session_state.total_pages}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Architecture
    st.markdown(f"""
    <div class="sb-sec">
        <div class="sb-title">Architecture</div>
        <div class="sb-info">🌐 <span>Streamlit Frontend :8501</span></div>
        <div class="sb-info">⚙️ <span>FastAPI + Uvicorn :8000</span></div>
        <div class="sb-info">🤖 <span>xAI Grok-2-1212</span></div>
        <div class="sb-info">🔒 <span>PII Auto-redacted</span></div>
        <div class="sb-info">📋 <span>TILA / RESPA / ECOA</span></div>
        <div class="sb-info">📂 <span>PDF + DOCX Support</span></div>
        <div class="sb-info">📦 <span>Up to 50 files / batch</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Options
    st.markdown(f'<div class="sb-sec"><div class="sb-title">Options</div>', unsafe_allow_html=True)
    st.session_state.show_raw = st.checkbox("Show raw AI output", value=st.session_state.show_raw)
    if st.button("🔄 Reset Session", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════

# Hero
st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-eyebrow">⬡ Fintech AI &nbsp;·&nbsp; Mortgage Compliance</div>
    <div class="hero-title">Automated Mortgage <span class="hl">Document Auditor</span></div>
    <div class="hero-sub">
        Enterprise-grade AI compliance pipeline. Upload mortgage PDFs or Word documents — 
        up to 50 files at once — and get instant risk assessment, PII protection, 
        and regulatory flag detection powered by xAI Grok-2.
    </div>
    <div class="hero-badges">
        <span class="hero-badge">Streamlit :8501</span>
        <span class="hero-badge">FastAPI :8000</span>
        <span class="hero-badge">Grok-2-1212</span>
        <span class="hero-badge">PII-Safe</span>
        <span class="hero-badge">TILA/RESPA</span>
        <span class="hero-badge">PDF + DOCX</span>
        <span class="hero-badge">50-File Batch</span>
        <span class="hero-badge">CORS Secured</span>
        <span class="hero-badge">Auto-Escalation</span>
        <span class="hero-badge">Confidence Scoring</span>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI strip
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-accent" style="background:{ACCENT}"></div>
        <div class="kpi-val">{st.session_state.audit_count}</div>
        <div class="kpi-label">Total Audits Run</div>
        <div class="kpi-sub">↑ This session</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:{GREEN}"></div>
        <div class="kpi-val" style="color:{GREEN}">{st.session_state.approved_count}</div>
        <div class="kpi-label">Documents Approved</div>
        <div class="kpi-sub">{approval_rate}% approval rate</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:{AMBER}"></div>
        <div class="kpi-val" style="color:{AMBER}">{st.session_state.escalated_count}</div>
        <div class="kpi-label">Escalated to Human</div>
        <div class="kpi-sub">Requires review</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-accent" style="background:{PURPLE}"></div>
        <div class="kpi-val" style="color:{PURPLE}">{st.session_state.total_pages}</div>
        <div class="kpi-label">Total Pages Scanned</div>
        <div class="kpi-sub">{avg_time:.1f}s avg processing</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📄 Audit", "📊 History", "ℹ️ How It Works", "⚙️ Debug"])

# ════════════════════════
# TAB 1 — AUDIT
# ════════════════════════
with tab1:
    st.markdown('<p class="sec-head">Document Upload</p>', unsafe_allow_html=True)

    col_up, col_info = st.columns([2, 1])
    with col_up:
        st.markdown('<div class="upload-shell">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drag & drop mortgage documents — PDF or Word (.docx) — up to 50 files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="visible"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if uploaded_files and len(uploaded_files) > 50:
            st.warning("⚠️ Maximum 50 files per batch. First 50 will be processed.")
            uploaded_files = uploaded_files[:50]

    with col_info:
        st.markdown(f"""
        <div class="info-box">
        <b>Accepted Formats</b><br>
        📄 PDF — mortgage applications<br>
        📝 DOCX — Word agreements<br>
        📊 Loan contracts & statements<br>
        🏠 Title deeds & bank docs<br><br>
        <b>Batch:</b> Up to 50 files<br>
        <b>Max Size:</b> 200 MB / file<br>
        <b>Privacy:</b> PII auto-masked<br>
        <b>Output:</b> TXT + JSON report
        </div>
        """, unsafe_allow_html=True)

    if uploaded_files:
        pdf_count  = sum(1 for f in uploaded_files if f.name.lower().endswith(".pdf"))
        docx_count = sum(1 for f in uploaded_files if f.name.lower().endswith(".docx"))
        total_kb   = sum(len(f.getvalue()) for f in uploaded_files) / 1024

        st.markdown(f"""
        <div class="file-chips">
            <span class="file-chip">📦 {len(uploaded_files)} file(s)</span>
            <span class="file-chip">📄 {pdf_count} PDF</span>
            <span class="file-chip">📝 {docx_count} DOCX</span>
            <span class="file-chip">💾 {total_kb:.1f} KB total</span>
            <span class="file-chip">🕐 {datetime.now().strftime('%H:%M:%S')}</span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📁 View {len(uploaded_files)} file(s)"):
            for i, f in enumerate(uploaded_files, 1):
                sz = len(f.getvalue()) / 1024
                icon = "📄" if f.name.lower().endswith(".pdf") else "📝"
                st.markdown(f'<div class="chk-row">{icon} <span style="color:{ACCENT};font-family:JetBrains Mono,monospace">#{i:02d}</span> {f.name} <span style="color:{TEXT3};margin-left:auto">{sz:.1f} KB</span></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            run_btn = st.button("🚀 Run AI Compliance Audit", type="primary", use_container_width=True, disabled=not backend_ok)
        with c2:
            if st.button("🔍 Preview File List", use_container_width=True):
                st.info(f"{len(uploaded_files)} file(s) ready | {total_kb:.1f} KB total")
        with c3:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.rerun()

        if not backend_ok:
            st.error("🔴 Backend offline. Run: `uvicorn main:app --reload`")

        if run_btn and backend_ok:
            all_results = []

            for file_idx, uploaded_file in enumerate(uploaded_files):
                st.markdown(f"---")
                st.markdown(f'<p class="sec-head">File {file_idx+1}/{len(uploaded_files)}: {uploaded_file.name}</p>', unsafe_allow_html=True)

                prog = st.progress(0, text=f"Starting audit for {uploaded_file.name}...")
                start_ts = time.time()

                steps = [
                    (20, f"📤 Uploading {uploaded_file.name}..."),
                    (40, "🔒 Masking PII data..."),
                    (60, "📋 Running checklist scan..."),
                    (80, "🤖 Grok-2 analyzing..."),
                    (95, "📊 Generating report..."),
                ]

                try:
                    import threading
                    result_holder = {}
                    file_bytes = uploaded_file.getvalue()

                    def call_api():
                        try:
                            files = {"file": (uploaded_file.name, file_bytes, "application/pdf" if uploaded_file.name.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
                            r = requests.post(f"{BACKEND_URL}/audit", files=files, timeout=90)
                            result_holder["response"] = r
                        except Exception as ex:
                            result_holder["error"] = str(ex)

                    t = threading.Thread(target=call_api)
                    t.start()

                    for pct, msg in steps:
                        if not t.is_alive():
                            break
                        prog.progress(pct, text=msg)
                        time.sleep(0.5)

                    t.join()
                    prog.progress(100, text="✅ Complete!")
                    time.sleep(0.2)
                    prog.empty()

                    if "error" in result_holder:
                        raise ConnectionError(result_holder["error"])

                    resp = result_holder["response"]
                    elapsed = round(time.time() - start_ts, 2)

                    if resp.status_code == 200:
                        result     = resp.json()
                        analysis   = result.get("analysis", "")
                        confidence = result.get("confidence") or 0
                        flags      = result.get("flags", [])
                        pages      = result.get("pages_scanned", 0)
                        missing    = result.get("missing_fields", [])
                        is_ok      = "APPROVED" in analysis.upper() and "ESCALATE" not in analysis.upper()

                        st.session_state.audit_count    += 1
                        st.session_state.total_pages    += pages
                        st.session_state.total_time     += elapsed
                        st.session_state.last_result     = analysis
                        if is_ok:
                            st.session_state.approved_count  += 1
                        else:
                            st.session_state.escalated_count += 1

                        st.session_state.audit_history.append({
                            "id": st.session_state.audit_count,
                            "file": uploaded_file.name,
                            "status": "APPROVED" if is_ok else "ESCALATED",
                            "confidence": confidence,
                            "time": elapsed,
                            "pages": pages,
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "flags": len(flags)
                        })
                        all_results.append(result)

                        # Confidence color
                        cc = GREEN if confidence >= 80 else AMBER if confidence >= 60 else RED

                        # Metrics
                        st.markdown(f"""
                        <div class="mbox-row">
                            <div class="mbox"><div class="mv" style="color:{cc}">{confidence}%</div><div class="ml">Confidence</div></div>
                            <div class="mbox"><div class="mv">{elapsed}s</div><div class="ml">Speed</div></div>
                            <div class="mbox"><div class="mv">{pages}</div><div class="ml">Pages</div></div>
                            <div class="mbox"><div class="mv" style="color:{RED if flags else GREEN}">{len(flags)}</div><div class="ml">Flags</div></div>
                        </div>
                        <div class="cbar-wrap">
                            <div class="cbar-labels"><span>Confidence Score</span><span style="color:{cc}">{confidence}%</span></div>
                            <div class="cbar-outer"><div class="cbar-inner" style="width:{confidence}%;background:linear-gradient(90deg,{cc}88,{cc})"></div></div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Result card
                        card_cls = "approved" if is_ok else "escalate"
                        pill_cls = "green"    if is_ok else "amber"
                        verdict  = "✅ APPROVED — Document Compliant" if is_ok else "⚠️ ESCALATED — Human Review Required"

                        st.markdown(f"""
                        <div class="result-card {card_cls}">
                            <span class="pill {pill_cls}">{verdict}</span>
                            <div class="result-body">{analysis}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        if is_ok and len(uploaded_files) == 1:
                            st.balloons()

                        # Checklist
                        all_fields = ["applicant name","date","loan amount","property address","signature","income","employment","bank statement"]
                        with st.expander(f"📋 Field Checklist — {'⚠️ ' + str(len(missing)) + ' missing' if missing else '✓ All present'}"):
                            for f in all_fields:
                                if f in missing:
                                    st.markdown(f'<div class="chk-row"><span class="chk-no">✗</span> {f.title()}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="chk-row"><span class="chk-ok">✓</span> {f.title()}</div>', unsafe_allow_html=True)

                        # Flags
                        if flags:
                            with st.expander(f"🚩 {len(flags)} Compliance Flag(s)"):
                                for i, flag in enumerate(flags, 1):
                                    st.markdown(f'<div class="flag-item"><b>#{i}</b> {flag}</div>', unsafe_allow_html=True)

                        if st.session_state.show_raw:
                            with st.expander("🔍 Raw AI Output"):
                                st.markdown(f'<div class="raw-out">{analysis}</div>', unsafe_allow_html=True)

                        # Download
                        report_txt = f"""MORTGAGEAI AUDITOR — COMPLIANCE REPORT
{'='*52}
File      : {uploaded_file.name}
Date/Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status    : {'APPROVED' if is_ok else 'ESCALATED TO HUMAN'}
Confidence: {confidence}%
Pages     : {pages}
Speed     : {elapsed}s
Flags     : {len(flags)}
{'='*52}

AI ASSESSMENT:
{analysis}

{'='*52}
Missing Fields : {', '.join(missing) if missing else 'None'}
Flags Raised   :
{chr(10).join('  - ' + f for f in flags) if flags else '  None'}
{'='*52}
Developed by Agha Wafa Abbas | ML Engineer Consultant
University of Portsmouth | Arden University
"""
                        d1, d2 = st.columns(2)
                        with d1:
                            st.download_button("⬇️ Report (.txt)", data=report_txt,
                                file_name=f"audit_{uploaded_file.name.replace('.','_')}.txt",
                                mime="text/plain", use_container_width=True)
                        with d2:
                            st.download_button("⬇️ Data (.json)", data=json.dumps(result, indent=2),
                                file_name=f"audit_{uploaded_file.name.replace('.','_')}.json",
                                mime="application/json", use_container_width=True)
                    else:
                        err = resp.json().get("detail", "Unknown error.")
                        st.error(f"❌ Error {resp.status_code}: {err}")

                except ConnectionError as e:
                    st.error(f"🔴 Cannot reach backend: {e}")
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")
    else:
        st.markdown(f"""
        <div style="background:{BG2};border:1.5px dashed {BORDER2};border-radius:16px;padding:3rem 2rem;text-align:center;color:{TEXT3};margin-top:1rem;">
            <div style="font-size:3rem;margin-bottom:0.8rem">📄</div>
            <div style="font-size:1.1rem;font-weight:700;color:{TEXT2};font-family:Sora,sans-serif">Upload documents to begin</div>
            <div style="font-size:0.84rem;margin-top:0.4rem">Supports PDF & DOCX · Up to 50 files per batch</div>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════
# TAB 2 — HISTORY
# ════════════════════════
with tab2:
    st.markdown('<p class="sec-head">Audit History — This Session</p>', unsafe_allow_html=True)
    if st.session_state.audit_history:
        st.markdown(f'<div class="hist-row hist-head"><span>#</span><span>File</span><span>Status</span><span>Conf.</span><span>Time</span></div>', unsafe_allow_html=True)
        for row in reversed(st.session_state.audit_history):
            bc  = "b-ok"  if row["status"] == "APPROVED" else "b-esc"
            btx = "✅ OK" if row["status"] == "APPROVED" else "⚠️ ESC"
            st.markdown(f"""
            <div class="hist-row hist-body">
                <span style="color:{TEXT3}">#{row['id']}</span>
                <span style="font-size:0.78rem">{row['file'][:28]}</span>
                <span class="{bc}">{btx}</span>
                <span style="font-family:'JetBrains Mono',monospace">{row['confidence']}%</span>
                <span style="color:{TEXT3}">{row['time']}s</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        h = st.session_state.audit_history
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Confidence", f"{int(sum(r['confidence'] for r in h)/len(h))}%")
        c2.metric("Total Time",     f"{sum(r['time'] for r in h):.1f}s")
        c3.metric("Total Flags",    sum(r['flags'] for r in h))
    else:
        st.info("No audits yet this session.")

# ════════════════════════
# TAB 3 — HOW IT WORKS
# ════════════════════════
with tab3:
    st.markdown('<p class="sec-head">System Architecture</p>', unsafe_allow_html=True)
    for step, title, body in [
        ("01", "Upload",       "PDF or DOCX uploaded via Streamlit (:8501) and sent via HTTP multipart POST to FastAPI backend (:8000)."),
        ("02", "Text Extract", "PyPDF handles PDF text extraction. python-docx handles Word document parsing."),
        ("03", "PII Masking",  "SSNs, credit card numbers, phone numbers, emails and account numbers are auto-redacted before AI processing."),
        ("04", "Checklist",    "8 required mortgage fields are verified: Applicant Name, Date, Loan Amount, Property Address, Signature, Income, Employment, Bank Statement."),
        ("05", "Grok-2 AI",    "Redacted text is sent to xAI Grok-2-1212 with a structured compliance prompt. Returns STATUS, CONFIDENCE, REASON, FLAGS, RECOMMENDATION."),
        ("06", "Risk Engine",  "Auto-escalation fires if confidence < 70%. All flags parsed and categorized. Missing fields added as compliance flags."),
        ("07", "Report",       "Full audit reports available for TXT and JSON download. Session analytics tracked across all audits."),
    ]:
        st.markdown(f"""
        <div style="display:flex;gap:1.2rem;align-items:flex-start;background:{BG2};border:1px solid {BORDER};border-radius:12px;padding:1rem 1.2rem;margin-bottom:0.6rem;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:1.2rem;font-weight:800;color:{ACCENT};min-width:36px">{step}</div>
            <div><div style="font-weight:700;color:{TEXT1};margin-bottom:0.25rem">{title}</div>
            <div style="font-size:0.83rem;color:{TEXT2};line-height:1.65">{body}</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<p class="sec-head" style="margin-top:1.5rem">Compliance Standards</p>', unsafe_allow_html=True)
    for law, desc in [
        ("TILA",  "Truth in Lending Act — APR, total payments, finance charges disclosure"),
        ("RESPA", "Real Estate Settlement Procedures — kickbacks and fee disclosures"),
        ("ECOA",  "Equal Credit Opportunity Act — no discriminatory lending"),
        ("HMDA",  "Home Mortgage Disclosure Act — demographic reporting"),
        ("FCRA",  "Fair Credit Reporting Act — credit data accuracy"),
    ]:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;background:{BG2};border:1px solid {BORDER};border-radius:8px;padding:0.7rem 1rem;margin-bottom:0.4rem;">
            <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{ACCENT};min-width:50px">{law}</span>
            <span style="font-size:0.82rem;color:{TEXT2}">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════
# TAB 4 — DEBUG
# ════════════════════════
with tab4:
    st.markdown('<p class="sec-head">Backend Debug Console</p>', unsafe_allow_html=True)
    if st.button("🔁 Re-check Health"):
        st.cache_data.clear()
        st.rerun()
    if backend_ok:
        st.markdown(f'<div class="raw-out">{json.dumps(health_data, indent=2)}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="raw-out">❌ Cannot reach http://127.0.0.1:8000/health

Fix checklist:
  [ ] Run: uvicorn main:app --reload
  [ ] Activate venv: .\\venv\\Scripts\\activate
  [ ] Check .env has GROK_API_KEY set
  [ ] Check main.py has no import errors

Expected /health response:
{{
  "status": "online",
  "model": "grok-2-latest",
  "api_key_loaded": true
}}</div>""", unsafe_allow_html=True)

    st.markdown('<p class="sec-head" style="margin-top:1.5rem">Last Audit Output</p>', unsafe_allow_html=True)
    if st.session_state.last_result:
        st.markdown(f'<div class="raw-out">{st.session_state.last_result}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="raw-out">No audit run yet this session.</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    <div class="footer-name">⚡ Developed by Agha Wafa Abbas</div>
    <div class="footer-role">ML Engineer Consultant &nbsp;·&nbsp; AI/ML Researcher &nbsp;·&nbsp; University of Portsmouth &nbsp;·&nbsp; Arden University</div>
    <div class="footer-tags">
        <span class="footer-tag">FastAPI</span>
        <span class="footer-tag">Streamlit</span>
        <span class="footer-tag">xAI Grok-2</span>
        <span class="footer-tag">Python</span>
        <span class="footer-tag">NLP</span>
        <span class="footer-tag">Fintech AI</span>
        <span class="footer-tag">Compliance AI</span>
        <span class="footer-tag">PII Protection</span>
        <span class="footer-tag">Batch Processing</span>
    </div>
</div>
""", unsafe_allow_html=True)