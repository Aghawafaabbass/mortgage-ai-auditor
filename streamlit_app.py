import streamlit as st
import time
import json
import re
import io
from datetime import datetime

st.set_page_config(
    page_title="MortgageAI Auditor | Enterprise",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Imports with graceful fallback ────────────────────────────────────────────
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDoc
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ── Session defaults ──────────────────────────────────────────────────────────
defaults = {
    "audit_count": 0, "approved_count": 0, "escalated_count": 0,
    "audit_history": [], "last_result": None, "theme": "dark",
    "total_pages": 0, "total_time": 0.0, "show_raw": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

theme = st.session_state.theme
is_dark = theme == "dark"

if is_dark:
    BG="#07090f"; BG2="#0d1120"; BG3="#111827"; BORDER="#1e293b"; BORDER2="#243352"
    TEXT1="#f1f5f9"; TEXT2="#94a3b8"; TEXT3="#475569"
    ACCENT="#3b82f6"; ACCENT2="#1d4ed8"; GREEN="#10b981"; AMBER="#f59e0b"; RED="#ef4444"; PURPLE="#8b5cf6"
    HERO_BG="linear-gradient(135deg,#080e1c 0%,#0f1e3c 50%,#080e1c 100%)"
    CARD_BG=f"linear-gradient(135deg,{BG2},{BG3})"; SB_BG=f"linear-gradient(180deg,{BG} 0%,#0a1020 100%)"
    SHADOW="0 4px 24px rgba(0,0,0,0.5)"
else:
    BG="#f0f4ff"; BG2="#ffffff"; BG3="#f8faff"; BORDER="#dde3f0"; BORDER2="#b8c5e0"
    TEXT1="#0f172a"; TEXT2="#334155"; TEXT3="#64748b"
    ACCENT="#2563eb"; ACCENT2="#1d4ed8"; GREEN="#059669"; AMBER="#d97706"; RED="#dc2626"; PURPLE="#7c3aed"
    HERO_BG="linear-gradient(135deg,#dbeafe 0%,#eff6ff 50%,#dbeafe 100%)"
    CARD_BG=f"linear-gradient(135deg,{BG2},{BG3})"; SB_BG=f"linear-gradient(180deg,{BG2} 0%,#f0f4ff 100%)"
    SHADOW="0 4px 24px rgba(37,99,235,0.1)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body,.stApp{{background:{BG}!important;font-family:'Space Grotesk',sans-serif!important;color:{TEXT1}!important;transition:background 0.3s,color 0.3s}}
::-webkit-scrollbar{{width:5px}}::-webkit-scrollbar-track{{background:{BG}}}::-webkit-scrollbar-thumb{{background:{ACCENT}55;border-radius:3px}}
section[data-testid="stSidebar"]{{background:{SB_BG}!important;border-right:1px solid {BORDER}!important;min-width:270px!important;max-width:270px!important}}
section[data-testid="stSidebar"]>div{{padding:0!important}}
.main .block-container{{padding:1.5rem 2.2rem!important;max-width:1400px!important}}
.hero-wrap{{background:{HERO_BG};border:1px solid {BORDER2};border-radius:22px;padding:2.2rem 2.6rem;margin-bottom:1.8rem;position:relative;overflow:hidden;box-shadow:{SHADOW}}}
.hero-wrap::after{{content:'';position:absolute;top:-60px;right:-60px;width:280px;height:280px;background:radial-gradient(circle,{"#1d4ed820" if is_dark else "#3b82f615"} 0%,transparent 70%);border-radius:50%;pointer-events:none}}
.hero-eye{{font-family:'JetBrains Mono',monospace;font-size:0.7rem;font-weight:600;letter-spacing:0.2em;color:{ACCENT};text-transform:uppercase;margin-bottom:0.6rem}}
.hero-title{{font-family:'Sora',sans-serif;font-size:2rem;font-weight:800;color:{TEXT1};line-height:1.2;margin-bottom:0.5rem}}
.hero-title .hl{{color:{ACCENT}}}
.hero-sub{{color:{TEXT2};font-size:0.9rem;line-height:1.65;max-width:560px}}
.hero-badges{{display:flex;gap:0.4rem;margin-top:1rem;flex-wrap:wrap}}
.hero-badge{{background:{"rgba(59,130,246,0.12)" if is_dark else "rgba(37,99,235,0.08)"};border:1px solid {"#3b82f630" if is_dark else "#2563eb22"};color:{ACCENT};font-size:0.69rem;font-weight:600;padding:0.25rem 0.75rem;border-radius:20px;font-family:'JetBrains Mono',monospace}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.8rem}}
.kpi-card{{background:{CARD_BG};border:1px solid {BORDER};border-radius:16px;padding:1.2rem 1.4rem;position:relative;overflow:hidden;transition:transform 0.2s;box-shadow:{SHADOW}}}
.kpi-card:hover{{transform:translateY(-2px)}}
.kpi-accent{{position:absolute;top:0;left:0;width:3px;height:100%;border-radius:16px 0 0 16px}}
.kpi-val{{font-family:'Sora',sans-serif;font-size:2rem;font-weight:800;color:{TEXT1};line-height:1}}
.kpi-label{{font-size:0.71rem;color:{TEXT3};font-weight:600;text-transform:uppercase;letter-spacing:0.1em;margin-top:0.3rem}}
.kpi-sub{{font-size:0.73rem;color:{TEXT3};margin-top:0.4rem}}
.sec-head{{font-family:'JetBrains Mono',monospace;font-size:0.68rem;font-weight:700;letter-spacing:0.2em;color:{TEXT3};text-transform:uppercase;border-bottom:1px solid {BORDER};padding-bottom:0.45rem;margin-bottom:0.9rem}}
.upload-shell{{background:{"rgba(59,130,246,0.05)" if is_dark else BG3};border:1.5px dashed {"#3b82f655" if is_dark else "#2563eb44"};border-radius:16px;padding:1.4rem;transition:border-color 0.2s}}
.upload-shell:hover{{border-color:{ACCENT}}}
.file-chips{{display:flex;flex-wrap:wrap;gap:0.4rem;margin:0.7rem 0}}
.file-chip{{background:{"rgba(59,130,246,0.1)" if is_dark else "#eff6ff"};border:1px solid {BORDER2};border-radius:8px;padding:0.3rem 0.8rem;font-size:0.76rem;color:{ACCENT};font-family:'JetBrains Mono',monospace}}
.stButton>button[kind="primary"]{{background:linear-gradient(135deg,{ACCENT2},{ACCENT})!important;color:white!important;font-weight:700!important;border:none!important;border-radius:10px!important;padding:0.75rem 2rem!important;font-size:0.9rem!important;font-family:'Space Grotesk',sans-serif!important;box-shadow:0 4px 20px {"#1d4ed850" if is_dark else "#2563eb30"}!important;transition:all 0.2s!important}}
.stButton>button[kind="primary"]:hover{{transform:translateY(-2px)!important;box-shadow:0 8px 30px {"#2563eb60" if is_dark else "#2563eb40"}!important}}
.stButton>button:not([kind="primary"]){{background:{"rgba(255,255,255,0.04)" if is_dark else BG3}!important;color:{TEXT2}!important;border:1px solid {BORDER}!important;border-radius:8px!important;font-size:0.8rem!important;font-family:'Space Grotesk',sans-serif!important;transition:all 0.2s!important}}
.result-card{{border-radius:18px;padding:1.8rem;margin:1.2rem 0;box-shadow:{SHADOW}}}
.result-card.approved{{background:{"linear-gradient(135deg,#042715,#054d2a)" if is_dark else "linear-gradient(135deg,#f0fdf4,#dcfce7)"};border:1.5px solid {"#10b98155" if is_dark else "#86efac"}}}
.result-card.escalate{{background:{"linear-gradient(135deg,#1a0f00,#2d1a00)" if is_dark else "linear-gradient(135deg,#fffbeb,#fef3c7)"};border:1.5px solid {"#f59e0b55" if is_dark else "#fcd34d"}}}
.pill{{display:inline-flex;align-items:center;gap:0.4rem;padding:0.3rem 1rem;border-radius:30px;font-size:0.78rem;font-weight:700;letter-spacing:0.04em;margin-bottom:0.8rem}}
.pill.green{{background:{"#10b98122" if is_dark else "#d1fae5"};color:{"#34d399" if is_dark else "#065f46"};border:1px solid {"#10b98155" if is_dark else "#6ee7b7"}}}
.pill.amber{{background:{"#f59e0b22" if is_dark else "#fef3c7"};color:{"#fbbf24" if is_dark else "#92400e"};border:1px solid {"#f59e0b55" if is_dark else "#fcd34d"}}}
.result-body{{color:{TEXT2};font-size:0.86rem;line-height:1.85;white-space:pre-wrap}}
.mbox-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:0.8rem;margin:1rem 0}}
.mbox{{background:{BG2};border:1px solid {BORDER};border-radius:12px;padding:0.9rem;text-align:center;box-shadow:{SHADOW}}}
.mbox .mv{{font-family:'Sora',sans-serif;font-size:1.5rem;font-weight:800;color:{ACCENT}}}
.mbox .ml{{font-size:0.66rem;color:{TEXT3};text-transform:uppercase;letter-spacing:0.1em;margin-top:0.2rem}}
.cbar-wrap{{margin:0.7rem 0}}
.cbar-labels{{display:flex;justify-content:space-between;font-size:0.73rem;color:{TEXT3};margin-bottom:0.3rem;font-family:'JetBrains Mono',monospace}}
.cbar-outer{{background:{BORDER};border-radius:10px;height:5px;overflow:hidden}}
.cbar-inner{{height:5px;border-radius:10px}}
.flag-item{{background:{"rgba(245,158,11,0.08)" if is_dark else "#fffbeb"};border-left:3px solid {AMBER};border-radius:0 8px 8px 0;padding:0.6rem 1rem;margin-bottom:0.4rem;font-size:0.82rem;color:{"#fcd34d" if is_dark else "#92400e"}}}
.chk-row{{display:flex;align-items:center;gap:0.5rem;padding:0.28rem 0;font-size:0.8rem;color:{TEXT2}}}
.chk-ok{{color:{GREEN};font-weight:700}}.chk-no{{color:{RED};font-weight:700}}
.hist-row{{display:grid;grid-template-columns:55px 1fr 100px 75px 65px;gap:0.4rem;padding:0.5rem 0.9rem;border-radius:8px;margin-bottom:0.2rem;font-size:0.77rem;align-items:center}}
.hist-head{{background:{BG2};color:{TEXT3};font-weight:700;font-size:0.67rem;text-transform:uppercase;letter-spacing:0.1em;border:1px solid {BORDER}}}
.hist-body{{background:{BG3};border:1px solid {BORDER};color:{TEXT2}}}
.sb-logo{{padding:1.4rem 1.2rem 0.9rem;border-bottom:1px solid {BORDER}}}
.sb-logo-title{{font-family:'Sora',sans-serif;font-size:1rem;font-weight:800;color:{TEXT1}}}
.sb-logo-sub{{font-size:0.7rem;color:{TEXT3};margin-top:0.2rem}}
.sb-sec{{padding:0.85rem 1.2rem;border-bottom:1px solid {"#1e293b22" if is_dark else "#dde3f044"}}}
.sb-title{{font-family:'JetBrains Mono',monospace;font-size:0.64rem;font-weight:700;color:{TEXT3};text-transform:uppercase;letter-spacing:0.18em;margin-bottom:0.65rem}}
.sb-row{{display:flex;justify-content:space-between;align-items:center;padding:0.25rem 0}}
.sb-lbl{{font-size:0.78rem;color:{TEXT3}}}
.sb-val{{font-size:0.78rem;font-weight:700;color:{ACCENT};font-family:'JetBrains Mono',monospace}}
.dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:0.35rem}}
.dot.on{{background:{GREEN};box-shadow:0 0 6px {GREEN}}}.dot.off{{background:{RED};box-shadow:0 0 6px {RED}}}
.clock-box{{background:{"rgba(59,130,246,0.08)" if is_dark else "#eff6ff"};border:1px solid {BORDER2};border-radius:10px;padding:0.65rem 1rem;text-align:center;margin:0.4rem 0}}
.clock-time{{font-family:'JetBrains Mono',monospace;font-size:1.35rem;font-weight:700;color:{ACCENT};letter-spacing:0.1em}}
.clock-date{{font-size:0.7rem;color:{TEXT3};margin-top:0.12rem}}
.info-box{{background:{BG2};border:1px solid {BORDER};border-radius:12px;padding:0.9rem 1.1rem;font-size:0.8rem;color:{TEXT2};line-height:1.75;box-shadow:{SHADOW}}}
.info-box b{{color:{ACCENT}}}
.raw-out{{background:{BG};border:1px solid {BORDER};border-radius:10px;padding:1.1rem;font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:{TEXT2};line-height:1.8;white-space:pre-wrap;max-height:280px;overflow-y:auto}}
.stDownloadButton>button{{background:{"rgba(59,130,246,0.1)" if is_dark else "#eff6ff"}!important;color:{ACCENT}!important;border:1px solid {BORDER2}!important;border-radius:8px!important;font-size:0.8rem!important;font-family:'Space Grotesk',sans-serif!important;transition:all 0.2s!important}}
.stDownloadButton>button:hover{{background:{ACCENT}!important;color:white!important}}
div[data-baseweb="tab-list"]{{background:{BG2}!important;border-radius:10px!important;border:1px solid {BORDER}!important;padding:3px!important}}
div[data-baseweb="tab"]{{color:{TEXT3}!important;font-size:0.8rem!important;font-weight:600!important;font-family:'Space Grotesk',sans-serif!important}}
div[data-baseweb="tab"][aria-selected="true"]{{color:{ACCENT}!important;background:{"rgba(59,130,246,0.15)" if is_dark else "#dbeafe"}!important;border-radius:8px!important}}
div[data-baseweb="tab-highlight"]{{background:transparent!important}}
details{{background:{BG2}!important;border:1px solid {BORDER}!important;border-radius:12px!important}}
summary{{color:{TEXT2}!important;font-size:0.81rem!important;padding:0.65rem 1rem!important;font-family:'Space Grotesk',sans-serif!important}}
.stCheckbox label{{font-size:0.8rem!important;color:{TEXT2}!important;font-family:'Space Grotesk',sans-serif!important}}
.stSpinner>div{{border-top-color:{ACCENT}!important}}
.footer{{background:{BG2};border-top:1px solid {BORDER};border-radius:16px;padding:1.4rem 2rem;text-align:center;margin-top:3rem;box-shadow:{SHADOW}}}
.footer-name{{font-family:'Sora',sans-serif;font-size:0.95rem;font-weight:800;color:{ACCENT}}}
.footer-role{{font-size:0.75rem;color:{TEXT3};margin-top:0.22rem}}
.footer-tags{{display:flex;justify-content:center;gap:0.4rem;margin-top:0.6rem;flex-wrap:wrap}}
.footer-tag{{background:{"rgba(59,130,246,0.08)" if is_dark else "#eff6ff"};border:1px solid {BORDER2};color:{TEXT3};font-size:0.66rem;padding:0.18rem 0.6rem;border-radius:10px;font-family:'JetBrains Mono',monospace}}
div[data-testid="stFileUploader"] label{{color:{TEXT2}!important;font-size:0.86rem!important;font-family:'Space Grotesk',sans-serif!important}}
div[data-testid="stFileUploader"] section{{background:transparent!important;border:none!important}}
div[data-testid="stFileUploader"] button{{background:{"rgba(59,130,246,0.1)" if is_dark else "#eff6ff"}!important;color:{ACCENT}!important;border:1px solid {BORDER2}!important;border-radius:8px!important;font-size:0.8rem!important}}
#MainMenu,footer,header{{visibility:hidden!important}}
.stDeployButton{{display:none!important}}
</style>
""", unsafe_allow_html=True)

# ── PII masking ───────────────────────────────────────────────────────────────
PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN-REDACTED"),
    (r"\b(?:\d{4}[\s\-]?){3}\d{4}\b", "CARD-REDACTED"),
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "EMAIL-REDACTED"),
    (r"\b(\+?\d[\d\s\-]{7,14}\d)\b", "PHONE-REDACTED"),
    (r"\b\d{9,13}\b", "ACCT-REDACTED"),
]
def mask_pii(text):
    for p, r in PII_PATTERNS:
        text = re.sub(p, r, text)
    return text

REQUIRED_FIELDS = ["applicant name","date","loan amount","property address","signature","income","employment","bank statement"]
def check_missing(text):
    tl = text.lower()
    return [f for f in REQUIRED_FIELDS if f not in tl]

def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        if not PDF_AVAILABLE:
            return None, 0, "pypdf not installed"
        reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
        pages = len(reader.pages)
        text = "".join((p.extract_text() or "") + "\n" for p in reader.pages)
        return text, pages, None
    elif name.endswith(".docx"):
        if not DOCX_AVAILABLE:
            return None, 0, "python-docx not installed"
        doc = DocxDoc(io.BytesIO(uploaded_file.getvalue()))
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paras), max(1, len(paras)//30), None
    return None, 0, "Unsupported file type"

def parse_response(raw):
    confidence = None
    flags = []
    m = re.search(r"CONFIDENCE:\s*(\d+)", raw, re.IGNORECASE)
    if m:
        confidence = int(m.group(1))
    fm = re.search(r"FLAGS?:\s*\n(.*?)(?:\nRECOMMENDATION:|$)", raw, re.DOTALL | re.IGNORECASE)
    if fm:
        flags = [f.lstrip("-• ").strip() for f in fm.group(1).strip().splitlines()
                 if f.strip() and f.strip().upper() not in ("NONE", "-")]
    return confidence, flags

def run_groq_audit(text, missing_fields, api_key):
    missing_str = f"Missing: {', '.join(missing_fields)}" if missing_fields else "All standard fields present."
    prompt = f"""You are a senior fintech compliance AI auditor specializing in US mortgage underwriting.

PRE-SCAN CHECKLIST:
{missing_str}

DOCUMENT TEXT (PII Redacted):
\"\"\"{text[:7000]}\"\"\"

Respond STRICTLY in this exact format:

STATUS: [APPROVED or ESCALATE TO HUMAN]
CONFIDENCE: [0-100]
REASON: [2-3 professional sentences]
FLAGS:
- [flag or NONE]
RECOMMENDATION: [one actionable sentence for loan officer]
"""
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a strict US mortgage compliance auditor. Always respond in the exact structured format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=700
    )
    return resp.choices[0].message.content.strip()

# ── Get API key ───────────────────────────────────────────────────────────────
import os
api_key = os.getenv("GROQ_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = ""

approval_rate = int((st.session_state.approved_count / st.session_state.audit_count) * 100) if st.session_state.audit_count > 0 else 0
avg_time = (st.session_state.total_time / st.session_state.audit_count) if st.session_state.audit_count > 0 else 0.0

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div class="sb-logo">
        <div style="font-size:1.7rem;margin-bottom:0.4rem">🏦</div>
        <div class="sb-logo-title">MortgageAI Auditor</div>
        <div class="sb-logo-sub">Enterprise Compliance Engine v2.0</div>
    </div>""", unsafe_allow_html=True)

    now = datetime.now()
    st.markdown(f"""
    <div class="sb-sec">
        <div class="sb-title">System Clock</div>
        <div class="clock-box">
            <div class="clock-time">{now.strftime('%H:%M:%S')}</div>
            <div class="clock-date">{now.strftime('%A, %d %B %Y')}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-sec"><div class="sb-title">Appearance</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🌙 Dark", use_container_width=True):
            st.session_state.theme = "dark"; st.rerun()
    with c2:
        if st.button("☀️ Light", use_container_width=True):
            st.session_state.theme = "light"; st.rerun()
    st.markdown(f'<div style="font-size:0.7rem;color:{TEXT3};text-align:center;padding:0.25rem 0">{"🌙 Dark" if is_dark else "☀️ Light"} mode active</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    api_status = "✓ Loaded" if api_key else "✗ Missing"
    api_color  = GREEN if api_key else RED
    st.markdown(f"""
    <div class="sb-sec">
        <div class="sb-title">System Status</div>
        <div class="sb-row"><span class="sb-lbl"><span class="dot {"on" if api_key else "off"}"></span>Groq API</span><span class="sb-val" style="color:{api_color}">{"ONLINE" if api_key else "OFFLINE"}</span></div>
        <div class="sb-row"><span class="sb-lbl">Model</span><span class="sb-val">llama-3.3-70b</span></div>
        <div class="sb-row"><span class="sb-lbl">API Key</span><span class="sb-val" style="color:{api_color}">{api_status}</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sb-sec">
        <div class="sb-title">Session Analytics</div>
        <div class="sb-row"><span class="sb-lbl">Total Audits</span><span class="sb-val">{st.session_state.audit_count}</span></div>
        <div class="sb-row"><span class="sb-lbl">✅ Approved</span><span class="sb-val" style="color:{GREEN}">{st.session_state.approved_count}</span></div>
        <div class="sb-row"><span class="sb-lbl">⚠️ Escalated</span><span class="sb-val" style="color:{AMBER}">{st.session_state.escalated_count}</span></div>
        <div class="sb-row"><span class="sb-lbl">Approval Rate</span><span class="sb-val">{approval_rate}%</span></div>
        <div class="sb-row"><span class="sb-lbl">Avg Speed</span><span class="sb-val">{avg_time:.1f}s</span></div>
        <div class="sb-row"><span class="sb-lbl">Pages Scanned</span><span class="sb-val">{st.session_state.total_pages}</span></div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="sb-sec"><div class="sb-title">Options</div>', unsafe_allow_html=True)
    st.session_state.show_raw = st.checkbox("Show raw AI output", value=st.session_state.show_raw)
    if st.button("🔄 Reset Session", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-eye">⬡ Fintech AI · Mortgage Compliance</div>
    <div class="hero-title">Automated Mortgage <span class="hl">Document Auditor</span></div>
    <div class="hero-sub">Enterprise AI compliance pipeline. Upload mortgage PDFs or Word docs — up to 50 files — for instant risk assessment, PII protection, and regulatory flag detection.</div>
    <div class="hero-badges">
        <span class="hero-badge">Groq LLaMA-3.3-70b</span>
        <span class="hero-badge">PII-Safe</span>
        <span class="hero-badge">TILA/RESPA</span>
        <span class="hero-badge">PDF + DOCX</span>
        <span class="hero-badge">50-File Batch</span>
        <span class="hero-badge">Auto-Escalation</span>
        <span class="hero-badge">Confidence Scoring</span>
    </div>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-accent" style="background:{ACCENT}"></div><div class="kpi-val">{st.session_state.audit_count}</div><div class="kpi-label">Total Audits</div><div class="kpi-sub">↑ This session</div></div>
    <div class="kpi-card"><div class="kpi-accent" style="background:{GREEN}"></div><div class="kpi-val" style="color:{GREEN}">{st.session_state.approved_count}</div><div class="kpi-label">Approved</div><div class="kpi-sub">{approval_rate}% rate</div></div>
    <div class="kpi-card"><div class="kpi-accent" style="background:{AMBER}"></div><div class="kpi-val" style="color:{AMBER}">{st.session_state.escalated_count}</div><div class="kpi-label">Escalated</div><div class="kpi-sub">Requires review</div></div>
    <div class="kpi-card"><div class="kpi-accent" style="background:{PURPLE}"></div><div class="kpi-val" style="color:{PURPLE}">{st.session_state.total_pages}</div><div class="kpi-label">Pages Scanned</div><div class="kpi-sub">{avg_time:.1f}s avg</div></div>
</div>""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📄 Audit", "📊 History", "ℹ️ How It Works"])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    if not api_key:
        st.error("⚠️ GROQ_API_KEY missing! Add it in Streamlit Cloud → Settings → Secrets as: `GROQ_API_KEY = 'gsk_...'`")

    st.markdown('<p class="sec-head">Document Upload</p>', unsafe_allow_html=True)
    col_up, col_info = st.columns([2, 1])
    with col_up:
        st.markdown('<div class="upload-shell">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Drag & drop mortgage documents — PDF or Word (.docx) — up to 50 files",
            type=["pdf","docx"], accept_multiple_files=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if uploaded_files and len(uploaded_files) > 50:
            st.warning("Max 50 files. First 50 will be processed.")
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
        </div>""", unsafe_allow_html=True)

    if uploaded_files:
        pdf_c = sum(1 for f in uploaded_files if f.name.lower().endswith(".pdf"))
        docx_c = sum(1 for f in uploaded_files if f.name.lower().endswith(".docx"))
        total_kb = sum(len(f.getvalue()) for f in uploaded_files) / 1024
        st.markdown(f"""
        <div class="file-chips">
            <span class="file-chip">📦 {len(uploaded_files)} file(s)</span>
            <span class="file-chip">📄 {pdf_c} PDF</span>
            <span class="file-chip">📝 {docx_c} DOCX</span>
            <span class="file-chip">💾 {total_kb:.1f} KB total</span>
            <span class="file-chip">🕐 {datetime.now().strftime('%H:%M:%S')}</span>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        with c1:
            run_btn = st.button("🚀 Run AI Compliance Audit", type="primary", use_container_width=True, disabled=not api_key)
        with c2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.rerun()

        if run_btn and api_key:
            for idx, uf in enumerate(uploaded_files):
                st.markdown("---")
                st.markdown(f'<p class="sec-head">File {idx+1}/{len(uploaded_files)}: {uf.name}</p>', unsafe_allow_html=True)
                prog = st.progress(0, text="Starting...")
                start_ts = time.time()
                try:
                    prog.progress(20, text="Extracting text...")
                    raw_text, pages, err = extract_text(uf)
                    if err:
                        st.error(f"❌ {err}")
                        prog.empty(); continue
                    if not raw_text.strip():
                        st.error("❌ No text found in document.")
                        prog.empty(); continue

                    prog.progress(40, text="Masking PII...")
                    safe_text = mask_pii(raw_text)
                    missing = check_missing(safe_text)

                    prog.progress(65, text="AI analyzing document...")
                    analysis = run_groq_audit(safe_text, missing, api_key)
                    elapsed = round(time.time() - start_ts, 2)

                    prog.progress(90, text="Parsing results...")
                    confidence, flags = parse_response(analysis)
                    is_ok = "APPROVED" in analysis.upper() and "ESCALATE" not in analysis.upper()

                    if confidence and confidence < 70 and is_ok:
                        flags.append(f"Auto-escalated: confidence below threshold ({confidence}%)")
                        is_ok = False
                    for mf in missing:
                        ft = f"Missing required field: {mf.title()}"
                        if ft not in flags: flags.append(ft)

                    prog.progress(100, text="✅ Done!")
                    time.sleep(0.3); prog.empty()

                    st.session_state.audit_count += 1
                    st.session_state.total_pages += pages
                    st.session_state.total_time  += elapsed
                    st.session_state.last_result  = analysis
                    if is_ok: st.session_state.approved_count  += 1
                    else:     st.session_state.escalated_count += 1
                    st.session_state.audit_history.append({
                        "id": st.session_state.audit_count, "file": uf.name,
                        "status": "APPROVED" if is_ok else "ESCALATED",
                        "confidence": confidence or 0, "time": elapsed, "pages": pages,
                        "timestamp": datetime.now().strftime("%H:%M:%S"), "flags": len(flags)
                    })

                    cc = GREEN if (confidence or 0) >= 80 else AMBER if (confidence or 0) >= 60 else RED
                    st.markdown(f"""
                    <div class="mbox-row">
                        <div class="mbox"><div class="mv" style="color:{cc}">{confidence or 'N/A'}{'%' if confidence else ''}</div><div class="ml">Confidence</div></div>
                        <div class="mbox"><div class="mv">{elapsed}s</div><div class="ml">Speed</div></div>
                        <div class="mbox"><div class="mv">{pages}</div><div class="ml">Pages</div></div>
                        <div class="mbox"><div class="mv" style="color:{RED if flags else GREEN}">{len(flags)}</div><div class="ml">Flags</div></div>
                    </div>
                    <div class="cbar-wrap">
                        <div class="cbar-labels"><span>Confidence Score</span><span style="color:{cc}">{confidence or 0}%</span></div>
                        <div class="cbar-outer"><div class="cbar-inner" style="width:{confidence or 0}%;background:linear-gradient(90deg,{cc}88,{cc})"></div></div>
                    </div>""", unsafe_allow_html=True)

                    card_cls = "approved" if is_ok else "escalate"
                    pill_cls = "green"    if is_ok else "amber"
                    verdict  = "✅ APPROVED — Document Compliant" if is_ok else "⚠️ ESCALATED — Human Review Required"
                    st.markdown(f"""
                    <div class="result-card {card_cls}">
                        <span class="pill {pill_cls}">{verdict}</span>
                        <div class="result-body">{analysis}</div>
                    </div>""", unsafe_allow_html=True)

                    if is_ok and len(uploaded_files) == 1:
                        st.balloons()

                    all_fields = ["applicant name","date","loan amount","property address","signature","income","employment","bank statement"]
                    with st.expander(f"📋 Checklist — {'⚠️ ' + str(len(missing)) + ' missing' if missing else '✓ All present'}"):
                        for f in all_fields:
                            cls = "chk-no" if f in missing else "chk-ok"
                            sym = "✗"      if f in missing else "✓"
                            st.markdown(f'<div class="chk-row"><span class="{cls}">{sym}</span> {f.title()}</div>', unsafe_allow_html=True)

                    if flags:
                        with st.expander(f"🚩 {len(flags)} Compliance Flag(s)"):
                            for i, flag in enumerate(flags, 1):
                                st.markdown(f'<div class="flag-item"><b>#{i}</b> {flag}</div>', unsafe_allow_html=True)

                    if st.session_state.show_raw:
                        with st.expander("🔍 Raw AI Output"):
                            st.markdown(f'<div class="raw-out">{analysis}</div>', unsafe_allow_html=True)

                    report = f"""MORTGAGEAI AUDITOR - COMPLIANCE REPORT
{'='*52}
File      : {uf.name}
Date/Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status    : {'APPROVED' if is_ok else 'ESCALATED TO HUMAN'}
Confidence: {confidence or 0}%
Pages     : {pages}
Speed     : {elapsed}s
Flags     : {len(flags)}
{'='*52}
AI ASSESSMENT:
{analysis}
{'='*52}
Missing Fields : {', '.join(missing) if missing else 'None'}
Flags Raised:
{chr(10).join('  - ' + f for f in flags) if flags else '  None'}
{'='*52}
Developed by Agha Wafa Abbas | ML Engineer Consultant
"""
                    d1, d2 = st.columns(2)
                    with d1:
                        st.download_button("⬇️ Report (.txt)", data=report,
                            file_name=f"audit_{uf.name.replace('.','_')}.txt", mime="text/plain", use_container_width=True)
                    with d2:
                        st.download_button("⬇️ Data (.json)", data=json.dumps({"file": uf.name, "status": "APPROVED" if is_ok else "ESCALATED", "confidence": confidence, "flags": flags, "analysis": analysis}, indent=2),
                            file_name=f"audit_{uf.name.replace('.','_')}.json", mime="application/json", use_container_width=True)

                except Exception as e:
                    prog.empty()
                    st.error(f"❌ Error: {str(e)}")
    else:
        st.markdown(f"""
        <div style="background:{BG2};border:1.5px dashed {"#1e3a5f55" if is_dark else "#2563eb33"};border-radius:16px;padding:3rem 2rem;text-align:center;color:{TEXT3};margin-top:1rem;">
            <div style="font-size:3rem;margin-bottom:0.8rem">📄</div>
            <div style="font-size:1rem;font-weight:700;color:{TEXT2};font-family:Sora,sans-serif">Upload documents to begin</div>
            <div style="font-size:0.82rem;margin-top:0.3rem">PDF & DOCX supported · Up to 50 files per batch</div>
        </div>""", unsafe_allow_html=True)

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<p class="sec-head">Audit History — This Session</p>', unsafe_allow_html=True)
    if st.session_state.audit_history:
        st.markdown(f'<div class="hist-row hist-head"><span>#</span><span>File</span><span>Status</span><span>Conf.</span><span>Time</span></div>', unsafe_allow_html=True)
        for row in reversed(st.session_state.audit_history):
            bc  = "color:#34d399;font-weight:700" if row["status"] == "APPROVED" else f"color:{AMBER};font-weight:700"
            btx = "✅ OK" if row["status"] == "APPROVED" else "⚠️ ESC"
            st.markdown(f'<div class="hist-row hist-body"><span style="color:{TEXT3}">#{row["id"]}</span><span style="font-size:0.75rem">{row["file"][:24]}</span><span style="{bc}">{btx}</span><span style="font-family:JetBrains Mono,monospace">{row["confidence"]}%</span><span style="color:{TEXT3}">{row["time"]}s</span></div>', unsafe_allow_html=True)
        h = st.session_state.audit_history
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Confidence", f"{int(sum(r['confidence'] for r in h)/len(h))}%")
        c2.metric("Total Time", f"{sum(r['time'] for r in h):.1f}s")
        c3.metric("Total Flags", sum(r['flags'] for r in h))
    else:
        st.info("No audits yet this session.")

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<p class="sec-head">How It Works</p>', unsafe_allow_html=True)
    for n, t, b in [
        ("01","Upload","PDF or DOCX uploaded via Streamlit. Up to 50 files per batch supported."),
        ("02","Text Extract","PyPDF handles PDFs. python-docx handles Word documents."),
        ("03","PII Masking","SSNs, card numbers, phones, emails auto-redacted before AI sees the text."),
        ("04","Checklist","8 required mortgage fields verified before AI call."),
        ("05","Groq AI","LLaMA-3.3-70b analyzes document and returns structured compliance report."),
        ("06","Risk Engine","Auto-escalation if confidence < 70%. Flags parsed and categorized."),
        ("07","Download","Full audit reports in TXT and JSON format available for download."),
    ]:
        st.markdown(f'<div style="display:flex;gap:1.1rem;align-items:flex-start;background:{BG2};border:1px solid {BORDER};border-radius:12px;padding:0.9rem 1.1rem;margin-bottom:0.5rem;"><div style="font-family:JetBrains Mono,monospace;font-size:1.1rem;font-weight:800;color:{ACCENT};min-width:32px">{n}</div><div><div style="font-weight:700;color:{TEXT1};margin-bottom:0.2rem">{t}</div><div style="font-size:0.81rem;color:{TEXT2};line-height:1.6">{b}</div></div></div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    <div class="footer-name">⚡ Developed by Agha Wafa Abbas</div>
    <div class="footer-role">ML Engineer Consultant · AI/ML Researcher · University of Portsmouth · Arden University</div>
    <div class="footer-tags">
        <span class="footer-tag">Groq LLaMA</span><span class="footer-tag">Streamlit</span>
        <span class="footer-tag">Python</span><span class="footer-tag">NLP</span>
        <span class="footer-tag">Fintech AI</span><span class="footer-tag">PII Protection</span>
        <span class="footer-tag">Compliance AI</span><span class="footer-tag">Batch Processing</span>
    </div>
</div>""", unsafe_allow_html=True)