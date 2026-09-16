# Teazzi Audit & QC Toolkit (Gabungan)

Aplikasi Streamlit terpadu yang menggabungkan dua sistem:

1. **Audit & QC Toolkit** — checklist 130 item, skor berbobot, foto QC, log Supabase.
2. **Reimburse Scanner** — OCR struk jadi Excel reimburse + PDF bukti gabungan.

Kedua modul dibagi per halaman, tetapi kode core-nya tetap terpisah
(`*.py` untuk audit, `reim_*.py` untuk reimburse) sesuai kebutuhan.

---

## Halaman (urutan sidebar)

| # | Halaman | Fungsi |
|---|---------|--------|
| 1 | **Detail Audit LLM** | Mapping temuan bebas ke 130 checklist pakai Multi-LLM |
| 2 | **Detail Audit** | Input checklist manual + skor & grade otomatis |
| 3 | **QC Image Inserter** | Tempel foto QC massal ke template Excel |
| 4 | **Admin Hapus Data** | Edit/hapus draft audit (password) |
| 5 | **Audit Log** | Riwayat save/update/download audit |
| 6 | **Cek Model AI** | Tes provider, API key, dan model tersedia |
| 7 | **Traffic Log** | Riwayat pemakaian QC Image Inserter (password) |
| 8 | **Reimburse Scanner** | OCR struk → Excel + PDF |

---

## Struktur File

```
app.py                     Landing page (launcher)
style.py                   CSS & komponen UI bersama
scoring.py                 Rumus skor & grading audit
audit_core.py              Supabase + generator workbook audit
llm_core.py                Multi-provider LLM untuk audit
structure.json             130 item checklist audit
template.xlsx              Template Excel audit

reim_llm_core.py           Multi-provider LLM (vision) reimburse
reim_extract_core.py       Prompt + aturan ekstraksi + dedup Flazz
reim_excel_core.py         Isi template Excel reimburse
reim_pdf_core.py           Gabung gambar → PDF (tanpa kompresi)
reim_gps_core.py           Baca GPS dari EXIF foto
FORM_REIMBURSE_template.xlsx  Template Excel reimburse

pages/                     Halaman Streamlit (urutan sidebar)
presets/                   Preset template Excel QC Image Inserter
.streamlit/secrets.toml.example   Contoh konfigurasi secrets
.github/workflows/         Keep-alive Supabase
```

### Urutan halaman (sidebar)

| # | File | Halaman |
|---|---|---|
| 1 | `pages/1_Detail_Audit_LLM.py`   | Detail Audit dengan AI |
| 2 | `pages/2_Detail_Audit.py`       | Detail Audit Manual |
| 3 | `pages/3_QC_Image_Inserter.py`  | QC Image Inserter |
| 4 | `pages/4_Cek_Model_AI.py`       | Cek Model AI |
| 5 | `pages/5_Reimburse_Scanner.py`  | Reimburse Scanner (LLMREIM) |
| 6 | `pages/6_Admin_Hapus_Data.py`   | Admin Data |
| 7 | `pages/7_Audit_Log.py`          | Audit Log |
| 8 | `pages/8_Traffic_Log.py`        | Traffic Log |

---

## Setup

```bash
pip install -r requirements.txt
```

Buat file `.streamlit/secrets.toml` (salin dari `.streamlit/secrets.toml.example`)
lalu isi kredensial ASLI kamu:

- `SUPABASE_URL`, `SUPABASE_KEY` — untuk draft audit & log.
- `ADMIN_PASSWORD`, `TRAFFIC_LOG_PASSWORD` — proteksi halaman Admin & Traffic Log.
- `GEMINI_API_KEY` / `DEEPSEEK_API_KEY` / `BANDEL_API_KEY` / `KAGIRO_API_KEY` /
  `ROUTER9_API_KEY` — provider AI (isi yang dipakai saja).

Jalankan:

```bash
streamlit run app.py
```

> **PENTING:** `.streamlit/secrets.toml` TIDAK boleh di-commit ke GitHub
> (sudah dikecualikan di `.gitignore`). Hanya file `.example` yang masuk repo.

---

## Deploy ke Streamlit Community Cloud

1. Push folder ini ke GitHub (tanpa `secrets.toml`).
2. Buat app baru, pilih repo & `app.py` sebagai entrypoint.
3. Isi Secrets lewat menu **App → Settings → Secrets** (nilai sama seperti
   `secrets.toml` lokal).

Keep-alive Supabase memakai GitHub Actions (`.github/workflows/keep-alive.yml`);
set repo secret `SUPABASE_URL` dan `SUPABASE_KEY` agar ping berjalan.
