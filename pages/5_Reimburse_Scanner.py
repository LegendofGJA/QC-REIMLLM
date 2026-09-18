"""
Halaman Reimburse Scanner — Scan & Ekstraksi Reimburse Struk.

Modul core (prefixed `reim_` supaya tidak bentrok dengan core audit):
  - reim_llm_core.py    : koneksi provider + ping sungguhan + call vision (retry/timeout)
  - reim_extract_core.py: prompt + aturan ekstraksi + dedup Flazz + skip top up
  - reim_excel_core.py  : isi template Excel FORM_REIMBURSE
  - reim_pdf_core.py    : gabung gambar asli -> PDF tanpa kompresi
  - reim_gps_core.py    : baca lokasi GPS dari EXIF foto (dipertahankan)
"""

import os
from datetime import date

import streamlit as st

from style import inject_css, inject_footer
from reim_excel_core import TEMPLATE_PATH, fill_excel_template
from reim_extract_core import (
    EXTRACTION_PROMPT,
    FLAZZ_PROMPT,
    build_rows,
    dedupe_flazz_against_receipts,
    receipt_sort_key,
)
from reim_gps_core import gps_location_name, gps_short_address, read_gps
from reim_llm_core import PROVIDERS, fetch_all_models, fetch_vision_models, ping_model
from reim_llm_core import call_vision
from reim_pdf_core import merge_images_to_pdf

st.set_page_config(page_title="Reimburse Scanner", page_icon="🧾", layout="wide")
inject_css()

st.markdown(
    """
    <h2>🧾 Aplikasi Scan &amp; Ekstraksi Reimburse Struk</h2>
    <p>Upload foto struk (bensin, parkir, Teazzi) dan screenshot Flazz/e-money.
    Sistem mengekstrak data, mengurutkan kronologis, mengisi template Excel, dan
    menggabungkan bukti asli ke satu PDF tanpa kompresi.</p>
    """,
    unsafe_allow_html=True,
)

if not PROVIDERS:
    st.error(
        "Belum ada API key yang dikonfigurasi. Buat file `.streamlit/secrets.toml` "
        "(lihat `.streamlit/secrets.toml.example`) atau set environment variable "
        "KAGIRO_API_KEY / BANDEL_API_KEY / ROUTER9_API_KEY, lalu jalankan ulang aplikasi."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────
# Sidebar: data pemohon
# ─────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Data Pemohon")

    def _default(key: str, fallback: str = "") -> str:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass
        return os.environ.get(key, fallback)

    name = st.text_input("Name", value=_default("DEFAULT_NAME"))
    department = st.text_input("Department", value=_default("DEFAULT_DEPARTMENT"))
    purpose = st.text_input("Purpose", value=_default("DEFAULT_PURPOSE", "Reimburse"))
    bank_acc = st.text_input("Bank Acc.", value=_default("DEFAULT_BANK_ACC"))
    st.caption("Periode (kolom E6 & E7) diisi otomatis: awal & akhir bulan dari tanggal struk ter-upload.")


# ─────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────
DEFAULTS = {
    "extracted_items": [],
    "ordered_pdf_images": [],
    "failed_scans": [],
    "flazz_rows": [],
    "flazz_kept": [],
    "flazz_skipped": 0,
    "reim_excel_bytes": None,
    "reim_excel_err": None,
    "reim_excel_sig": None,
    "reim_excel_ready": False,
    "reim_pdf_bytes": None,
    "reim_pdf_err": None,
    "reim_pdf_sig": None,
    "reim_pdf_ready": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────
# Provider & model
# ─────────────────────────────────────────────────────────────────────────
st.subheader("Pemilihan Provider OCR")

provider_name = st.selectbox("Pilih Provider OCR", list(PROVIDERS.keys()))

# Mode daftar model:
#   - "Vision saja"  : hasil scan /models difilter buang model non-vision
#                       (embedding/tts/rerank/dsb) — default.
#   - "Semua model"  : seluruh model asli dari server, tanpa filter apa pun.
#                       Dipakai kalau model vision yang dicari tidak terdeteksi
#                       otomatis (mis. id tidak lazim).
mode_col, ref_col = st.columns([3, 1])
with mode_col:
    model_mode = st.radio(
        "Tampilkan model",
        ["Vision saja (rekomendasi OCR)", "Semua model dari server"],
        horizontal=True,
    )
with ref_col:
    refresh_clicked = st.button("🔄 Refresh daftar model", use_container_width=True)

_show_all = model_mode.startswith("Semua")
# Daftar model di-cache per provider per mode supaya rerun Streamlit (mis. ganti
# widget) tidak memanggil ulang endpoint /models berulang-ulang.
_models_cache_key = f"reim_models_{provider_name}_{'all' if _show_all else 'vision'}"
if refresh_clicked or _models_cache_key not in st.session_state:
    try:
        if _show_all:
            st.session_state[_models_cache_key] = fetch_all_models(provider_name)
        else:
            st.session_state[_models_cache_key] = fetch_vision_models(provider_name)
    except Exception as e:
        st.session_state[_models_cache_key] = []
        st.warning(f"Gagal mengambil daftar model: {e}")

available_models = st.session_state[_models_cache_key]

selected_model = st.selectbox(
    "Pilih Model Vision",
    available_models if available_models else ["Model tidak tersedia"],
)

if available_models:
    _shown = len(available_models)
    st.caption(
        f"✅ Terdeteksi **{_shown} model** dari server `{PROVIDERS[provider_name]['base_url']}`."
        + ("" if _show_all else " (disaring: model non-vision seperti embedding/tts dibuang)")
    )
else:
    st.warning(
        "Tidak ada model yang terdeteksi dari server ini. Cek API Key/Base URL, "
        "atau coba mode **Semua model dari server** lalu tekan **Refresh**."
    )

st.caption(
    "Daftar diambil langsung dari endpoint `/models` provider. Tidak ada ping otomatis — "
    "kalau ingin menguji model terpilih, pakai tombol Cek API Hidup di bawah."
)

# Info konsumsi token — bisa dibuka/tutup (nilai default tetutup agar tidak
# memakan ruang layar). Sumber: log pemakaian provider Kagiro per 1 gambar.
with st.expander("💡 Konsumsi token per gambar (hemat vs boros) — klik untuk buka"):
    st.caption(
        "Rata-rata token terpakai per 1 gambar, diurutkan dari paling hemat. "
        "Pilih model di atas berdasarkan tabel ini kalau ingin menekan biaya."
    )
    st.markdown(
        """
| Peringkat | Model | Rata-rata token / gambar | Catatan |
|:--:|---|--:|---|
| 🥇 1 | **Kimi k2.7 Code** | ~6.433 | Paling hemat (70.763 token / 11 gambar) |
| 🥈 2 | **DS Vision** | 7.938 | Paling hemat kedua |
| 🥉 3 | **Kimi k2.6** | 8.643 | Hemat |
| 4 | **Kimi k3** | 20.628 | Sedang |
| 5 | **Gemini 3.7f** | 21.383 | Sedang |
| 6 | **Gemini 3.6f** | 37.020 | Paling boros |
"""
    )
    st.caption(
        "Kesimpulan: **Kimi k2.7 Code** paling hemat untuk OCR, disusul **DS Vision**. "
        "Hindari model Gemini lama (3.6f) untuk banyak gambar."
    )

if provider_name and selected_model != "Model tidak tersedia":
    with st.expander("🩺 Cek API hidup (ping sungguhan ke model terpilih)"):
        st.caption(
            "Ping hanya dijalankan saat tombol ini ditekan — tidak otomatis, "
            "tidak memakan token kecuali kamu eksekusi."
        )
        if st.button("🔄 Test ping model sekarang"):
            with st.spinner(f"Mengirim pesan 'hi' ke {provider_name} / {selected_model}..."):
                ok, pesan, _ms = ping_model(provider_name, selected_model)
            if ok:
                st.success(pesan)
            else:
                st.error(pesan)


# ─────────────────────────────────────────────────────────────────────────
# Uploader
# ─────────────────────────────────────────────────────────────────────────
st.subheader("Unggah Bukti")

# Tombol reset supaya uploader dikosongkan penuh (ganti key -> widget dibuat ulang).
if "reim_uploader_key" not in st.session_state:
    st.session_state.reim_uploader_key = 0

if st.button("Hapus Semua Bukti (Reset)"):
    st.session_state.reim_uploader_key += 1
    st.rerun()

col_receipt, col_flazz = st.columns(2)

with col_receipt:
    uploaded_files = st.file_uploader(
        "Unggah foto struk (Bensin, Parkir, Teazzi) untuk satu bulan",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"receipt_uploader_{st.session_state.reim_uploader_key}",
    )
    # Indikator hijau begitu file dipilih — sama seperti QC Image Inserter.
    if uploaded_files:
        st.success(f"{len(uploaded_files)} struk terupload")
    else:
        st.caption("Belum ada struk yang dipilih")

with col_flazz:
    flazz_files = st.file_uploader(
        "Unggah screenshot Flazz / e-money (opsional)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"flazz_uploader_{st.session_state.reim_uploader_key}",
    )
    if flazz_files:
        st.success(f"{len(flazz_files)} screenshot Flazz terupload")
    else:
        st.caption("Belum ada screenshot Flazz yang dipilih")

_total_uploaded = len(uploaded_files or []) + len(flazz_files or [])
if _total_uploaded:
    st.success(f"Total {_total_uploaded} file terupload dan siap diproses")

st.info(
    """
**Aturan ekstraksi & format output:**
1. **Sorting kronologis:** hasil Excel diurutkan dari tanggal & jam transaksi paling awal ke akhir (bukan urutan upload).
2. **Bensin:** Pertalite → description cukup nama BBM. Pertamax/jenis lain → description berisi jenis BBM + jumlah liter, nominal tetap total akhir struk.
3. **Drink (Teazzi):** description berisi jenis minuman & nama outlet, nominal total akhir.
4. **Parkir:** description berisi nama tempat (atau `-` jika tidak ada), nominal total.
5. **Dedup Flazz:** baris "Parking" di screenshot Flazz yang tanggal & nominalnya sama persis dengan struk parkir fisik di-skip (tidak dobel). "Top Up" selalu di-skip.
6. **Periode E6/E7:** otomatis diisi awal & akhir bulan berdasarkan tanggal struk.
7. **PDF gabungan:** seluruh foto struk **dan** screenshot Flazz digabung ke satu PDF **tanpa kompresi/downsizing**.
    """
)


# ─────────────────────────────────────────────────────────────────────────
# Proses
# ─────────────────────────────────────────────────────────────────────────
if st.button("🚀 Mulai Proses OCR, Sorting, Generate Excel & PDF", type="primary"):
    if not uploaded_files and not flazz_files:
        st.warning("Silakan unggah minimal satu foto struk atau screenshot Flazz.")
    elif not available_models or selected_model == "Model tidak tersedia":
        st.error("Provider tidak aktif atau model tidak ditemukan. Gagal memproses.")
    else:
        extracted_items = []
        failures = []

        # PDF: setiap foto struk disimpan sebagai (urutan tanggal, bytes) supaya
        # halaman PDF bisa diurutkan kronologis. Foto yang gagal OCR masuk daftar
        # terpisah (tanpa tanggal) -> ditaruh di akhir PDF.
        receipt_pdf_pairs = []   # (sort_key, filename, img_bytes)
        failed_pdf_images = []   # (filename, img_bytes)

        total_files = len(uploaded_files or [])
        if total_files:
            ok_count = 0
            progress_bar = st.progress(0, text=f"0 dari {total_files} struk diproses...")
            with st.spinner("Memproses foto struk dengan AI Vision..."):
                for i, file in enumerate(uploaded_files):
                    img_bytes = file.getvalue()
                    try:
                        parsed = call_vision(provider_name, selected_model, img_bytes, EXTRACTION_PROMPT)
                        if isinstance(parsed, dict) and (parsed.get("type") or "").strip().lower() == "parkir":
                            loc = (parsed.get("location_name") or "").strip()
                            if not loc or loc == "-":
                                gps_name = gps_location_name(img_bytes)
                                if gps_name:
                                    parsed["location_name"] = gps_name
                        extracted_items.append(parsed)
                        sort_key = receipt_sort_key(parsed)
                        receipt_pdf_pairs.append((sort_key, file.name, img_bytes))
                        ok_count += 1
                    except Exception as e:
                        failures.append((file.name, str(e)))
                        failed_pdf_images.append((file.name, img_bytes))
                    done = i + 1
                    progress_bar.progress(
                        done / total_files,
                        text=f"{done} dari {total_files} struk diproses...",
                    )
            st.success(f"{total_files} struk terupload, {ok_count} berhasil di-OCR")

        # Screenshot Flazz — simpan per file agar dedup antar-screenshot akurat
        # (2 screenshot tumpang tindih menangkap riwayat yang sama).
        # Screenshot Flazz SELALU ditaruh di akhir PDF (bukan bukti struk fisik).
        flazz_items_by_file = []
        flazz_pdf_images = []
        if flazz_files:
            total_flazz = len(flazz_files)
            flazz_bar = st.progress(0, text=f"0 dari {total_flazz} screenshot Flazz diproses...")
            with st.spinner("Memproses screenshot Flazz/e-money..."):
                for i, file in enumerate(flazz_files):
                    img_bytes = file.getvalue()
                    flazz_pdf_images.append((file.name, img_bytes))
                    try:
                        parsed = call_vision(provider_name, selected_model, img_bytes, FLAZZ_PROMPT)
                        if isinstance(parsed, dict):
                            parsed = [parsed]
                        flazz_items_by_file.append(parsed if isinstance(parsed, list) else [])
                    except Exception as e:
                        failures.append((file.name, str(e)))
                        flazz_items_by_file.append([])
                    done = i + 1
                    flazz_bar.progress(
                        done / total_flazz,
                        text=f"{done} dari {total_flazz} screenshot Flazz diproses...",
                    )
            st.success(f"{total_flazz} screenshot Flazz terupload")

        if failures:
            st.warning(
                f"⚠️ {len(failures)} file gagal di-scan dan tetap dimasukkan ke akhir PDF "
                f"(baris Excel untuk file ini tidak ada):"
            )
            with st.expander(f"Lihat {len(failures)} file yang gagal di-scan"):
                for fname, err in failures:
                    st.write(f"- **{fname}**: {err}")

        # Dedup Flazz vs struk parkir + skip top up + dedup antar-screenshot
        receipt_df = build_rows(extracted_items)
        flazz_kept, flazz_skipped, matched = dedupe_flazz_against_receipts(
            flazz_items_by_file, receipt_df.to_dict("records")
        )

        # Baris Flazz parkir yang tetap -> jadi baris struk "parkir" (description '-')
        flazz_as_receipts = []
        for fr in flazz_kept:
            flazz_as_receipts.append(
                {
                    "date": fr["date"],
                    "time": fr.get("time"),
                    "type": "parkir",
                    "nominal": fr["nominal"],
                    "location_name": "-",
                    "description_override": "-",
                }
            )

        final_items = extracted_items + flazz_as_receipts

        # Urutan halaman PDF:
        #   1) struk fisik, kronologis sesuai tanggal & jam pada struk
        #   2) screenshot Flazz (selalu di akhir)
        #   3) foto yang gagal OCR (tanpa tanggal, paling akhir)
        receipt_pdf_pairs.sort(key=lambda p: p[0])
        ordered_images = [b for _, _, b in receipt_pdf_pairs]
        ordered_images += [b for _, b in flazz_pdf_images]
        ordered_images += [b for _, b in failed_pdf_images]

        st.session_state.extracted_items = final_items
        st.session_state.ordered_pdf_images = ordered_images
        st.session_state.failed_scans = [fname for fname, _ in failures]
        st.session_state.flazz_kept = flazz_kept
        st.session_state.flazz_skipped = flazz_skipped
        # Data baru -> hasil Excel/PDF lama tidak valid, wajib proses ulang.
        st.session_state.reim_excel_ready = False
        st.session_state.reim_excel_sig = None
        st.session_state.reim_excel_bytes = None
        st.session_state.reim_pdf_ready = False
        st.session_state.reim_pdf_sig = None
        st.session_state.reim_pdf_bytes = None

        msg = f"Ekstraksi selesai: {len(extracted_items)} struk fisik, {len(flazz_kept)} transaksi Flazz ditambahkan"
        if flazz_skipped:
            msg += f", {flazz_skipped} duplikat di-skip"
        st.success(msg + ".")


# ─────────────────────────────────────────────────────────────────────────
# Hasil & download
# ─────────────────────────────────────────────────────────────────────────
if st.session_state.extracted_items:
    df = build_rows(st.session_state.extracted_items)
    display_df = df[["date", "category", "description", "nominal"]].copy()
    display_df["date"] = display_df["date"].apply(lambda d: d.strftime("%d %b %Y") if d else "-")
    st.dataframe(display_df, width="stretch")
    st.markdown(f"**Total: Rp {df['nominal'].sum():,.0f}**".replace(",", "."))

    # GPS dari foto struk → tampilkan nama jalan & kota (bukan koordinat mentah)
    gps_list = []
    for f in uploaded_files or []:
        g = read_gps(f.getvalue())
        if not g:
            continue
        try:
            addr = gps_short_address(f.getvalue())
        except Exception:
            addr = ""
        gps_list.append((f.name, addr))
    if gps_list:
        with st.expander("📍 Lokasi GPS dari EXIF foto"):
            for fname, addr in gps_list:
                if addr:
                    st.write(f"- **{fname}**: {addr}")
                else:
                    st.write(f"- **{fname}**: _(nama jalan/kota tidak terbaca)_")

    # ── Proses Excel & PDF secara manual → baru muncul tombol download ───────
    # Tombol "Proses" menghasilkan file sekali; hasilnya disimpan di
    # session_state. Tombol "Download" baru muncul SETELAH proses selesai,
    # sehingga klik download tidak pernah "ketelan" dan byte-nya stabil
    # (tidak dibuat ulang di tengah rerun).
    _excel_sig = (
        len(df),
        f"{df['nominal'].sum():.2f}",
        str(df["date"].iloc[0]) if len(df) else "",
        str(df["date"].iloc[-1]) if len(df) else "",
        name,
        department,
        purpose,
        bank_acc,
    )
    _pdf_sig = (len(st.session_state.get("ordered_pdf_images") or []),)

    st.divider()
    st.markdown("#### Proses & unduh hasil")
    st.caption(
        "Klik **Proses Excel** / **Proses PDF** dulu. Kalau proses selesai, "
        "tombol **Download** akan muncul."
    )

    _month_tag = date.today().strftime("%Y%m")
    pcol1, pcol2 = st.columns(2)

    # ── Excel ────────────────────────────────────────────────────────────────
    with pcol1:
        if st.button(
            "📊 Proses Excel",
            key="reim_proc_excel",
            use_container_width=True,
            type="primary",
        ):
            with st.spinner("Membuat file Excel…"):
                try:
                    st.session_state.reim_excel_bytes = fill_excel_template(
                        df,
                        TEMPLATE_PATH,
                        {
                            "name": name,
                            "department": department,
                            "purpose": purpose,
                            "bank_acc": bank_acc,
                        },
                    )
                    st.session_state.reim_excel_err = None
                    st.session_state.reim_excel_sig = _excel_sig
                    st.session_state.reim_excel_ready = True
                except Exception as e:  # pragma: no cover - tergantung template
                    st.session_state.reim_excel_bytes = None
                    st.session_state.reim_excel_err = str(e)
                    st.session_state.reim_excel_ready = False

        _excel_stale = st.session_state.get("reim_excel_sig") != _excel_sig
        if _excel_stale:
            st.session_state.reim_excel_ready = False

        if st.session_state.get("reim_excel_err"):
            st.error(f"Gagal membuat Excel: {st.session_state.reim_excel_err}")
        elif st.session_state.get("reim_excel_ready") and not _excel_stale:
            st.success("Excel siap.")
            st.download_button(
                "📥 Download Excel Reimburse",
                data=st.session_state.reim_excel_bytes,
                file_name=f"FORM_REIMBURSE_{_month_tag}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="reim_dl_excel",
                on_click="ignore",
                use_container_width=True,
            )
        else:
            st.caption("Belum diproses.")

    # ── PDF ──────────────────────────────────────────────────────────────────
    with pcol2:
        _ordered_images = st.session_state.get("ordered_pdf_images") or []
        _has_images = bool(_ordered_images)

        if st.button(
            "🧾 Proses PDF",
            key="reim_proc_pdf",
            use_container_width=True,
            type="primary",
            disabled=not _has_images,
            help=None if _has_images else "Tidak ada gambar bukti untuk PDF.",
        ):
            with st.spinner("Menggabungkan PDF (tanpa kompresi)…"):
                try:
                    st.session_state.reim_pdf_bytes = merge_images_to_pdf(
                        _ordered_images
                    )
                    st.session_state.reim_pdf_err = None
                    st.session_state.reim_pdf_sig = _pdf_sig
                    st.session_state.reim_pdf_ready = True
                except Exception as e:  # pragma: no cover
                    st.session_state.reim_pdf_bytes = None
                    st.session_state.reim_pdf_err = str(e)
                    st.session_state.reim_pdf_ready = False

        _pdf_stale = st.session_state.get("reim_pdf_sig") != _pdf_sig
        if _pdf_stale:
            st.session_state.reim_pdf_ready = False

        if st.session_state.get("reim_pdf_err"):
            st.error(f"Gagal membuat PDF: {st.session_state.reim_pdf_err}")
            st.caption("Excel tetap bisa diproses & diunduh di kiri.")
        elif st.session_state.get("reim_pdf_ready") and not _pdf_stale:
            st.success("PDF siap.")
            st.download_button(
                "📥 Download PDF Bukti Gabungan (tanpa kompresi)",
                data=st.session_state.reim_pdf_bytes,
                file_name=f"Bukti_Gabungan_{_month_tag}.pdf",
                mime="application/pdf",
                key="reim_dl_pdf",
                on_click="ignore",
                use_container_width=True,
                help="Urutan halaman: struk kronologis → screenshot Flazz → foto gagal scan.",
            )
        elif not _has_images:
            st.caption("Tidak ada gambar bukti untuk PDF.")
        else:
            st.caption("Belum diproses.")

    failed_scans = st.session_state.get("failed_scans") or []
    if failed_scans:
        st.warning(
            f"⚠️ {len(failed_scans)} foto gagal di-scan (tidak ada baris Excel-nya). "
            f"Foto ini tetap ditaruh di **akhir PDF**: " + ", ".join(failed_scans)
        )

inject_footer()
