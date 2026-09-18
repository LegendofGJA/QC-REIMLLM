LLLL<div align="center">

# 🧾 Teazzi Audit & QC Toolkit

**Platform terpadu untuk Audit Store, Quality Control, dan Reimburse Struk.**

Multi-LLM finding mapping · 130-item checklist · bulk QC photos · OCR struk → Excel & Invoice PDF.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Cloud%20Draft-3ECF8E?logo=supabase&logoColor=white)
![Status](https://img.shields.io/badge/status-active-success)

</div>

---

## 📦 Dua Modul, Satu Aplikasi

| Modul | Isi |
|---|---|
| 🔍 **Audit & QC Toolkit** | Checklist 130 item, skor berbobot, foto QC massal, draft cloud, activity log |
| 🧾 **Reimburse Scanner** | OCR struk → Excel reimburse + PDF invoice gabungan (tanpa kompresi) |

Kedua modul dijalankan dari satu aplikasi Streamlit, tetapi **kode core-nya
tetap terpisah**: file audit tanpa prefix, file reimburse ber-prefix `reim_`.

---

## 🗂️ Urutan Halaman (Sidebar)

| # | File | Halaman | Fungsi |
|---|------|---------|--------|
| 1 | `pages/1_Detail_Audit_LLM.py` | 🤖 **Detail Audit (AI)** | Mapping temuan bebas ke 130 checklist pakai Multi-LLM |
| 2 | `pages/2_Detail_Audit.py` | 📋 **Detail Audit Manual** | Input checklist manual + skor & grade otomatis |
| 3 | `pages/3_QC_Image_Inserter.py` | 📸 **QC Image Inserter** | Tempel foto QC massal ke template Excel |
| 4 | `pages/4_Cek_Model_AI.py` | 🩺 **Cek Model AI** | Tes provider, API key, dan model yang tersedia |
| 5 | `pages/5_Reimburse_Scanner.py` | 🧾 **Reimburse Scanner** | OCR struk → Excel + Invoice PDF |
| 6 | `pages/6_Admin_Hapus_Data.py` | 🔑 **Admin Data** | Edit / hapus draft audit (password) |
| 7 | `pages/7_Audit_Log.py` | 📜 **Audit Log** | Riwayat save / update / download audit |
| 8 | `pages/8_Traffic_Log.py` | 📡 **Traffic Log** | Riwayat pemakaian QC Image Inserter (password) |

---

## 🧩 Struktur File

```
app.py                          Landing page (launcher)
style.py                        CSS & komponen UI bersama
scoring.py                      Rumus skor & grading audit
audit_core.py                   Supabase + generator workbook audit
llm_core.py                     Multi-provider LLM untuk audit
structure.json                  130 item checklist audit
template.xlsx                   Template Excel audit

reim_llm_core.py                Multi-provider LLM (vision) reimburse
reim_extract_core.py            Prompt + aturan ekstraksi + dedup Flazz
reim_excel_core.py              Isi template Excel reimburse
reim_pdf_core.py                Gabung gambar → PDF (tanpa kompresi)
reim_gps_core.py                Baca GPS dari EXIF foto → nama jalan & kota
FORM_REIMBURSE_template.xlsx    Template Excel reimburse

pages/                          Halaman Streamlit (urutan sidebar)
presets/                        Preset template Excel QC Image Inserter
.streamlit/secrets.toml.example Contoh konfigurasi secrets
.github/workflows/              Keep-alive Supabase
```

---

## 🔌 Provider AI yang Didukung

Provider otomatis muncul di dropdown **hanya kalau API key-nya diisi**.
Semua provider OpenAI-compatible dan bisa dipakai untuk **Detail Audit LLM**,
**Reimburse Scanner**, maupun **Cek Model AI**.

| Provider | Prefix Secret | Mendukung Vision |
|----------|---------------|:----------------:|
| Google Gemini | `GEMINI_` | ✅ |
| DeepSeek | `DEEPSEEK_` | ✅ |
| Bandel Gateway | `BANDEL_` | ✅ |
| Kagiro | `KAGIRO_` | ✅ |
| 9router | `ROUTER9_` | ✅ (`cbai/deepseek-v4.1-flash`) |
| Cartridge | `CARTRIDGE_` | ✅ |
| Kenari | `KENARI_` | ✅ |
| GateAI | `GATEAI_` | ✅ |
| Juan | `JUAN_` | ✅ |
| SeekAI | `SEEKAI_` | ✅ |
| BYOK (Bring Your Own Key) | `BYOK_` | sesuai model |

> Catatan: model `cbai/*` (mis. `cbai/deepseek-v4.1-flash`) **hanya** tersedia
> di provider **9router**.

---

## 📄 Hasil Unduhan Reimburse

Nama file mengikuti **bulan & tahun data** (bukan tanggal hari ini):

- 📊 **Excel** → `Reimburse [Bulan] [Tahun].xlsx` — mis. `Reimburse Agustus 2026.xlsx`
- 🧾 **PDF** → `Invoice [Bulan] [Tahun].pdf` — mis. `Invoice Agustus 2026.pdf`

Alur unduhan dipisah jadi dua tahap: klik **Proses Excel** / **Proses PDF**
terlebih dahulu, lalu tombol **Download** muncul setelah proses selesai.

---

## 🚀 Setup Lokal

```bash
pip install -r requirements.txt
```

Buat file `.streamlit/secrets.toml` (salin dari `.streamlit/secrets.toml.example`)
lalu isi kredensial asli kamu. Variabel yang tersedia:

- `SUPABASE_URL`, `SUPABASE_KEY` — database draft audit & log.
- `ADMIN_PASSWORD`, `TRAFFIC_LOG_PASSWORD` — proteksi halaman password.
- `<PROVIDER>_API_KEY` (+ `<PROVIDER>_BASE_URL` bila perlu) — provider AI yang dipakai.
- `DEFAULT_NAME`, `DEFAULT_DEPARTMENT`, `DEFAULT_PURPOSE`, `DEFAULT_BANK_ACC` — data pemohon reimburse.

Jalankan:

```bash
streamlit run app.py
```

> ⚠️ **PENTING:** `.streamlit/secrets.toml` **TIDAK boleh** di-commit ke GitHub
> (sudah dikecualikan di `.gitignore`). Hanya file `.example` yang masuk repo.

---

## ☁️ Deploy ke Streamlit Community Cloud

1. Push folder ini ke GitHub (tanpa `secrets.toml`).
2. Buat app baru, pilih repo & `app.py` sebagai entrypoint.
3. Isi Secrets lewat **App → Settings → Secrets** (nilai sama seperti `secrets.toml` lokal).

Keep-alive Supabase memakai GitHub Actions (`.github/workflows/keep-alive.yml`);
set repo secret `SUPABASE_URL` dan `SUPABASE_KEY` agar ping berjalan.

---

<div align="center">

**Teazzi Audit & QC Toolkit** · dibuat untuk mempercepat proses QC retail.

</div>
