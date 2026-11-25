"""
Halaman Panduan & Dokumentasi Interaktif di dalam aplikasi Streamlit.

Menyajikan panduan pemakaian semua halaman, cara tambah/hapus provider AI,
kustomisasi template/checklist/tema, serta troubleshooting — lengkap dengan
tombol unduh file DOCS.md.
"""

from pathlib import Path

import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer

st.set_page_config(
    page_title="Panduan & Docs",
    page_icon="📖",
    layout="wide",
)

inject_css()
inject_sidebar_brand()

# ── PAGE HEADER ───────────────────────────────────────────
st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">📖</div>
        <h2>Panduan &amp; Dokumentasi</h2>
        <p>
            Cara penggunaan seluruh modul Audit &amp; Reimburse, cara tambah/hapus
            provider AI, kustomisasi template, dan troubleshooting cepat.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tombol download DOCS.md langsung dari web jika tersedia
docs_path = Path(__file__).resolve().parent.parent / "DOCS.md"
if docs_path.is_file():
    col_info, col_dl = st.columns([3, 1])
    with col_info:
        st.caption(
            "Dokumentasi versi lengkap (All-in-One) tersimpan di `DOCS.md` pada repositori GitHub."
        )
    with col_dl:
        st.download_button(
            "📥 Download DOCS.md",
            data=docs_path.read_text(encoding="utf-8"),
            file_name="DOCS.md",
            mime="text/markdown",
            use_container_width=True,
        )

# ── TABS INTERAKTIF ───────────────────────────────────────
tab_quick, tab_pages, tab_provider, tab_custom, tab_trouble = st.tabs(
    [
        "🚀 Alur Cepat & Tips",
        "📋 Panduan Halaman (1–8)",
        "🔌 Kelola Provider AI",
        "⚙️ Template & Tema",
        "🛠️ Troubleshooting",
    ]
)

# ── TAB 1: ALUR CEPAT & TIPS ──────────────────────────────
with tab_quick:
    c_audit, c_reim = st.columns(2)
    with c_audit:
        st.markdown(
            """
            <div class="card-head">
                <div class="card-head-icon">🔍</div>
                <h3>Alur Audit &amp; QC Store</h3>
                <p>Dari catatan lapangan sampai Excel final lengkap dengan foto &amp; TTD</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            1. Buka **Detail Audit (AI)** → pilih provider → klik **`🔍 Scan`** *(0 token)*.
            2. *(Opsional)* Klik **`🩺 Test`** untuk menyaring hanya model yang hidup *(tersimpan lintas tab & device)*.
            3. Paste temuan bebas → klik **`🤖 Proses dengan AI`** → review & edit remarks.
            4. Klik **`✅ Terapkan ke DETAIL AUDIT`** → lengkapi header toko/auditor/PIC.
            5. Klik ikon **`💾`** (kiri bawah) untuk simpan draft ke Supabase.
            6. Buka **QC Image Inserter** → pilih **`Dari Draft DETAIL AUDIT`** → upload foto QC & TTD → Export Excel.
            """
        )

    with c_reim:
        st.markdown(
            """
            <div class="card-head">
                <div class="card-head-icon">🧾</div>
                <h3>Alur Reimburse Scanner</h3>
                <p>OCR struk bulanan &amp; Flazz jadi Excel kronologis + PDF lossless</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            1. Buka **Reimburse Scanner** → cek/isi **Data Pemohon** di sidebar kiri.
            2. Pilih **Provider** & **Model Vision** *(cek expander referensi hemat token)*.
            3. Upload foto struk fisik (kiri) dan screenshot mutasi Flazz *(kanan, opsional)*.
            4. Klik **`🚀 Mulai Proses OCR, Sorting, Generate Excel & PDF`**.
            5. Cek tabel hasil, total nominal, dan lokasi EXIF GPS.
            6. Klik **`📊 Proses Excel`** & **`🧾 Proses PDF`**, lalu klik tombol **Download** yang muncul.
            """
        )

    st.markdown("---")
    t1, t2 = st.columns(2)
    with t1:
        st.info(
            "**💡 Tips Hemat Token AI**\n\n"
            "- Di `Detail Audit (AI)`, klik **`🔍 Scan`** hanya mengambil daftar model (**0 token**).\n"
            "- Gunakan **`🩺 Test`** hanya saat perlu cek kesehatan provider; hasilnya otomatis tersimpan untuk semua tab & device lain.\n"
            "- Di `Reimburse Scanner`, pilih model vision hemat token sesuai tabel referensi di halaman tersebut."
        )
    with t2:
        st.warning(
            "**📱 Tips Upload Foto dari HP**\n\n"
            "- Pilih foto dari **Gallery bawaan HP** atau **File Manager** (hindari Google Photos langsung agar tidak putus koneksi).\n"
            "- Jika sempat *reconnecting*, tunggu beberapa detik lalu ulangi atau tekan **Hapus Semua Foto (Reset)**."
        )

# ── TAB 2: PANDUAN TIAP HALAMAN ───────────────────────────
with tab_pages:
    st.caption("Klik tiap bagian di bawah untuk melihat panduan langkah demi langkah.")

    with st.expander("1️⃣ Detail Audit (AI) — Pemetaan Temuan Otomatis", expanded=True):
        st.markdown(
            """
            - **`🔍 Scan`**: mengambil semua raw model ID dari endpoint `/models` tanpa memakan token.
            - **`🩺 Test`**: melakukan ping test + ukur latensi ke tiap model, lalu menyaring dropdown agar **hanya menampilkan model yang hidup** (tersimpan di cache bersama lintas tab & device).
            - **Review Usulan**: centang/lepas centang item sebelum diterapkan. Catatan yang tidak cocok masuk ke daftar **`unmatched`** dan bisa diunduh sebagai `.txt`.
            - Tombol **`✅ Terapkan ke DETAIL AUDIT`** otomatis membuat draft baru di halaman 2.
            """
        )

    with st.expander("2️⃣ Detail Audit Manual — 130 Checklist & Skor Real-Time"):
        st.markdown(
            """
            - Isi kolom **Remarks** bila ada temuan → **Actual Score** item tersebut otomatis menjadi **`0`** (jika kosong mendapat nilai penuh `Basic`).
            - Bobot nilai: **SERVICE (30%)**, **FOOD SAFETY (40%)**, **CLEANLINESS (30%)**. Item `#58 (Putar musik)` dikecualikan sesuai rumus Excel.
            - Grade otomatis: `≥96` **A** | `≥91` **B+** | `≥86` **B** | `≥81` **B-** | `<81` **C**.
            - Gunakan **`✏️ Update Draft Ini`** jika ingin mengganti Store Name / Date pada draft yang sedang dimuat tanpa membuat draft baru.
            - Floating bar kiri bawah: **`💾`** simpan draft ke Supabase, **`⬇️`** download `.xlsx`. Tombol **`▲ / ▼`** di kanan untuk scroll cepat.
            """
        )

    with st.expander("3️⃣ QC Image Inserter — Foto Massal & Tanda Tangan"):
        st.markdown(
            """
            - Mendukung 3 sumber template: **Dari Draft DETAIL AUDIT**, **File Preset (`presets/`)**, dan **Upload Manual**.
            - Kapasitas foto **unlimited**: jika foto melebihi slot layout default (`6 kolom × 25 baris`), baris baru ditambahkan otomatis dengan ukuran identik.
            - Foto otomatis diurutkan berdasarkan timestamp nama file, dikoreksi rotasi EXIF, dan dikompres JPEG 1280px.
            - Tanda tangan Auditor & PIC ditempel ke `A166` / `D166` (nama di `A167` / `D167`), bisa dikustomisasi di mode `Custom`.
            """
        )

    with st.expander("4️⃣ Cek Model AI — Diagnostik Provider & BYOK"):
        st.markdown(
            """
            - Berguna untuk menguji validitas API key, melihat semua model di server, dan mengukur latensi tiap model.
            - API key yang berasal dari Secrets otomatis disembunyikan (`•••••••• [Terisi dari Secrets]`).
            - Mendukung input bebas URL + API key lewat preset **`Custom / Manual Input (BYOK)`**.
            """
        )

    with st.expander("5️⃣ Reimburse Scanner — OCR Struk + Flazz → Excel & PDF"):
        st.markdown(
            """
            - Kategori otomatis: **bensin** (jenis BBM + liter), **drink** (minuman + outlet), **parkir** (nama lokasi / fallback otomatis dari **EXIF GPS**).
            - **Dedup Flazz**: baris *Top Up* selalu dilewati; transaksi parkir Flazz yang tanggal & nominalnya sama dengan struk fisik atau dobel antar-screenshot otomatis di-skip.
            - Nama file otomatis mengikuti bulan & tahun data: `Reimburse [Bulan] [Tahun].xlsx` & `Invoice [Bulan] [Tahun].pdf` (PDF lossless tanpa kompresi).
            """
        )

    with st.expander("6️⃣–8️⃣ Admin Data, Audit Log, & Traffic Log"):
        st.markdown(
            """
            - **Admin Data (`6_Admin_Hapus_Data`)**: login `ADMIN_PASSWORD` untuk filter, edit metadata draft, hapus satuan, atau hapus semua draft (konfirmasi ketik `HAPUS`).
            - **Audit Log (`7_Audit_Log`)**: login `TRAFFIC_LOG_PASSWORD` untuk pantau & hapus riwayat `Save`, `Update`, `Download` (waktu WIB).
            - **Traffic Log (`8_Traffic_Log`)**: login `TRAFFIC_LOG_PASSWORD` untuk tampilan *read-only* riwayat pemakaian aplikasi.
            """
        )

# ── TAB 3: KELOLA PROVIDER AI ─────────────────────────────
with tab_provider:
    st.markdown("#### Cheat Sheet: 4 Tempat untuk Tambah / Hapus Provider AI")
    st.markdown(
        """
        | # | File / Lokasi | Yang Diubah |
        |:-:|---|---|
        | 1 | `.streamlit/secrets.toml` *(+ Streamlit Cloud Secrets)* | Tambah/hapus `<PREFIX>_API_KEY` *(+ `<PREFIX>_BASE_URL` bila perlu)* |
        | 2 | `llm_core.py` | `PROVIDER_LIST`, `_GENERIC_GATEWAYS`, `FALLBACK_MODELS` |
        | 3 | `reim_llm_core.py` | `_PROVIDER_DEFS` *(+ `_PROVIDER_EXTRA_FALLBACK` bila perlu)* |
        | 4 | `pages/4_Cek_Model_AI.py` | `PRESET_PROVIDERS` |
        """
    )

    st.markdown("#### ➕ Contoh Menambah Provider Baru (`NovaAI`)")
    st.code(
        """# 1) .streamlit/secrets.toml
NOVAAI_API_KEY = "sk-isi-api-key-kamu"

# 2) llm_core.py
PROVIDER_LIST = [..., "NovaAI Proxy", "BYOK (Custom)"]
_GENERIC_GATEWAYS["NovaAI Proxy"] = ("NOVAAI", "https://api.novaai.id/v1")
FALLBACK_MODELS["NovaAI Proxy"] = {
    "deepseek-v4.1-flash": {"provider": "novaai", "model": "deepseek-v4.1-flash"},
}

# 3) reim_llm_core.py
_PROVIDER_DEFS = [..., ("NovaAI", "NOVAAI", "https://api.novaai.id/v1")]

# 4) pages/4_Cek_Model_AI.py
PRESET_PROVIDERS["NovaAI"] = {
    "url": "https://api.novaai.id/v1",
    "secret": "NOVAAI_API_KEY",
}""",
        language="python",
    )

    c_del, c_byok = st.columns(2)
    with c_del:
        st.markdown("#### 🗑️ Cara Menghapus Provider")
        st.markdown(
            """
            1. Hapus entri provider dari **`llm_core.py`** (`PROVIDER_LIST`, `_GENERIC_GATEWAYS`, `FALLBACK_MODELS`).
            2. Hapus barisnya dari **`reim_llm_core.py`** (`_PROVIDER_DEFS`).
            3. Hapus dari **`pages/4_Cek_Model_AI.py`** (`PRESET_PROVIDERS`).
            4. Hapus key `<PREFIX>_API_KEY` dari **Secrets**.
            *(Tip: di Reimburse Scanner, cukup kosongkan API key di Secrets untuk menyembunyikan provider sementara tanpa ubah kode.)*
            """
        )
    with c_byok:
        st.markdown("#### 🔑 Pakai BYOK Tanpa Edit Kode")
        st.markdown(
            """
            - Di **`Detail Audit (AI)`**, pilih **`BYOK (Custom)`** → masukkan Base URL (`/v1`) & API Key → klik **`💾 Simpan BYOK`** (otomatis ter-share antar device) → klik **`🔍 Scan`** lalu **`🩺 Test`**.
            - Khusus **`9router Proxy`**: URL wajib diisi via `ROUTER9_BASE_URL` di Secrets (tidak di-hardcode di repo).
            """
        )

# ── TAB 4: TEMPLATE, CHECKLIST & TEMA ─────────────────────
with tab_custom:
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("#### 📋 Checklist & Template Audit")
        st.markdown(
            """
            - **`structure.json`**: daftar 130 item (`number`, `row`, `desc`, `basic`).
            - **`template.xlsx`**: jika baris digeser di Excel, field `"row"` di `structure.json` wajib ikut disamakan.
            - **`scoring.py`**: atur bobot `GROUP_WEIGHTS` (`SERVICE 30`, `FOOD SAFETY 40`, `CLEANLINESS 30`) dan batas nilai grade.
            - **`presets/`**: cukup tambah/hapus file `.xlsx` di folder ini untuk daftar preset `QC Image Inserter`.
            """
        )
    with k2:
        st.markdown("#### 🧾 Template Reimburse & 🎨 Tema Neon")
        st.markdown(
            """
            - **`FORM_REIMBURSE_template.xlsx`**: sheet `FORM`, header `C6:C9`, periode `E6:E7`, data mulai baris `12` (auto-insert baris jika > 50 item, logo *grouped-shape* dipertahankan otomatis oleh `reim_excel_core.py`).
            - **Tema Cyberpunk Neon**: edit variabel `:root` (`--bg`, `--cyan: #00f0ff`, `--magenta: #ff007f`) di **`style.py`** dan CSS landing di **`app.py`**.
            """
        )

# ── TAB 5: TROUBLESHOOTING ────────────────────────────────
with tab_trouble:
    st.markdown(
        """
        | Masalah | Penyebab | Solusi Cepat |
        |---|---|---|
        | **`Scan gagal: ... belum diisi`** | Secret API Key / Base URL belum ada. | Isi `<PREFIX>_API_KEY` (+ `ROUTER9_BASE_URL` jika 9router) di Secrets, lalu restart app. |
        | **`HTTP 401 / 403`** | API key salah / expired / saldo habis. | Uji key lewat `4_Cek_Model_AI`, lalu perbarui di Secrets. |
        | **Hasil `Test` hilang keesokan harinya** | Server Streamlit *sleep* / restart sehingga cache memori reset. | Klik **`🔍 Scan`** lalu **`🩺 Test`** sekali lagi — hasil langsung tersimpan lintas tab & device. |
        | **`HTTP 429 Rate Limit`** | Kuota/limit request provider penuh. | Ganti ke model atau provider lain di dropdown. |
        | **Supabase belum terkoneksi** | Secrets kosong atau proyek Supabase *paused*. | Cek dashboard Supabase (unpause) & pastikan `keep-alive.yml` aktif. |
        | **Foto struk gagal OCR** | Foto buram / timeout API vision. | Foto gagal tetap masuk di **akhir PDF**; lengkapi barisnya di Excel bila perlu. |
        """
    )

inject_footer()
