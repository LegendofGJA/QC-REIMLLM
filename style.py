import streamlit as st
import os
import re
import requests
from datetime import datetime, timedelta, timezone
from PIL import ExifTags

PRESETS_DIR = "presets"

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0b0b12;
    --surface: #121220;
    --surface-2: #191930;
    --border: #1e1e35;
    --border-hover: #2e2e50;
    --text: #eaeaf2;
    --text-sec: #8888a5;
    --text-muted: #50506a;
    --accent: #E5322D;
    --accent-hover: #ff4440;
    --accent-soft: rgba(229,50,45,0.10);
    --accent-glow: rgba(229,50,45,0.22);
    --green: #10b981;
    --yellow: #f59e0b;
    --red: #ef4444;
    --radius: 16px;
    --radius-sm: 10px;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.block-container {
    max-width: 960px !important;
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #222240; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #353550; }
::selection { background: rgba(229,50,45,0.3); color: #fff; }

[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
}
.stAppDeployButton { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

[data-testid="stSidebar"] {
    background: #0e0e1a !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top: 8px; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    color: var(--text-sec) !important; border-radius: 8px !important;
    padding: 8px 12px !important; margin: 2px 8px !important;
    transition: all 0.2s ease !important; font-size: 0.88rem !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    color: var(--text) !important; background: var(--surface-2) !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    color: var(--accent) !important; background: var(--accent-soft) !important;
    font-weight: 600 !important;
}

[data-testid="stMarkdownContainer"] h1 {
    font-weight: 800 !important; font-size: 2.2rem !important;
    color: var(--text) !important; letter-spacing: -0.02em;
}
[data-testid="stMarkdownContainer"] h2 {
    font-weight: 700 !important; font-size: 1.5rem !important;
    color: var(--text) !important;
}
[data-testid="stMarkdownContainer"] h3 {
    font-weight: 600 !important; font-size: 1rem !important;
    color: var(--text) !important;
}
[data-testid="stMarkdownContainer"] h5 {
    font-weight: 500 !important; color: var(--text-muted) !important;
    font-size: 0.82rem !important;
}
[data-testid="stCaption"] {
    color: var(--text-muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
}
[data-testid="stWidgetLabel"] label {
    color: var(--text-sec) !important; font-weight: 500 !important;
    font-size: 0.82rem !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    padding: 0.6rem 0.9rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--text-muted) !important; }

[data-testid="stSelectbox"] > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
}
[data-testid="stSelectbox"] > div > div:hover { border-color: var(--border-hover) !important; }

[data-testid="stRadio"] > div { gap: 8px !important; }
[data-testid="stRadio"] label {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.85rem !important;
    transition: all 0.2s !important;
}
[data-testid="stRadio"] label:hover { border-color: var(--accent) !important; }

[data-testid="stFileUploader"] {
    border: 2px dashed var(--accent) !important;
    border-radius: var(--radius) !important;
    background: var(--accent-soft) !important;
    padding: 24px 16px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover { background: rgba(229,50,45,0.07) !important; }
[data-testid="stFileUploader"] button {
    background: var(--surface-2) !important; color: var(--accent) !important;
    border: 1px solid var(--border) !important; border-radius: 8px !important;
    font-weight: 600 !important; transition: all 0.2s !important;
}
[data-testid="stFileUploader"] button:hover {
    background: var(--accent) !important; color: #fff !important;
}

[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), #c0242a) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 1rem !important;
    padding: 0.75rem 1.5rem !important; letter-spacing: 0.03em;
    box-shadow: 0 4px 24px var(--accent-glow) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    box-shadow: 0 6px 32px rgba(229,50,45,0.4) !important;
    transform: translateY(-2px);
}
[data-testid="stButton"] button:not([kind="primary"]) {
    background: var(--surface-2) !important; color: var(--text-sec) !important;
    border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important;
    font-weight: 500 !important; transition: all 0.2s !important;
}
[data-testid="stButton"] button:not([kind="primary"]):hover {
    border-color: var(--accent) !important; color: var(--accent) !important;
}

[data-testid="stDownloadButton"] a,
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, var(--accent), #c0242a) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 1.05rem !important;
    padding: 0.8rem 2rem !important; letter-spacing: 0.04em;
    animation: ilpPulse 2s ease-in-out infinite !important;
    transition: all 0.3s !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border: none !important; font-size: 0.85rem !important;
}
[data-testid="stAlert"][kind="success"] {
    background: rgba(16,185,129,0.10) !important;
    color: #6ee7b7 !important; border-left: 3px solid var(--green) !important;
}
[data-testid="stAlert"][kind="warning"] {
    background: rgba(245,158,11,0.10) !important;
    color: #fcd34d !important; border-left: 3px solid var(--yellow) !important;
}
[data-testid="stAlert"][kind="error"] {
    background: rgba(239,68,68,0.10) !important;
    color: #fca5a5 !important; border-left: 3px solid var(--red) !important;
}
[data-testid="stAlert"][kind="info"] {
    background: var(--accent-soft) !important;
    color: #fca5a5 !important; border-left: 3px solid var(--accent) !important;
}

[data-testid="stToast"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stSpinner"] { color: var(--accent) !important; }
[data-testid="stHorizontalBlock"] { gap: 16px !important; }

div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 24px 20px !important;
    transition: border-color 0.3s, box-shadow 0.3s !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"]:hover {
    border-color: var(--border-hover) !important;
    box-shadow: 0 4px 28px rgba(0,0,0,0.25) !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
    background: transparent !important; border: none !important;
    border-radius: 0 !important; padding: 0 !important; box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"]:hover {
    border-color: transparent !important; box-shadow: none !important;
}

.card-head {
    margin-bottom: 16px; padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
}
.card-head-icon {
    width: 42px; height: 42px; background: var(--accent-soft); border-radius: 11px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 19px; margin-bottom: 12px;
}
.card-head h3 {
    font-size: 1rem !important; font-weight: 700 !important;
    color: var(--text) !important; margin: 0 0 4px 0 !important;
}
.card-head p {
    font-size: 0.78rem !important; color: var(--text-muted) !important; margin: 0 !important;
}

.upload-head {
    text-align: center; margin-bottom: 14px; padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
}
.upload-head-icon {
    width: 54px; height: 54px; background: var(--accent-soft); border-radius: 14px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 26px; margin-bottom: 10px;
}
.upload-head h3 {
    font-size: 1rem !important; font-weight: 700 !important;
    color: var(--text) !important; margin: 0 0 4px 0 !important;
}
.upload-head p {
    font-size: 0.78rem !important; color: var(--text-muted) !important; margin: 0 !important;
}

.page-head { text-align: center; padding: 32px 0 20px; }
.page-head-icon {
    width: 64px; height: 64px; background: var(--accent-soft); border-radius: 16px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 30px; margin-bottom: 14px;
}
.page-head h2 {
    font-size: 1.6rem !important; font-weight: 800 !important;
    color: var(--text) !important; margin: 0 0 6px !important; letter-spacing: -0.02em;
}
.page-head p { color: var(--text-sec) !important; font-size: 0.92rem !important; margin: 0 !important; }

.ilp-hero { text-align: center; padding: 52px 0 28px; position: relative; }
.ilp-hero::after {
    content: ''; position: absolute; top: -20px; left: 50%; transform: translateX(-50%);
    width: 500px; height: 220px;
    background: radial-gradient(ellipse, rgba(229,50,45,0.06) 0%, transparent 70%);
    pointer-events: none; z-index: -1;
}
.ilp-hero-icon {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, var(--accent), #ff6b5a);
    border-radius: 22px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 36px; margin-bottom: 20px;
    box-shadow: 0 8px 40px var(--accent-glow);
    animation: ilpFloat 3s ease-in-out infinite;
}
.ilp-hero h1 {
    font-size: 2.4rem; font-weight: 800; color: var(--text);
    margin: 0 0 8px; letter-spacing: -0.03em;
}
.ilp-hero p {
    color: var(--text-sec); font-size: 1rem; margin: 0;
    line-height: 1.6; max-width: 520px; display: inline-block;
}

.tools-grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 20px; margin: 36px 0;
}

a.tool-card-link {
    text-decoration: none !important;
    color: inherit !important;
    outline: none !important;
    display: block;
    transition: transform 0.3s ease;
}
a.tool-card-link:hover {
    transform: translateY(-4px);
}

.tool-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 32px 24px; text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    height: 100%;
}
a.tool-card-link:hover .tool-card {
    border-color: var(--accent);
    box-shadow: 0 12px 40px rgba(229,50,45,0.12);
}
.tool-card-icon {
    width: 56px; height: 56px; background: var(--accent-soft); border-radius: 14px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 26px; margin-bottom: 16px;
}
.tool-card h3 {
    font-size: 1.05rem; font-weight: 700; color: var(--text); margin: 0 0 8px;
}
.tool-card p {
    font-size: 0.82rem; color: var(--text-muted); margin: 0 0 16px; line-height: 1.5;
}
.tool-card-tag {
    display: inline-block; background: var(--accent-soft); color: var(--accent);
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.04em;
}

.ilp-steps {
    display: flex; align-items: flex-start; justify-content: center;
    gap: 0; margin: 36px 0; flex-wrap: wrap;
}
.ilp-step {
    display: flex; flex-direction: column;
    align-items: center; gap: 8px; min-width: 80px;
}
.ilp-step-num {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--surface-2); border: 2px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.82rem; font-weight: 700; color: var(--text-muted);
}
.ilp-step.active .ilp-step-num {
    background: var(--accent); border-color: var(--accent); color: #fff;
    box-shadow: 0 0 16px var(--accent-glow);
}
.ilp-step-label {
    font-size: 0.7rem; font-weight: 600; color: var(--text-muted); text-align: center;
}
.ilp-step.active .ilp-step-label { color: var(--text-sec); }
.ilp-step-line { width: 52px; height: 2px; background: var(--border); margin-top: 17px; }
.ilp-step-line.active { background: var(--accent); }

.stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px; margin: 24px 0;
}
.stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px 20px; text-align: center;
    transition: border-color 0.3s;
}
.stat-card:hover { border-color: var(--border-hover); }
.stat-card-value { font-size: 2rem; font-weight: 800; color: var(--accent); line-height: 1; }
.stat-card-label { font-size: 0.78rem; color: var(--text-muted); margin-top: 8px; }

.ilp-user { text-align: center; margin-bottom: 8px; }
.ilp-user-icon {
    width: 36px; height: 36px; background: var(--surface-2);
    border: 1px solid var(--border); border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 16px; margin-bottom: 6px;
}
.ilp-user-hint { font-size: 0.78rem; color: var(--text-muted); margin-bottom: 10px; }

.ilp-action-head { text-align: center; margin-bottom: 16px; }
.ilp-action-head h3 {
    font-size: 1.1rem !important; font-weight: 700 !important;
    color: var(--text) !important; margin: 0 0 4px !important;
}
.ilp-action-head p {
    font-size: 0.82rem !important; color: var(--text-muted) !important; margin: 0 !important;
}

hr {
    border: none !important; height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--border), transparent) !important;
    margin: 2rem 0 !important;
}

[data-testid="stNumberInput"] button {
    background: var(--surface-2) !important;
    color: var(--accent) !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stNumberInput"] button:hover {
    background: var(--accent) !important; color: #fff !important;
}

[data-testid="stSlider"] [data-testid="stTickBar"] { color: var(--text-muted) !important; }

@keyframes ilpFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
}
@keyframes ilpPulse {
    0%, 100% { box-shadow: 0 4px 24px var(--accent-glow); }
    50% { box-shadow: 0 4px 40px rgba(229,50,45,0.45); }
}
@keyframes ilpFadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stVerticalBlock"] > div {
    animation: ilpFadeUp 0.45s ease forwards; opacity: 0;
}
[data-testid="stVerticalBlock"] > div:nth-child(1)  { animation-delay: 0.00s; }
[data-testid="stVerticalBlock"] > div:nth-child(2)  { animation-delay: 0.04s; }
[data-testid="stVerticalBlock"] > div:nth-child(3)  { animation-delay: 0.08s; }
[data-testid="stVerticalBlock"] > div:nth-child(4)  { animation-delay: 0.12s; }
[data-testid="stVerticalBlock"] > div:nth-child(5)  { animation-delay: 0.16s; }
[data-testid="stVerticalBlock"] > div:nth-child(6)  { animation-delay: 0.20s; }
[data-testid="stVerticalBlock"] > div:nth-child(7)  { animation-delay: 0.24s; }
[data-testid="stVerticalBlock"] > div:nth-child(8)  { animation-delay: 0.28s; }
[data-testid="stVerticalBlock"] > div:nth-child(9)  { animation-delay: 0.32s; }
[data-testid="stVerticalBlock"] > div:nth-child(10) { animation-delay: 0.36s; }
[data-testid="stVerticalBlock"] > div:nth-child(11) { animation-delay: 0.40s; }
[data-testid="stVerticalBlock"] > div:nth-child(12) { animation-delay: 0.44s; }
[data-testid="stVerticalBlock"] > div:nth-child(13) { animation-delay: 0.48s; }
[data-testid="stVerticalBlock"] > div:nth-child(14) { animation-delay: 0.52s; }
[data-testid="stVerticalBlock"] > div:nth-child(15) { animation-delay: 0.56s; }
[data-testid="stVerticalBlock"] > div:nth-child(16) { animation-delay: 0.60s; }
[data-testid="stVerticalBlock"] > div:nth-child(17) { animation-delay: 0.64s; }
[data-testid="stVerticalBlock"] > div:nth-child(18) { animation-delay: 0.68s; }
[data-testid="stVerticalBlock"] > div:nth-child(19) { animation-delay: 0.72s; }
[data-testid="stVerticalBlock"] > div:nth-child(20) { animation-delay: 0.76s; }

@media (max-width: 768px) {
    .tools-grid { grid-template-columns: 1fr; }
    .ilp-hero h1 { font-size: 1.6rem !important; }
    .ilp-hero-icon { width: 60px; height: 60px; font-size: 28px; border-radius: 16px; }
    .ilp-step-line { width: 28px; }
    .ilp-step-label { font-size: 0.6rem; }
    .ilp-step-num { width: 30px; height: 30px; font-size: 0.75rem; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
        padding: 16px 14px !important;
    }
    .card-head-icon, .upload-head-icon, .page-head-icon {
        width: 36px; height: 36px; font-size: 16px;
    }
}
"""


def inject_css():
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def inject_sidebar_brand():
    st.sidebar.markdown(
        """
        <div style="padding: 8px 0 16px; border-bottom: 1px solid #1e1e35; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width:36px; height:36px; background:linear-gradient(135deg,#E5322D,#ff6b5a);
                            border-radius:10px; display:flex; align-items:center; justify-content:center;
                            font-size:18px; box-shadow:0 3px 12px rgba(229,50,45,0.25);">📸</div>
                <div>
                    <div style="font-weight:700; font-size:0.92rem; color:#eaeaf2;">QC Image Inserter</div>
                    <div style="font-size:0.65rem; color:#50506a;">Crew Edition</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_footer():
    st.markdown(
        """
        <div style="text-align:center; padding:32px 0 16px; margin-top:40px; border-top:1px solid #1e1e35;">
            <p style="color:#50506a; font-size:0.78rem; margin:0; line-height:1.9;">
                QC Image Inserter - Crew Edition<br>
                Built with <span style="color:#E5322D; font-weight:600;">AI</span>
                &amp; <span style="color:#E5322D; font-weight:600;">GJorma</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def convert_date_to_english(date_str):
    if not date_str or not date_str.strip():
        return ""
    date_str = date_str.strip()
    MONTH_MAP = {
        "jan": "January", "januari": "January",
        "feb": "February", "februari": "February",
        "mar": "March", "maret": "March",
        "apr": "April",
        "mei": "May", "may": "May",
        "jun": "June", "juni": "June",
        "jul": "July", "juli": "July",
        "agu": "August", "agustus": "August", "aug": "August",
        "sep": "September",
        "okt": "October", "oktober": "October", "oct": "October",
        "nov": "November",
        "des": "December", "dec": "December",
    }
    parts = date_str.split()
    if len(parts) == 3:
        day, month_abbr, year = parts
        month_key = month_abbr.lower()
        if month_key in MONTH_MAP:
            month_full = MONTH_MAP[month_key]
            if len(year) == 2 and year.isdigit():
                year = "20" + year
            return f"{day} {month_full} {year}"
    return date_str


def log_traffic(user, toko, tgl_qc, template, layout):
    try:
        from audit_core import get_supabase_client
        supabase = get_supabase_client()
        if supabase is None:
            st.error("Traffic log failed: Supabase belum terkoneksi.")
            return
        supabase.table("audit_traffic_log").insert({
            "auditor": user or "Unknown",
            "store_name": toko or "Unknown",
            "audit_date": tgl_qc or "Unknown",
            "score_info": f"Template: {template} | Layout: {layout}",
            "action": "Image Inserter",
        }).execute()
        st.toast("Traffic logged!")
    except Exception as e:
        st.error(f"Traffic log failed: {e}")


def correct_orientation(img):
    try:
        if hasattr(img, "_getexif") and img._getexif() is not None:
            exif = img._getexif()
            orientation = exif.get(ExifTags.Base.Orientation)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img


def convert_utc_to_wib(iso_str):
    """Convert a UTC timestamp string (Supabase created_at) to WIB (UTC+7)."""
    if not iso_str:
        return ""
    s = str(iso_str).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        s = s.replace("T", " ")
        return s[:19]
    if dt.tzinfo is None:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.astimezone(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")


def extract_datetime(filename, uploaded_file_obj):
    match = re.search(r"(\d{4}-\d{2}-\d{2}) at (\d{2}\.\d{2}\.\d{2})", filename)
    if match:
        try:
            return datetime.strptime(
                f"{match.group(1)} {match.group(2).replace('.', ':')}", "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
    return datetime.min


def get_preset_files():
    if not os.path.isdir(PRESETS_DIR):
        os.makedirs(PRESETS_DIR, exist_ok=True)
        return []
    return [f for f in os.listdir(PRESETS_DIR) if f.lower().endswith(".xlsx")]
