import streamlit as st
import os
import re
import requests
from datetime import datetime, timedelta, timezone
from PIL import ExifTags

PRESETS_DIR = "presets"

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800;900&family=Chakra+Petch:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg: #05050d;
    --bg-deep: #030308;
    --surface: rgba(10, 12, 28, 0.90);
    --surface-2: rgba(16, 19, 44, 0.96);
    --border: rgba(0, 240, 255, 0.28);
    --border-hover: rgba(255, 0, 127, 0.78);
    --text: #eefbff;
    --text-sec: #9ae4f5;
    --text-muted: #6c80ad;
    --cyan: #00f0ff;
    --cyan-soft: rgba(0, 240, 255, 0.13);
    --cyan-glow: rgba(0, 240, 255, 0.50);
    --magenta: #ff007f;
    --magenta-soft: rgba(255, 0, 127, 0.15);
    --magenta-glow: rgba(255, 0, 127, 0.50);
    --accent: #00f0ff;
    --accent-2: #ff007f;
    --accent-hover: #5ff7ff;
    --accent-soft: rgba(0, 240, 255, 0.13);
    --accent-glow: rgba(0, 240, 255, 0.48);
    --green: #00ff9d;
    --yellow: #ffbe0b;
    --red: #ff0055;
    --radius: 14px;
    --radius-sm: 8px;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    background-image:
        radial-gradient(circle at 10% 8%, rgba(0, 240, 255, 0.14), transparent 34%),
        radial-gradient(circle at 90% 18%, rgba(255, 0, 127, 0.14), transparent 36%),
        radial-gradient(circle at 50% 96%, rgba(0, 240, 255, 0.10), transparent 42%),
        linear-gradient(rgba(0, 240, 255, 0.042) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 0, 127, 0.032) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 100% 100%, 40px 40px, 40px 40px !important;
    background-attachment: fixed !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
    border-bottom: none !important;
    color: var(--text) !important;
}

.block-container {
    max-width: 980px !important;
    padding-top: 0.4rem !important;
    padding-bottom: 2.5rem !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #05050d; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--cyan), var(--magenta));
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #70f8ff, #ff4da6);
}
::selection {
    background: rgba(255, 0, 127, 0.45);
    color: #fff;
}

.stAppDeployButton { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── SIDEBAR CYBER HUD ── */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(7, 9, 24, 0.98), rgba(4, 5, 14, 0.99)) !important;
    border-right: 1px solid rgba(0, 240, 255, 0.35) !important;
    box-shadow: 4px 0 28px rgba(0, 240, 255, 0.14), inset -1px 0 0 rgba(255, 0, 127, 0.25) !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top: 8px; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    color: var(--text-sec) !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    margin: 3px 8px !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    transition: all 0.22s ease !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    color: #ffffff !important;
    background: rgba(0, 240, 255, 0.10) !important;
    border-color: rgba(0, 240, 255, 0.45) !important;
    box-shadow: 0 0 14px rgba(0, 240, 255, 0.22) !important;
    transform: translateX(2px);
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    color: var(--cyan) !important;
    background: linear-gradient(90deg, rgba(255, 0, 127, 0.22), rgba(0, 240, 255, 0.14)) !important;
    border: 1px solid rgba(0, 240, 255, 0.65) !important;
    border-left: 3px solid var(--magenta) !important;
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.26), inset 0 0 12px rgba(255, 0, 127, 0.16) !important;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
    font-weight: 700 !important;
}

/* ── TYPOGRAPHY ── */
[data-testid="stMarkdownContainer"] h1 {
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.15rem !important;
    color: #ffffff !important;
    letter-spacing: 0.03em;
    text-shadow: 0 0 14px rgba(0, 240, 255, 0.65), 0 0 32px rgba(255, 0, 127, 0.35);
}
[data-testid="stMarkdownContainer"] h2 {
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.48rem !important;
    color: var(--cyan) !important;
    letter-spacing: 0.03em;
    text-shadow: 0 0 14px rgba(0, 240, 255, 0.55);
}
[data-testid="stMarkdownContainer"] h3 {
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.08rem !important;
    color: #ffffff !important;
    letter-spacing: 0.02em;
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.35);
}
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5 {
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600 !important;
    color: var(--magenta) !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-size: 0.86rem !important;
    text-shadow: 0 0 10px rgba(255, 0, 127, 0.45);
}
[data-testid="stCaption"] {
    color: var(--text-sec) !important;
    opacity: 0.85;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.76rem !important;
}
[data-testid="stWidgetLabel"] label {
    color: var(--cyan) !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    letter-spacing: 0.03em;
}

/* ── INPUTS & TEXTAREAS ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background: rgba(9, 12, 28, 0.96) !important;
    border: 1px solid rgba(0, 240, 255, 0.34) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    padding: 0.6rem 0.9rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.28), 0 0 20px rgba(0, 240, 255, 0.35) !important;
    outline: none !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: var(--text-muted) !important;
}

[data-testid="stSelectbox"] > div > div {
    background: rgba(9, 12, 28, 0.96) !important;
    border: 1px solid rgba(0, 240, 255, 0.34) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stSelectbox"] > div > div:hover {
    border-color: var(--magenta) !important;
    box-shadow: 0 0 14px rgba(255, 0, 127, 0.32) !important;
}

[data-testid="stRadio"] > div { gap: 8px !important; }
[data-testid="stRadio"] label {
    background: rgba(11, 14, 34, 0.92) !important;
    border: 1px solid rgba(0, 240, 255, 0.28) !important;
    border-radius: 8px !important;
    padding: 0.42rem 0.9rem !important;
    transition: all 0.2s !important;
}
[data-testid="stRadio"] label:hover {
    border-color: var(--magenta) !important;
    box-shadow: 0 0 12px rgba(255, 0, 127, 0.35) !important;
}

/* ── EXPANDER & DATAFRAME & METRICS ── */
[data-testid="stExpander"] {
    background: rgba(9, 11, 26, 0.88) !important;
    border: 1px solid rgba(0, 240, 255, 0.32) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 0 24px rgba(0, 240, 255, 0.08), inset 0 1px 0 rgba(0, 240, 255, 0.16) !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 700 !important;
    color: var(--cyan) !important;
    letter-spacing: 0.02em;
}
[data-testid="stExpander"] summary:hover {
    color: var(--magenta) !important;
}

/* ── TABS (PANDUAN & INTERAKTIF) ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(0, 240, 255, 0.28) !important;
    padding-bottom: 6px;
}
[data-testid="stTabs"] button[role="tab"] {
    background: rgba(11, 14, 34, 0.90) !important;
    color: var(--text-sec) !important;
    border: 1px solid rgba(0, 240, 255, 0.28) !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: #ffffff !important;
    border-color: var(--magenta) !important;
    box-shadow: 0 0 14px rgba(255, 0, 127, 0.35) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #ffffff !important;
    background: linear-gradient(135deg, rgba(255, 0, 127, 0.35), rgba(0, 240, 255, 0.25)) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.42), 0 0 12px rgba(255, 0, 127, 0.32) !important;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, var(--cyan), var(--magenta)) !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(12, 16, 38, 0.94), rgba(7, 9, 22, 0.98)) !important;
    border: 1px solid rgba(0, 240, 255, 0.35) !important;
    border-top: 2px solid var(--magenta) !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.12), 0 0 14px rgba(255, 0, 127, 0.10) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Chakra Petch', sans-serif !important;
    color: var(--text-sec) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    font-family: 'Orbitron', sans-serif !important;
    color: var(--cyan) !important;
    font-weight: 800 !important;
    text-shadow: 0 0 14px rgba(0, 240, 255, 0.65);
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(0, 240, 255, 0.32) !important;
    border-radius: 12px !important;
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.10) !important;
    overflow: hidden;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--cyan) !important;
    border-radius: var(--radius) !important;
    background: linear-gradient(145deg, rgba(0, 240, 255, 0.08), rgba(255, 0, 127, 0.06)) !important;
    padding: 24px 16px !important;
    box-shadow: 0 0 24px rgba(0, 240, 255, 0.14), inset 0 0 24px rgba(0, 240, 255, 0.06) !important;
    transition: all 0.25s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--magenta) !important;
    background: linear-gradient(145deg, rgba(255, 0, 127, 0.11), rgba(0, 240, 255, 0.08)) !important;
    box-shadow: 0 0 28px rgba(255, 0, 127, 0.26) !important;
}
[data-testid="stFileUploader"] button {
    background: rgba(10, 14, 34, 0.96) !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 8px !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 700 !important;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.25) !important;
    transition: all 0.2s !important;
}
[data-testid="stFileUploader"] button:hover {
    background: var(--cyan) !important;
    color: #05050d !important;
    box-shadow: 0 0 22px rgba(0, 240, 255, 0.7) !important;
}

/* ── BUTTONS (FULL NEON) ── */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #ff007f 0%, #d400a8 48%, #00d9ff 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(0, 240, 255, 0.75) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 1.5rem !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    text-shadow: 0 1px 6px rgba(0, 0, 0, 0.55);
    box-shadow: 0 0 24px rgba(255, 0, 127, 0.50), 0 0 16px rgba(0, 240, 255, 0.35) !important;
    transition: all 0.25s ease !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    box-shadow: 0 0 34px rgba(255, 0, 127, 0.78), 0 0 28px rgba(0, 240, 255, 0.65) !important;
    transform: translateY(-2px);
    filter: brightness(1.1);
}
[data-testid="stButton"] button:not([kind="primary"]) {
    background: rgba(12, 16, 38, 0.94) !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(0, 240, 255, 0.45) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.14) !important;
    transition: all 0.22s !important;
}
[data-testid="stButton"] button:not([kind="primary"]):hover {
    border-color: var(--magenta) !important;
    color: #ffffff !important;
    background: rgba(255, 0, 127, 0.18) !important;
    box-shadow: 0 0 20px rgba(255, 0, 127, 0.48), 0 0 12px rgba(0, 240, 255, 0.25) !important;
    transform: translateY(-1px);
}

[data-testid="stDownloadButton"] a,
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #00f0ff 0%, #0095ff 45%, #ff007f 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Chakra Petch', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    padding: 0.8rem 2rem !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    text-shadow: 0 1px 6px rgba(0, 0, 0, 0.55);
    animation: cyberPulse 2.2s ease-in-out infinite !important;
    transition: all 0.25s !important;
}
[data-testid="stDownloadButton"] a:hover,
[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-2px);
    filter: brightness(1.12);
}

/* ── PROGRESS BAR ── */
[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, var(--cyan), var(--magenta)) !important;
    box-shadow: 0 0 14px rgba(0, 240, 255, 0.65) !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.85rem !important;
}
[data-testid="stAlert"][kind="success"] {
    background: rgba(0, 255, 157, 0.10) !important;
    color: #8affcf !important;
    border: 1px solid rgba(0, 255, 157, 0.35) !important;
    border-left: 4px solid var(--green) !important;
    box-shadow: 0 0 16px rgba(0, 255, 157, 0.12) !important;
}
[data-testid="stAlert"][kind="warning"] {
    background: rgba(255, 190, 11, 0.11) !important;
    color: #ffe07d !important;
    border: 1px solid rgba(255, 190, 11, 0.35) !important;
    border-left: 4px solid var(--yellow) !important;
    box-shadow: 0 0 16px rgba(255, 190, 11, 0.12) !important;
}
[data-testid="stAlert"][kind="error"] {
    background: rgba(255, 0, 85, 0.13) !important;
    color: #ff85b3 !important;
    border: 1px solid rgba(255, 0, 127, 0.45) !important;
    border-left: 4px solid var(--magenta) !important;
    box-shadow: 0 0 18px rgba(255, 0, 127, 0.18) !important;
}
[data-testid="stAlert"][kind="info"] {
    background: rgba(0, 240, 255, 0.10) !important;
    color: #a3f7ff !important;
    border: 1px solid rgba(0, 240, 255, 0.35) !important;
    border-left: 4px solid var(--cyan) !important;
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.15) !important;
}

[data-testid="stToast"] {
    background: rgba(10, 13, 30, 0.96) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 0 22px rgba(0, 240, 255, 0.35) !important;
}
[data-testid="stSpinner"] { color: var(--cyan) !important; }
[data-testid="stHorizontalBlock"] { gap: 16px !important; }

div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
    background: linear-gradient(155deg, rgba(12, 15, 36, 0.90), rgba(7, 9, 22, 0.95)) !important;
    border: 1px solid rgba(0, 240, 255, 0.28) !important;
    border-radius: var(--radius) !important;
    padding: 22px 18px !important;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45), 0 0 18px rgba(0, 240, 255, 0.08) !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"]:hover {
    border-color: rgba(255, 0, 127, 0.62) !important;
    box-shadow: 0 8px 34px rgba(0, 0, 0, 0.55), 0 0 24px rgba(255, 0, 127, 0.18), 0 0 14px rgba(0, 240, 255, 0.14) !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
    background: transparent !important; border: none !important;
    border-radius: 0 !important; padding: 0 !important; box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"]:hover {
    border-color: transparent !important; box-shadow: none !important;
}

/* ── CARD HEADS & PAGE HEADS ── */
.card-head {
    margin-bottom: 16px; padding-bottom: 14px;
    border-bottom: 1px solid rgba(0, 240, 255, 0.24);
}
.card-head-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, rgba(0, 240, 255, 0.18), rgba(255, 0, 127, 0.18));
    border: 1px solid rgba(0, 240, 255, 0.45);
    border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 20px; margin-bottom: 12px;
    box-shadow: 0 0 16px rgba(0, 240, 255, 0.28);
}
.card-head h3 {
    font-family: 'Chakra Petch', sans-serif !important;
    font-size: 1.05rem !important; font-weight: 700 !important;
    color: var(--cyan) !important; margin: 0 0 4px 0 !important;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
}
.card-head p {
    font-size: 0.78rem !important; color: var(--text-muted) !important; margin: 0 !important;
}

.upload-head {
    text-align: center; margin-bottom: 14px; padding-bottom: 14px;
    border-bottom: 1px solid rgba(0, 240, 255, 0.24);
}
.upload-head-icon {
    width: 56px; height: 56px;
    background: linear-gradient(135deg, rgba(0, 240, 255, 0.20), rgba(255, 0, 127, 0.22));
    border: 1px solid rgba(255, 0, 127, 0.55);
    border-radius: 14px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 26px; margin-bottom: 10px;
    box-shadow: 0 0 22px rgba(255, 0, 127, 0.35), 0 0 12px rgba(0, 240, 255, 0.25);
}
.upload-head h3 {
    font-family: 'Chakra Petch', sans-serif !important;
    font-size: 1.08rem !important; font-weight: 700 !important;
    color: var(--cyan) !important; margin: 0 0 4px 0 !important;
}
.upload-head p {
    font-size: 0.78rem !important; color: var(--text-muted) !important; margin: 0 !important;
}

.page-head {
    text-align: center;
    padding: 32px 20px 24px;
    margin-bottom: 18px;
    border-radius: 18px;
    border: 1px solid rgba(0, 240, 255, 0.34);
    background:
        radial-gradient(circle at 20% 20%, rgba(0, 240, 255, 0.16), transparent 45%),
        radial-gradient(circle at 80% 80%, rgba(255, 0, 127, 0.18), transparent 45%),
        linear-gradient(145deg, rgba(11, 14, 34, 0.94), rgba(6, 7, 18, 0.98));
    box-shadow: 0 0 32px rgba(0, 240, 255, 0.14), 0 0 24px rgba(255, 0, 127, 0.12);
    position: relative;
    overflow: hidden;
}
.page-head::after {
    content: "";
    position: absolute;
    left: 15%; right: 15%; bottom: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--cyan), var(--magenta), transparent);
    box-shadow: 0 0 12px var(--cyan);
}
.page-head-icon {
    width: 68px; height: 68px;
    background: linear-gradient(135deg, rgba(0, 240, 255, 0.22), rgba(255, 0, 127, 0.26));
    border: 1px solid rgba(0, 240, 255, 0.65);
    border-radius: 16px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 30px; margin-bottom: 14px;
    box-shadow: 0 0 26px rgba(0, 240, 255, 0.42), 0 0 18px rgba(255, 0, 127, 0.32);
    animation: cyberFloat 3.2s ease-in-out infinite;
}
.page-head h2 {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 1.65rem !important; font-weight: 800 !important;
    color: #ffffff !important; margin: 0 0 8px !important;
    letter-spacing: 0.04em;
    text-shadow: 0 0 16px rgba(0, 240, 255, 0.72), 0 0 28px rgba(255, 0, 127, 0.42);
}
.page-head p {
    color: var(--text-sec) !important;
    font-size: 0.9rem !important;
    margin: 0 auto !important;
    max-width: 640px;
}

.ilp-hero { text-align: center; padding: 52px 0 28px; position: relative; }
.ilp-hero::after {
    content: ''; position: absolute; top: -20px; left: 50%; transform: translateX(-50%);
    width: 520px; height: 240px;
    background: radial-gradient(ellipse, rgba(0, 240, 255, 0.16) 0%, rgba(255, 0, 127, 0.10) 45%, transparent 72%);
    pointer-events: none; z-index: -1;
}
.ilp-hero-icon {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, var(--cyan), var(--magenta));
    border-radius: 20px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 36px; margin-bottom: 20px;
    box-shadow: 0 0 36px rgba(0, 240, 255, 0.55), 0 0 26px rgba(255, 0, 127, 0.45);
    animation: cyberFloat 3s ease-in-out infinite;
}
.ilp-hero h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.3rem; font-weight: 800; color: #ffffff;
    margin: 0 0 8px; letter-spacing: 0.03em;
    text-shadow: 0 0 18px rgba(0, 240, 255, 0.65);
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
a.tool-card-link:hover { transform: translateY(-4px); }

.tool-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 32px 24px; text-align: center;
    transition: all 0.3s ease; cursor: pointer; height: 100%;
}
a.tool-card-link:hover .tool-card {
    border-color: var(--magenta);
    box-shadow: 0 0 30px rgba(255, 0, 127, 0.30), 0 0 18px rgba(0, 240, 255, 0.25);
}
.tool-card-icon {
    width: 56px; height: 56px; background: var(--cyan-soft);
    border: 1px solid rgba(0, 240, 255, 0.45); border-radius: 14px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 26px; margin-bottom: 16px;
}
.tool-card h3 {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 1.05rem; font-weight: 700; color: #ffffff; margin: 0 0 8px;
}
.tool-card p {
    font-size: 0.82rem; color: var(--text-muted); margin: 0 0 16px; line-height: 1.5;
}
.tool-card-tag {
    display: inline-block; background: var(--magenta-soft); color: #ff66b2;
    border: 1px solid rgba(255, 0, 127, 0.45);
    padding: 4px 12px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;
}

/* ── STEP INDICATOR (QC IMAGE INSERTER) ── */
.ilp-steps {
    display: flex; align-items: flex-start; justify-content: center;
    gap: 0; margin: 28px 0; flex-wrap: wrap;
}
.ilp-step {
    display: flex; flex-direction: column;
    align-items: center; gap: 8px; min-width: 82px;
}
.ilp-step-num {
    width: 38px; height: 38px; border-radius: 10px;
    background: rgba(11, 14, 34, 0.95); border: 1px solid rgba(0, 240, 255, 0.30);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Orbitron', sans-serif;
    font-size: 0.82rem; font-weight: 700; color: var(--text-muted);
}
.ilp-step.active .ilp-step-num {
    background: linear-gradient(135deg, var(--cyan), var(--magenta));
    border-color: #ffffff; color: #ffffff;
    box-shadow: 0 0 18px rgba(0, 240, 255, 0.65), 0 0 14px rgba(255, 0, 127, 0.45);
}
.ilp-step-label {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.74rem; font-weight: 600; color: var(--text-muted); text-align: center;
}
.ilp-step.active .ilp-step-label { color: var(--cyan); text-shadow: 0 0 8px rgba(0, 240, 255, 0.45); }
.ilp-step-line { width: 52px; height: 2px; background: rgba(0, 240, 255, 0.20); margin-top: 18px; }
.ilp-step-line.active {
    background: linear-gradient(90deg, var(--cyan), var(--magenta));
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
}

.stats-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px; margin: 24px 0;
}
.stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px 20px; text-align: center;
    transition: border-color 0.3s, box-shadow 0.3s;
}
.stat-card:hover {
    border-color: var(--magenta);
    box-shadow: 0 0 22px rgba(255, 0, 127, 0.24);
}
.stat-card-value {
    font-family: 'Orbitron', sans-serif;
    font-size: 2rem; font-weight: 800; color: var(--cyan); line-height: 1;
    text-shadow: 0 0 16px rgba(0, 240, 255, 0.65);
}
.stat-card-label { font-size: 0.78rem; color: var(--text-muted); margin-top: 8px; }

.ilp-user { text-align: center; margin-bottom: 8px; }
.ilp-user-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, rgba(0, 240, 255, 0.16), rgba(255, 0, 127, 0.16));
    border: 1px solid rgba(0, 240, 255, 0.5); border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 17px; margin-bottom: 6px;
    box-shadow: 0 0 14px rgba(0, 240, 255, 0.35);
}
.ilp-user-hint { font-size: 0.8rem; color: var(--text-sec); margin-bottom: 10px; }

.ilp-action-head { text-align: center; margin-bottom: 16px; }
.ilp-action-head h3 {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 1.12rem !important; font-weight: 700 !important;
    color: var(--cyan) !important; margin: 0 0 4px !important;
    text-shadow: 0 0 12px rgba(0, 240, 255, 0.5);
}
.ilp-action-head p {
    font-size: 0.82rem !important; color: var(--text-muted) !important; margin: 0 !important;
}

hr {
    border: none !important; height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--cyan), var(--magenta), transparent) !important;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.45) !important;
    margin: 2rem 0 !important;
}

[data-testid="stNumberInput"] button {
    background: rgba(12, 16, 38, 0.96) !important;
    color: var(--cyan) !important;
    border: 1px solid rgba(0, 240, 255, 0.4) !important;
}
[data-testid="stNumberInput"] button:hover {
    background: var(--magenta) !important; color: #fff !important;
    border-color: var(--magenta) !important;
}

[data-testid="stSlider"] [data-testid="stTickBar"] { color: var(--text-sec) !important; }

/* ── ANIMATIONS ── */
@keyframes cyberFloat {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
}
@keyframes cyberPulse {
    0%, 100% {
        box-shadow: 0 0 22px rgba(0, 240, 255, 0.55), 0 0 14px rgba(255, 0, 127, 0.40);
    }
    50% {
        box-shadow: 0 0 38px rgba(255, 0, 127, 0.78), 0 0 28px rgba(0, 240, 255, 0.65);
    }
}
@keyframes ilpFadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="stVerticalBlock"] > div {
    animation: ilpFadeUp 0.4s ease forwards; opacity: 0;
}
[data-testid="stVerticalBlock"] > div:nth-child(1)  { animation-delay: 0.00s; }
[data-testid="stVerticalBlock"] > div:nth-child(2)  { animation-delay: 0.03s; }
[data-testid="stVerticalBlock"] > div:nth-child(3)  { animation-delay: 0.06s; }
[data-testid="stVerticalBlock"] > div:nth-child(4)  { animation-delay: 0.09s; }
[data-testid="stVerticalBlock"] > div:nth-child(5)  { animation-delay: 0.12s; }
[data-testid="stVerticalBlock"] > div:nth-child(6)  { animation-delay: 0.15s; }
[data-testid="stVerticalBlock"] > div:nth-child(7)  { animation-delay: 0.18s; }
[data-testid="stVerticalBlock"] > div:nth-child(8)  { animation-delay: 0.21s; }
[data-testid="stVerticalBlock"] > div:nth-child(9)  { animation-delay: 0.24s; }
[data-testid="stVerticalBlock"] > div:nth-child(10) { animation-delay: 0.27s; }
[data-testid="stVerticalBlock"] > div:nth-child(n+11) { animation-delay: 0.30s; }

@media (max-width: 768px) {
    .tools-grid { grid-template-columns: 1fr; }
    .ilp-hero h1 { font-size: 1.55rem !important; }
    .page-head { padding: 24px 14px 18px; }
    .page-head h2 { font-size: 1.25rem !important; }
    .ilp-hero-icon { width: 60px; height: 60px; font-size: 28px; border-radius: 14px; }
    .ilp-step-line { width: 24px; }
    .ilp-step-label { font-size: 0.62rem; }
    .ilp-step-num { width: 32px; height: 32px; font-size: 0.75rem; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] {
        padding: 16px 14px !important;
    }
    .card-head-icon, .upload-head-icon, .page-head-icon {
        width: 44px; height: 44px; font-size: 20px;
    }
}
"""


def inject_css():
    st.markdown(f"<style>{THEME_CSS}</style>", unsafe_allow_html=True)


def inject_sidebar_brand():
    st.sidebar.markdown(
        """
        <div style="padding: 10px 0 16px; border-bottom: 1px solid rgba(0,240,255,0.28); margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 11px;">
                <div style="width:40px; height:40px;
                            background:linear-gradient(135deg,#00f0ff,#ff007f);
                            border:1px solid rgba(255,255,255,0.4);
                            border-radius:10px; display:flex; align-items:center; justify-content:center;
                            font-size:19px;
                            box-shadow:0 0 18px rgba(0,240,255,0.55), 0 0 12px rgba(255,0,127,0.45);">⚡</div>
                <div>
                    <div style="font-family:'Orbitron',sans-serif; font-weight:800; font-size:0.86rem;
                                color:#00f0ff; letter-spacing:0.05em;
                                text-shadow:0 0 10px rgba(0,240,255,0.65);">TEAZZI QC</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.63rem;
                                color:#ff007f; letter-spacing:0.12em; text-transform:uppercase;
                                text-shadow:0 0 8px rgba(255,0,127,0.6);">CYBERPUNK // NEON</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_footer():
    st.markdown(
        """
        <div style="text-align:center; padding:28px 0 16px; margin-top:44px;
                    border-top:1px solid rgba(0,240,255,0.26);
                    box-shadow:inset 0 1px 0 rgba(255,0,127,0.20);">
            <p style="font-family:'JetBrains Mono',monospace; color:#6c80ad;
                      font-size:0.75rem; margin:0; line-height:2; letter-spacing:0.04em;">
                TEAZZI AUDIT &amp; QC TOOLKIT // <span style="color:#00f0ff;">CYBERPUNK NEON EDITION</span><br>
                Built with
                <span style="color:#00f0ff; font-weight:700; text-shadow:0 0 8px rgba(0,240,255,0.65);">AI</span>
                &amp;
                <span style="color:#ff007f; font-weight:700; text-shadow:0 0 8px rgba(255,0,127,0.65);">GJorma</span>
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
