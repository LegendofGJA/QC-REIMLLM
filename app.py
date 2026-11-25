"""
Landing page utama Teazzi Audit & QC Toolkit (versi gabungan).

Berisi dua modul besar:
  1. Audit & QC       -> 130 item checklist, skor berbobot, foto QC, log.
  2. Reimburse Scanner -> OCR struk jadi Excel + PDF bukti gabungan.

Halaman memakai helper `render_html` untuk mencegah parser Markdown
Streamlit memutus blok HTML akibat baris kosong.
"""

import re
from textwrap import dedent
import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer

def render_html(content: str) -> None:
    """Render HTML tanpa membuat parser Markdown Streamlit memutus blok HTML."""
    normalized = dedent(content).strip()
    normalized = re.sub(r"\n\s*\n", "\n", normalized)
    st.markdown(normalized, unsafe_allow_html=True)

st.set_page_config(
    page_title="Teazzi Audit & QC Toolkit",
    page_icon=":material/fact_check:",
    layout="wide",
)

inject_css()
inject_sidebar_brand()

# -- CSS KHUSUS LANDING PAGE (CLASSIC CYBERPUNK NEON: CYAN + MAGENTA) --
st.markdown(
    """
    <style>
    .home-shell { width: 100%; margin: 0 auto; }
    .home-hero {
        position: relative; overflow: hidden; text-align: center;
        padding: 72px 24px 56px; margin: 0 0 32px;
        border: 1px solid rgba(0, 240, 255, 0.45);
        border-radius: 20px;
        background:
            radial-gradient(circle at 14% 18%, rgba(0, 240, 255, 0.28), transparent 36%),
            radial-gradient(circle at 86% 82%, rgba(255, 0, 127, 0.28), transparent 38%),
            radial-gradient(circle at 50% 0%, rgba(255, 0, 127, 0.14), transparent 45%),
            linear-gradient(145deg, rgba(10, 13, 34, 0.96), rgba(5, 5, 14, 0.99));
        box-shadow:
            0 0 42px rgba(0, 240, 255, 0.22),
            0 0 60px rgba(255, 0, 127, 0.16),
            inset 0 1px 0 rgba(0, 240, 255, 0.45),
            inset 0 -1px 0 rgba(255, 0, 127, 0.45);
    }
    .home-hero::before {
        content: ""; position: absolute; inset: 0; pointer-events: none;
        background-image:
            linear-gradient(rgba(0, 240, 255, 0.09) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 0, 127, 0.07) 1px, transparent 1px),
            repeating-linear-gradient(0deg, rgba(0, 240, 255, 0.03) 0px, rgba(0, 240, 255, 0.03) 1px, transparent 1px, transparent 4px);
        background-size: 32px 32px, 32px 32px, 100% 4px;
        mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.9), rgba(0, 0, 0, 0.2));
    }
    .home-hero::after {
        content: ""; position: absolute; left: 10%; right: 10%; bottom: 0; height: 2px;
        background: linear-gradient(90deg, transparent, #00f0ff, #ff007f, transparent);
        box-shadow: 0 0 16px #00f0ff, 0 0 24px #ff007f;
    }
    .home-hero-content { position: relative; z-index: 1; }
    .home-logo-wrap {
        width: 94px; height: 94px; display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 22px;
        border: 2px solid rgba(0, 240, 255, 0.85);
        border-radius: 22px;
        background: linear-gradient(135deg, #00f0ff 0%, #6a00ff 50%, #ff007f 100%);
        box-shadow:
            0 0 34px rgba(0, 240, 255, 0.60),
            0 0 54px rgba(255, 0, 127, 0.48),
            inset 0 1px 0 rgba(255, 255, 255, 0.45);
        color: #fff; font-size: 2.4rem;
        animation: cyberFloat 3.2s ease-in-out infinite;
    }
    .home-eyebrow {
        display: inline-flex; align-items: center; gap: 8px; margin-bottom: 16px;
        padding: 7px 16px;
        color: #00f0ff;
        border: 1px solid rgba(0, 240, 255, 0.55);
        border-radius: 999px;
        background: rgba(0, 240, 255, 0.10);
        box-shadow: 0 0 18px rgba(0, 240, 255, 0.25);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    }
    .home-live-dot {
        width: 8px; height: 8px; border-radius: 50%; background: #00ff9d;
        box-shadow: 0 0 12px #00ff9d, 0 0 20px #00f0ff;
    }
    .home-hero h1 {
        font-family: 'Orbitron', sans-serif !important;
        max-width: 820px; margin: 0 auto 14px !important; color: #ffffff !important;
        font-size: clamp(2rem, 5vw, 3.25rem) !important; font-weight: 900 !important;
        line-height: 1.15 !important; letter-spacing: 0.03em !important;
        text-shadow: 0 0 22px rgba(0, 240, 255, 0.65), 0 0 42px rgba(255, 0, 127, 0.35) !important;
    }
    .home-gradient-text {
        background: linear-gradient(90deg, #00f0ff 0%, #7df9ff 45%, #ff007f 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        filter: drop-shadow(0 0 14px rgba(255, 0, 127, 0.65));
    }
    .home-hero-description {
        max-width: 680px; margin: 0 auto; color: var(--text-sec);
        font-size: 0.98rem; line-height: 1.8;
    }
    .home-hero-badges {
        display: flex; align-items: center; justify-content: center;
        gap: 9px; margin-top: 26px; flex-wrap: wrap;
    }
    .home-hero-badge {
        display: inline-flex; align-items: center; gap: 6px; padding: 7px 13px;
        border: 1px solid rgba(0, 240, 255, 0.42);
        border-radius: 6px;
        color: #d8fbff;
        background: rgba(8, 12, 30, 0.85);
        box-shadow: 0 0 14px rgba(0, 240, 255, 0.16);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.04em;
    }
    .home-hero-badge:nth-child(even) {
        border-color: rgba(255, 0, 127, 0.48);
        color: #ffd1ea;
        box-shadow: 0 0 14px rgba(255, 0, 127, 0.18);
    }

    .home-section-head { margin: 44px 0 22px; text-align: center; }
    .home-section-kicker {
        display: inline-block; margin-bottom: 8px; color: #ff007f;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase;
        text-shadow: 0 0 12px rgba(255, 0, 127, 0.72);
    }
    .home-section-head h2 {
        font-family: 'Orbitron', sans-serif !important;
        margin: 0 0 8px !important; color: #ffffff !important;
        font-size: 1.65rem !important; font-weight: 800 !important; letter-spacing: 0.03em;
        text-shadow: 0 0 16px rgba(0, 240, 255, 0.58);
    }
    .home-section-head p {
        max-width: 600px; margin: 0 auto; color: var(--text-sec);
        font-size: 0.88rem; line-height: 1.65;
    }

    .home-tools-grid {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px; margin: 0 0 24px;
    }
    a.home-tool-link {
        display: block; height: 100%; color: inherit !important;
        text-decoration: none !important; outline: none;
    }
    .home-tool-card {
        position: relative; overflow: hidden; height: 100%; min-height: 295px;
        padding: 26px;
        border: 1px solid rgba(0, 240, 255, 0.36);
        border-radius: 16px;
        background:
            radial-gradient(circle at 100% 0%, rgba(255, 0, 127, 0.14), transparent 45%),
            linear-gradient(155deg, rgba(13, 17, 40, 0.94), rgba(6, 7, 19, 0.98));
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45), 0 0 18px rgba(0, 240, 255, 0.10);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .home-tool-card::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, #00f0ff, #ff007f);
        opacity: 0.85;
    }
    .home-tool-card::after {
        content: ""; position: absolute; right: -45px; bottom: -45px;
        width: 140px; height: 140px; border-radius: 50%;
        background: radial-gradient(circle, rgba(255, 0, 127, 0.20), transparent 70%);
        transition: transform 0.3s ease;
    }
    a.home-tool-link:hover .home-tool-card {
        transform: translateY(-7px);
        border-color: #ff007f;
        box-shadow:
            0 18px 46px rgba(0, 0, 0, 0.55),
            0 0 30px rgba(255, 0, 127, 0.45),
            0 0 22px rgba(0, 240, 255, 0.35);
    }
    a.home-tool-link:hover .home-tool-card::after { transform: scale(1.35); }
    .home-tool-top {
        position: relative; z-index: 1; display: flex;
        align-items: flex-start; justify-content: space-between; margin-bottom: 22px;
    }
    .home-tool-icon {
        width: 58px; height: 58px; display: inline-flex; align-items: center; justify-content: center;
        border: 1px solid rgba(0, 240, 255, 0.55); border-radius: 14px;
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.20), rgba(255, 0, 127, 0.20));
        box-shadow: 0 0 18px rgba(0, 240, 255, 0.30);
        color: #00f0ff; font-size: 1.6rem;
    }
    .home-tool-number {
        color: rgba(0, 240, 255, 0.24);
        font-family: 'Orbitron', monospace;
        font-size: 1.65rem; font-weight: 900;
        text-shadow: 0 0 12px rgba(0, 240, 255, 0.35);
    }
    .home-tool-card h3 {
        position: relative; z-index: 1; margin: 0 0 10px !important;
        font-family: 'Chakra Petch', sans-serif !important;
        color: #ffffff !important; font-size: 1.16rem !important; font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.42);
    }
    .home-tool-card p {
        position: relative; z-index: 1; min-height: 84px; margin: 0 0 20px;
        color: #a6bdd6; font-size: 0.82rem; line-height: 1.65;
    }
    .home-tool-footer {
        position: relative; z-index: 1; display: flex; align-items: center;
        justify-content: space-between; padding-top: 16px;
        border-top: 1px solid rgba(0, 240, 255, 0.22);
    }
    .home-tool-tag {
        display: inline-flex; align-items: center; padding: 5px 11px; border-radius: 6px;
        color: #ff66b2;
        border: 1px solid rgba(255, 0, 127, 0.50);
        background: rgba(255, 0, 127, 0.14);
        box-shadow: 0 0 12px rgba(255, 0, 127, 0.22);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem; font-weight: 800; letter-spacing: 0.06em;
    }
    .home-tool-arrow {
        color: #00f0ff; font-size: 1.15rem; font-weight: 800;
        text-shadow: 0 0 10px #00f0ff;
        transition: transform 0.2s ease, color 0.2s ease;
    }
    a.home-tool-link:hover .home-tool-arrow {
        transform: translateX(6px);
        color: #ff007f;
        text-shadow: 0 0 12px #ff007f;
    }

    .home-stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 26px 0 38px; }
    .home-stat-card {
        padding: 22px 16px; text-align: center;
        border: 1px solid rgba(0, 240, 255, 0.34);
        border-top: 2px solid #00f0ff;
        border-radius: 14px;
        background: linear-gradient(155deg, rgba(12, 16, 38, 0.92), rgba(6, 8, 20, 0.96));
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.12);
    }
    .home-stat-card:nth-child(even) {
        border-color: rgba(255, 0, 127, 0.38);
        border-top-color: #ff007f;
        box-shadow: 0 0 20px rgba(255, 0, 127, 0.14);
    }
    .home-stat-icon { margin-bottom: 8px; font-size: 21px; }
    .home-stat-value {
        font-family: 'Orbitron', sans-serif;
        margin-bottom: 6px; color: #00f0ff; font-size: 1.48rem; font-weight: 800; line-height: 1;
        text-shadow: 0 0 14px rgba(0, 240, 255, 0.72);
    }
    .home-stat-card:nth-child(even) .home-stat-value {
        color: #ff3d9a;
        text-shadow: 0 0 14px rgba(255, 0, 127, 0.72);
    }
    .home-stat-label {
        font-family: 'Chakra Petch', sans-serif;
        color: var(--text-sec); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
    }

    .home-workflow {
        display: flex; flex-wrap: wrap; align-items: center;
        justify-content: center; gap: 12px; padding: 28px 20px;
        border: 1px solid rgba(0, 240, 255, 0.36);
        border-radius: 18px;
        background:
            radial-gradient(circle at 15% 50%, rgba(0, 240, 255, 0.12), transparent 40%),
            radial-gradient(circle at 85% 50%, rgba(255, 0, 127, 0.12), transparent 40%),
            linear-gradient(145deg, rgba(10, 13, 30, 0.96), rgba(6, 7, 18, 0.98));
        box-shadow: 0 0 28px rgba(0, 240, 255, 0.12);
    }
    .home-workflow-step { width: 126px; text-align: center; }
    .home-workflow-icon {
        width: 54px; height: 54px; display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 10px;
        border: 1px solid rgba(0, 240, 255, 0.55);
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.16), rgba(255, 0, 127, 0.16));
        box-shadow: 0 0 18px rgba(0, 240, 255, 0.28);
        color: #00f0ff; font-size: 1.35rem;
    }
    .home-workflow-title {
        font-family: 'Chakra Petch', sans-serif;
        margin-bottom: 3px; color: #ffffff; font-size: 0.82rem; font-weight: 700;
    }
    .home-workflow-text { color: #8da6c9; font-size: 0.66rem; line-height: 1.45; }
    .home-workflow-arrow {
        color: #ff007f; font-size: 1.3rem; font-weight: 900;
        text-shadow: 0 0 12px rgba(255, 0, 127, 0.8);
    }

    .home-features-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .home-feature {
        display: flex; align-items: flex-start; gap: 14px; padding: 20px;
        border: 1px solid rgba(0, 240, 255, 0.28); border-radius: 14px;
        background: linear-gradient(155deg, rgba(12, 15, 36, 0.90), rgba(7, 9, 22, 0.96));
        transition: border-color 0.22s ease, box-shadow 0.22s ease, transform 0.22s ease;
    }
    .home-feature:hover {
        border-color: #ff007f;
        transform: translateY(-2px);
        box-shadow: 0 0 24px rgba(255, 0, 127, 0.24), 0 0 14px rgba(0, 240, 255, 0.18);
    }
    .home-feature-icon {
        width: 44px; height: 44px; flex: 0 0 44px; display: inline-flex; align-items: center; justify-content: center;
        border-radius: 11px;
        border: 1px solid rgba(0, 240, 255, 0.45);
        background: rgba(0, 240, 255, 0.12);
        box-shadow: 0 0 14px rgba(0, 240, 255, 0.22);
        color: #00f0ff; font-size: 1.15rem;
    }
    .home-feature h4 {
        font-family: 'Chakra Petch', sans-serif !important;
        margin: 0 0 5px; color: #00f0ff !important; font-size: 0.92rem !important; font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
    }
    .home-feature p { margin: 0; color: #a6bdd6; font-size: 0.77rem; line-height: 1.55; }

    .home-secondary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    a.home-secondary-link { color: inherit !important; text-decoration: none !important; }
    .home-secondary-card {
        height: 100%; padding: 20px 16px; text-align: center;
        border: 1px solid rgba(0, 240, 255, 0.30); border-radius: 14px;
        background: linear-gradient(155deg, rgba(12, 15, 36, 0.90), rgba(7, 9, 22, 0.96));
        transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
    }
    a.home-secondary-link:hover .home-secondary-card {
        transform: translateY(-4px);
        border-color: #ff007f;
        box-shadow: 0 0 24px rgba(255, 0, 127, 0.34), 0 0 14px rgba(0, 240, 255, 0.24);
    }
    .home-secondary-icon { margin-bottom: 9px; font-size: 1.5rem; }
    .home-secondary-title {
        font-family: 'Chakra Petch', sans-serif;
        margin-bottom: 5px; color: #00f0ff; font-size: 0.86rem; font-weight: 700;
        text-shadow: 0 0 8px rgba(0, 240, 255, 0.45);
    }
    .home-secondary-desc { color: #96aecb; font-size: 0.7rem; line-height: 1.45; }

    .home-cta {
        position: relative; overflow: hidden; margin: 46px 0 10px; padding: 34px 24px; text-align: center;
        border: 1px solid rgba(255, 0, 127, 0.55); border-radius: 18px;
        background:
            radial-gradient(circle at 20% 100%, rgba(0, 240, 255, 0.24), transparent 50%),
            radial-gradient(circle at 80% 100%, rgba(255, 0, 127, 0.28), transparent 50%),
            rgba(9, 11, 26, 0.94);
        box-shadow: 0 0 36px rgba(255, 0, 127, 0.20), 0 0 28px rgba(0, 240, 255, 0.16);
    }
    .home-cta h3 {
        font-family: 'Orbitron', sans-serif !important;
        margin: 0 0 8px !important; color: #ffffff !important;
        font-size: 1.28rem !important; font-weight: 800 !important;
        text-shadow: 0 0 16px rgba(0, 240, 255, 0.65), 0 0 24px rgba(255, 0, 127, 0.45);
    }
    .home-cta p { margin: 0; color: var(--text-sec); font-size: 0.84rem; line-height: 1.6; }

    @media (max-width: 900px) {
        .home-tools-grid { grid-template-columns: 1fr; }
        .home-secondary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .home-workflow { flex-direction: column; }
        .home-workflow-arrow { transform: rotate(90deg); }
    }
    @media (max-width: 640px) {
        .home-hero { padding: 48px 17px 38px; border-radius: 16px; }
        .home-stats-grid, .home-features-grid, .home-secondary-grid { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -- HERO --
render_html(
    """
    <main class="home-shell">
        <section class="home-hero">
            <div class="home-hero-content">
                <div class="home-logo-wrap">&#128203;</div>
                <div><span class="home-eyebrow">
                    <span class="home-live-dot"></span>
                    Internal Quality Control Platform
                </span></div>
                <h1>
                    Teazzi <span class="home-gradient-text">Audit &amp; QC</span>
                    Toolkit
                </h1>
                <p class="home-hero-description">
                    Platform terpadu untuk membantu auditor memetakan temuan,
                    menghitung nilai audit, menyimpan draft, menyusun foto QC,
                    dan menghasilkan laporan Excel resmi secara lebih cepat,
                    konsisten, dan terstruktur &mdash; plus modul scan struk
                    reimburse jadi Excel &amp; PDF.
                </p>
                <div class="home-hero-badges">
                    <span class="home-hero-badge">Multi-LLM Mapping</span>
                    <span class="home-hero-badge">130 Audit Items</span>
                    <span class="home-hero-badge">10+ Provider AI</span>
                    <span class="home-hero-badge">Bulk Image Processing</span>
                    <span class="home-hero-badge">Cloud Draft</span>
                    <span class="home-hero-badge">OCR Reimburse &rarr; Invoice</span>
                </div>
            </div>
        </section>
    </main>
    """
)

# -- PRIMARY NAVIGATION --
render_html(
    """
    <section class="home-section-head">
        <span class="home-section-kicker">Mulai bekerja</span>
        <h2>Pilih Workflow Utama</h2>
        <p>
            Gunakan bantuan AI untuk proses tercepat, isi checklist secara
            manual, susun foto ke laporan Excel, atau pindai struk reimburse
            dalam satu alur.
        </p>
    </section>

    <div class="home-tools-grid">
        <a href="/Detail_Audit_LLM" class="home-tool-link" target="_self" aria-label="Buka Detail Audit dengan AI">
            <article class="home-tool-card">
                <div class="home-tool-top">
                    <div class="home-tool-icon">&#129302;</div>
                    <div class="home-tool-number">01</div>
                </div>
                <h3>Detail Audit dengan AI</h3>
                <p>
                    Paste catatan temuan bebas dan biarkan Multi-LLM
                    mengusulkan pemetaan ke 130 item checklist resmi.
                    Semua hasil tetap dapat direview dan diedit sebelum dipakai.
                </p>
                <div class="home-tool-footer">
                    <span class="home-tool-tag">REKOMENDASI UTAMA</span>
                    <span class="home-tool-arrow">&rarr;</span>
                </div>
            </article>
        </a>

        <a href="/Detail_Audit" class="home-tool-link" target="_self" aria-label="Buka Detail Audit Manual">
            <article class="home-tool-card">
                <div class="home-tool-top">
                    <div class="home-tool-icon">&#128203;</div>
                    <div class="home-tool-number">02</div>
                </div>
                <h3>Detail Audit Manual</h3>
                <p>
                    Isi nilai dan remarks langsung pada setiap checklist.
                    Skor serta grade dihitung otomatis dan progres dapat
                    disimpan sebagai draft di Supabase.
                </p>
                <div class="home-tool-footer">
                    <span class="home-tool-tag">INPUT CHECKLIST</span>
                    <span class="home-tool-arrow">&rarr;</span>
                </div>
            </article>
        </a>

        <a href="/QC_Image_Inserter" class="home-tool-link" target="_self" aria-label="Buka QC Image Inserter">
            <article class="home-tool-card">
                <div class="home-tool-top">
                    <div class="home-tool-icon">&#128248;</div>
                    <div class="home-tool-number">03</div>
                </div>
                <h3>QC Image Inserter</h3>
                <p>
                    Upload foto temuan secara massal, kompres otomatis,
                    tambahkan tanda tangan, dan susun seluruh bukti ke
                    template Excel pada posisi yang sudah ditentukan.
                </p>
                <div class="home-tool-footer">
                    <span class="home-tool-tag">GENERATE EXCEL</span>
                    <span class="home-tool-arrow">&rarr;</span>
                </div>
            </article>
        </a>

        <a href="/Cek_Model_AI" class="home-tool-link" target="_self" aria-label="Buka Cek Model AI">
            <article class="home-tool-card">
                <div class="home-tool-top">
                    <div class="home-tool-icon">&#129658;</div>
                    <div class="home-tool-number">04</div>
                </div>
                <h3>Cek Model AI</h3>
                <p>
                    Periksa ketersediaan provider, validitas API key, dan
                    daftar model AI yang aktif sebelum dipakai untuk
                    pemrosesan temuan maupun OCR struk.
                </p>
                <div class="home-tool-footer">
                    <span class="home-tool-tag">DIAGNOSTIK</span>
                    <span class="home-tool-arrow">&rarr;</span>
                </div>
            </article>
        </a>

        <a href="/Reimburse_Scanner" class="home-tool-link" target="_self" aria-label="Buka Reimburse Scanner">
            <article class="home-tool-card">
                <div class="home-tool-top">
                    <div class="home-tool-icon">&#129534;</div>
                    <div class="home-tool-number">05</div>
                </div>
                <h3>Reimburse Scanner</h3>
                <p>
                    Upload sebulan foto struk (bensin, parkir, Teazzi) dan screenshot
                    Flazz/e-money. Model vision membaca tiap gambar, mengisi template
                    Excel reimburse secara kronologis, lalu menggabungkan semua bukti
                    asli ke satu PDF tanpa kompresi &mdash; hasilnya
                    <strong>Reimburse [Bulan] [Tahun].xlsx</strong> dan
                    <strong>Invoice [Bulan] [Tahun].pdf</strong>.
                </p>
                <div class="home-tool-footer">
                    <span class="home-tool-tag">MODUL REIMBURSE</span>
                    <span class="home-tool-arrow">&rarr;</span>
                </div>
            </article>
        </a>
    </div>
    """
)

# -- STATS --
render_html(
    """
    <div class="home-stats-grid">
        <div class="home-stat-card">
            <div class="home-stat-icon">&#128203;</div>
            <div class="home-stat-value">130</div>
            <div class="home-stat-label">Checklist Audit</div>
        </div>
        <div class="home-stat-card">
            <div class="home-stat-icon">&#129302;</div>
            <div class="home-stat-value">10+</div>
            <div class="home-stat-label">Provider AI</div>
        </div>
        <div class="home-stat-card">
            <div class="home-stat-icon">&#128444;</div>
            <div class="home-stat-value">Unlimited</div>
            <div class="home-stat-label">Kapasitas Foto QC</div>
        </div>
        <div class="home-stat-card">
            <div class="home-stat-icon">&#129534;</div>
            <div class="home-stat-value">2-in-1</div>
            <div class="home-stat-label">Excel + PDF Reimburse</div>
        </div>
    </div>
    """
)

# -- WORKFLOW --
render_html(
    """
    <section class="home-section-head">
        <span class="home-section-kicker">Alur operasional</span>
        <h2>Dari Temuan ke Laporan Final</h2>
        <p>
            Satu workflow terintegrasi untuk mempercepat proses audit
            tanpa menghilangkan tahap review oleh auditor.
        </p>
    </section>

    <div class="home-workflow">
        <div class="home-workflow-step">
            <div class="home-workflow-icon">&#128221;</div>
            <div class="home-workflow-title">Catat Temuan</div>
            <div class="home-workflow-text">Paste teks mentah atau input manual</div>
        </div>

        <div class="home-workflow-arrow">&rarr;</div>

        <div class="home-workflow-step">
            <div class="home-workflow-icon">&#129302;</div>
            <div class="home-workflow-title">Mapping AI</div>
            <div class="home-workflow-text">Cocokkan ke checklist resmi</div>
        </div>

        <div class="home-workflow-arrow">&rarr;</div>

        <div class="home-workflow-step">
            <div class="home-workflow-icon">&#9989;</div>
            <div class="home-workflow-title">Review &amp; Save</div>
            <div class="home-workflow-text">Validasi hasil lalu simpan draft</div>
        </div>

        <div class="home-workflow-arrow">&rarr;</div>

        <div class="home-workflow-step">
            <div class="home-workflow-icon">&#128248;</div>
            <div class="home-workflow-title">Foto QC</div>
            <div class="home-workflow-text">Susun bukti ke sheet ATTACHMENT</div>
        </div>

        <div class="home-workflow-arrow">&rarr;</div>

        <div class="home-workflow-step">
            <div class="home-workflow-icon">&#129534;</div>
            <div class="home-workflow-title">Scan Reimburse</div>
            <div class="home-workflow-text">OCR struk &rarr; Excel + Invoice PDF</div>
        </div>

        <div class="home-workflow-arrow">&rarr;</div>

        <div class="home-workflow-step">
            <div class="home-workflow-icon">&#128202;</div>
            <div class="home-workflow-title">Log &amp; Audit</div>
            <div class="home-workflow-text">Pantau Audit Log &amp; Traffic Log</div>
        </div>
    </div>
    """
)

# -- FEATURES --
render_html(
    """
    <section class="home-section-head">
        <span class="home-section-kicker">Kemampuan platform</span>
        <h2>Dibuat untuk Workflow QC Retail</h2>
        <p>
            Setiap fitur dirancang untuk mengurangi pekerjaan berulang,
            meminimalkan human error, dan menjaga konsistensi laporan.
        </p>
    </section>

    <div class="home-features-grid">
        <article class="home-feature">
            <div class="home-feature-icon">&#129302;</div>
            <div>
                <h4>Intelligent Finding Mapping</h4>
                <p>
                    Multi-LLM mengubah catatan auditor yang tidak terstruktur
                    menjadi usulan remarks pada item checklist yang sesuai.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#129518;</div>
            <div>
                <h4>Weighted Scoring &amp; Grading</h4>
                <p>
                    Skor dihitung dengan model berbobot SERVICE 30 / FOOD
                    SAFETY 40 / CLEANLINESS 30, identik dengan rumus template
                    Excel. Final Score &amp; Grade (A&ndash;C) muncul real-time.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#9729;&#65039;</div>
            <div>
                <h4>Cloud Draft Management</h4>
                <p>
                    Audit disimpan, dimuat kembali, diperbarui, atau diteruskan
                    ke proses penyusunan foto kapan saja lewat Supabase.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#128202;</div>
            <div>
                <h4>Activity &amp; Traffic Log</h4>
                <p>
                    Seluruh aktivitas audit dan pemakaian QC Image Inserter
                    tercatat otomatis di Supabase, dengan timestamp WIB.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#128247;</div>
            <div>
                <h4>Bulk Photo Processing</h4>
                <p>
                    Puluhan foto dikompres, diurutkan, dan ditempel secara
                    otomatis ke sheet ATTACHMENT tanpa proses manual.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#9997;&#65039;</div>
            <div>
                <h4>Digital Approval</h4>
                <p>
                    Tanda tangan Auditor dan PIC dapat ditambahkan langsung
                    ke cell pengesahan pada workbook final.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#129658;</div>
            <div>
                <h4>AI Model Health Check</h4>
                <p>
                    Periksa ketersediaan provider dan model AI sebelum
                    digunakan untuk pemrosesan temuan audit.
                </p>
            </div>
        </article>

        <article class="home-feature">
            <div class="home-feature-icon">&#129534;</div>
            <div>
                <h4>Receipt OCR &amp; Reimburse</h4>
                <p>
                    Foto struk dibaca model vision, diurutkan kronologis,
                    diisi ke template Excel, dan digabung ke PDF bukti
                    tanpa kompresi.
                </p>
            </div>
        </article>
    </div>
    """
)

# -- SECONDARY NAVIGATION --
render_html(
    """
    <section class="home-section-head">
        <span class="home-section-kicker">Tools pendukung</span>
        <h2>Monitoring &amp; Administrasi</h2>
        <p>
            Buka riwayat aktivitas, kelola draft, atau periksa status
            model AI langsung dari halaman utama.
        </p>
    </section>

    <div class="home-secondary-grid">
        <a href="/Admin_Hapus_Data" class="home-secondary-link" target="_self" aria-label="Buka halaman Admin">
            <div class="home-secondary-card">
                <div class="home-secondary-icon">&#128273;</div>
                <div class="home-secondary-title">Admin Data</div>
                <div class="home-secondary-desc">Edit dan hapus data draft tersimpan</div>
            </div>
        </a>

        <a href="/Audit_Log" class="home-secondary-link" target="_self" aria-label="Buka Audit Log">
            <div class="home-secondary-card">
                <div class="home-secondary-icon">&#128203;</div>
                <div class="home-secondary-title">Audit Log</div>
                <div class="home-secondary-desc">Riwayat Save, Update, dan Download audit</div>
            </div>
        </a>

        <a href="/Traffic_Log" class="home-secondary-link" target="_self" aria-label="Buka Traffic Log">
            <div class="home-secondary-card">
                <div class="home-secondary-icon">&#128225;</div>
                <div class="home-secondary-title">Traffic Log</div>
                <div class="home-secondary-desc">Riwayat penggunaan aplikasi</div>
            </div>
        </a>

        <a href="/Panduan" class="home-secondary-link" target="_self" aria-label="Buka Panduan dan Docs">
            <div class="home-secondary-card">
                <div class="home-secondary-icon">&#128214;</div>
                <div class="home-secondary-title">Panduan &amp; Docs</div>
                <div class="home-secondary-desc">Cara pakai web, kelola provider AI, &amp; FAQ</div>
            </div>
        </a>
    </div>
    """
)

# -- CLOSING CTA --
render_html(
    """
    <section class="home-cta">
        <h3>&#128640; Siap Memulai Proses Audit?</h3>
        <p>
            Pilih salah satu workflow utama di atas atau gunakan menu
            sidebar untuk membuka seluruh halaman aplikasi.
        </p>
    </section>
    """
)

inject_footer()
