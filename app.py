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

from style import inject_css, inject_footer

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

# -- CSS KHUSUS LANDING PAGE --
st.markdown(
    """
    <style>
    .home-shell { width: 100%; margin: 0 auto; }
    .home-hero {
        position: relative; overflow: hidden; text-align: center;
        padding: 72px 24px 54px; margin: 0 0 30px;
        border: 1px solid var(--border); border-radius: 24px;
        background:
            radial-gradient(circle at 15% 20%, rgba(229, 50, 45, 0.18), transparent 28%),
            radial-gradient(circle at 85% 80%, rgba(229, 50, 45, 0.10), transparent 30%),
            linear-gradient(145deg, rgba(25, 25, 48, 0.95), rgba(11, 11, 18, 0.98));
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.25);
    }
    .home-hero::before {
        content: ""; position: absolute; inset: 0; pointer-events: none;
        background-image:
            linear-gradient(rgba(255, 255, 255, 0.018) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.018) 1px, transparent 1px);
        background-size: 34px 34px;
        mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), transparent);
    }
    .home-hero-content { position: relative; z-index: 1; }
    .home-logo-wrap {
        width: 92px; height: 92px; display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 22px; border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 25px;
        background: linear-gradient(135deg, #E5322D, #ff675f);
        box-shadow: 0 18px 50px rgba(229, 50, 45, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.20);
        color: #fff; font-size: 2.4rem;
    }
    .home-eyebrow {
        display: inline-flex; align-items: center; gap: 7px; margin-bottom: 14px;
        padding: 7px 13px; color: #fca5a5; border: 1px solid rgba(229, 50, 45, 0.24);
        border-radius: 999px; background: rgba(229, 50, 45, 0.09);
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase;
    }
    .home-live-dot {
        width: 7px; height: 7px; border-radius: 50%; background: #10b981;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
    }
    .home-hero h1 {
        max-width: 760px; margin: 0 auto 14px !important; color: var(--text) !important;
        font-size: clamp(2rem, 5vw, 3.2rem) !important; font-weight: 800 !important;
        line-height: 1.12 !important; letter-spacing: -0.045em !important;
    }
    .home-gradient-text {
        background: linear-gradient(90deg, #ff7770, #E5322D);
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .home-hero-description {
        max-width: 670px; margin: 0 auto; color: var(--text-sec);
        font-size: 1rem; line-height: 1.8;
    }
    .home-hero-badges {
        display: flex; align-items: center; justify-content: center;
        gap: 9px; margin-top: 24px; flex-wrap: wrap;
    }
    .home-hero-badge {
        display: inline-flex; align-items: center; gap: 6px; padding: 7px 12px;
        border: 1px solid var(--border); border-radius: 999px; color: var(--text-sec);
        background: rgba(18, 18, 32, 0.72); backdrop-filter: blur(8px);
        font-size: 0.72rem; font-weight: 600;
    }
    .home-section-head { margin: 42px 0 20px; text-align: center; }
    .home-section-kicker {
        display: inline-block; margin-bottom: 8px; color: var(--accent);
        font-size: 0.72rem; font-weight: 800; letter-spacing: 0.11em; text-transform: uppercase;
    }
    .home-section-head h2 {
        margin: 0 0 8px !important; color: var(--text) !important;
        font-size: 1.65rem !important; font-weight: 800 !important; letter-spacing: -0.025em;
    }
    .home-section-head p {
        max-width: 600px; margin: 0 auto; color: var(--text-muted);
        font-size: 0.88rem; line-height: 1.65;
    }
    .home-tools-grid {
        display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px; margin: 0 0 22px;
    }
    a.home-tool-link {
        display: block; height: 100%; color: inherit !important;
        text-decoration: none !important; outline: none;
    }
    .home-tool-card {
        position: relative; overflow: hidden; height: 100%; min-height: 290px;
        padding: 26px; border: 1px solid var(--border); border-radius: 20px;
        background: linear-gradient(145deg, rgba(25, 25, 48, 0.88), rgba(18, 18, 32, 0.96));
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .home-tool-card::after {
        content: ""; position: absolute; right: -45px; bottom: -45px;
        width: 135px; height: 135px; border-radius: 50%;
        background: rgba(229, 50, 45, 0.07); transition: transform 0.3s ease;
    }
    a.home-tool-link:hover .home-tool-card {
        transform: translateY(-7px); border-color: rgba(229, 50, 45, 0.72);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.28), 0 8px 30px rgba(229, 50, 45, 0.10);
    }
    a.home-tool-link:hover .home-tool-card::after { transform: scale(1.25); }
    .home-tool-top {
        position: relative; z-index: 1; display: flex;
        align-items: flex-start; justify-content: space-between; margin-bottom: 24px;
    }
    .home-tool-icon {
        width: 58px; height: 58px; display: inline-flex; align-items: center; justify-content: center;
        border: 1px solid rgba(229, 50, 45, 0.20); border-radius: 16px;
        background: var(--accent-soft); color: var(--accent); font-size: 1.6rem;
    }
    .home-tool-number {
        color: rgba(255, 255, 255, 0.12); font-family: "JetBrains Mono", monospace;
        font-size: 1.7rem; font-weight: 800;
    }
    .home-tool-card h3 {
        position: relative; z-index: 1; margin: 0 0 10px !important;
        color: var(--text) !important; font-size: 1.12rem !important; font-weight: 750 !important;
    }
    .home-tool-card p {
        position: relative; z-index: 1; min-height: 84px; margin: 0 0 20px;
        color: var(--text-muted); font-size: 0.82rem; line-height: 1.65;
    }
    .home-tool-footer {
        position: relative; z-index: 1; display: flex; align-items: center;
        justify-content: space-between; padding-top: 16px; border-top: 1px solid var(--border);
    }
    .home-tool-tag {
        display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px;
        color: #fca5a5; background: rgba(229, 50, 45, 0.10);
        font-size: 0.67rem; font-weight: 800; letter-spacing: 0.05em;
    }
    .home-tool-arrow { color: var(--accent); font-size: 1.05rem; transition: transform 0.2s ease; }
    a.home-tool-link:hover .home-tool-arrow { transform: translateX(5px); }
    .home-stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 24px 0 38px; }
    .home-stat-card { padding: 20px 16px; text-align: center; border: 1px solid var(--border); border-radius: 15px; background: var(--surface); }
    .home-stat-icon { margin-bottom: 8px; font-size: 20px; color: var(--accent); }
    .home-stat-value { margin-bottom: 5px; color: var(--text); font-size: 1.45rem; font-weight: 800; line-height: 1; }
    .home-stat-label { color: var(--text-muted); font-size: 0.7rem; font-weight: 600; }
    .home-workflow {
        display: grid; grid-template-columns: repeat(7, auto); align-items: center;
        justify-content: center; gap: 12px; padding: 28px 20px;
        border: 1px solid var(--border); border-radius: 20px;
        background: linear-gradient(145deg, rgba(18, 18, 32, 0.96), rgba(25, 25, 48, 0.72));
    }
    .home-workflow-step { width: 130px; text-align: center; }
    .home-workflow-icon {
        width: 52px; height: 52px; display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 10px; border: 1px solid rgba(229, 50, 45, 0.18);
        border-radius: 15px; background: var(--accent-soft); color: var(--accent); font-size: 1.3rem;
    }
    .home-workflow-title { margin-bottom: 3px; color: var(--text); font-size: 0.78rem; font-weight: 750; }
    .home-workflow-text { color: var(--text-muted); font-size: 0.64rem; line-height: 1.4; }
    .home-workflow-arrow { color: var(--accent); font-size: 1.2rem; font-weight: 800; }
    .home-features-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .home-feature { display: flex; align-items: flex-start; gap: 14px; padding: 20px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); transition: border-color 0.2s ease, background 0.2s ease; }
    .home-feature:hover { border-color: var(--border-hover); background: var(--surface-2); }
    .home-feature-icon { width: 42px; height: 42px; flex: 0 0 42px; display: inline-flex; align-items: center; justify-content: center; border-radius: 12px; background: var(--accent-soft); color: var(--accent); font-size: 1.1rem; }
    .home-feature h4 { margin: 0 0 5px; color: var(--text); font-size: 0.88rem; font-weight: 750; }
    .home-feature p { margin: 0; color: var(--text-muted); font-size: 0.75rem; line-height: 1.55; }
    .home-secondary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
    a.home-secondary-link { color: inherit !important; text-decoration: none !important; }
    .home-secondary-card { height: 100%; padding: 18px 15px; text-align: center; border: 1px solid var(--border); border-radius: 15px; background: var(--surface); transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease; }
    a.home-secondary-link:hover .home-secondary-card { transform: translateY(-4px); border-color: rgba(229, 50, 45, 0.60); background: var(--surface-2); }
    .home-secondary-icon { margin-bottom: 9px; font-size: 1.4rem; color: var(--accent); }
    .home-secondary-title { margin-bottom: 5px; color: var(--text); font-size: 0.78rem; font-weight: 750; }
    .home-secondary-desc { color: var(--text-muted); font-size: 0.65rem; line-height: 1.45; }
    .home-cta { position: relative; overflow: hidden; margin: 46px 0 10px; padding: 32px 24px; text-align: center; border: 1px solid rgba(229, 50, 45, 0.20); border-radius: 20px; background: radial-gradient(circle at 50% 120%, rgba(229, 50, 45, 0.18), transparent 50%), var(--surface); }
    .home-cta h3 { margin: 0 0 7px !important; color: var(--text) !important; font-size: 1.25rem !important; font-weight: 800 !important; }
    .home-cta p { margin: 0; color: var(--text-muted); font-size: 0.8rem; line-height: 1.6; }
    @media (max-width: 900px) { .home-tools-grid { grid-template-columns: 1fr; } .home-secondary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .home-workflow { grid-template-columns: 1fr; } .home-workflow-arrow { transform: rotate(90deg); } }
    @media (max-width: 640px) { .home-hero { padding: 48px 17px 38px; border-radius: 18px; } .home-stats-grid, .home-features-grid, .home-secondary-grid { grid-template-columns: 1fr; } }
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
                    <span class="home-hero-badge">Bulk Image Processing</span>
                    <span class="home-hero-badge">Cloud Draft</span>
                    <span class="home-hero-badge">OCR Reimburse</span>
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
                    asli ke satu PDF tanpa kompresi.
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
            <div class="home-stat-value">5</div>
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
            <div class="home-workflow-icon">&#128194;</div>
            <div class="home-workflow-title">Export Excel</div>
            <div class="home-workflow-text">Tambahkan foto dan unduh laporan</div>
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
