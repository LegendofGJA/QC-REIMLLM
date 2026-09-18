"""
extract_core.py — Aturan ekstraksi data struk & Flazz (bebas dari UI).

Berisi prompt + logika murni (testable tanpa Streamlit):
  - klasifikasi kategori (bensin / drink / parkir),
  - penyusunan description per kategori,
  - ekstraksi screenshot Flazz (JSON array),
  - dedup Flazz vs struk parkir berdasar (tanggal, nominal),
  - skip "Top Up".
"""

import re

from dateutil import parser as dateparser

# ─────────────────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """Kamu adalah sistem OCR untuk struk belanja Indonesia.
Analisis gambar struk ini dan kembalikan HANYA JSON murni (tanpa markdown, tanpa teks tambahan) dengan struktur persis berikut:

{
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "type": "bensin" | "parkir" | "drink",
  "nominal": <angka total akhir struk, tanpa titik/koma/Rp>,
  "fuel_type": "<nama jenis BBM apa adanya di struk, contoh: Pertalite / Pertamax / Pertamax Turbo, atau null jika bukan bensin>",
  "liters": <jumlah liter sebagai angka, atau null jika tidak ada / bukan bensin>,
  "drink_name": "<jenis/menu minuman yang dibeli, atau null jika bukan drink>",
  "outlet_name": "<nama toko/outlet, contoh Teazzi, atau null jika bukan drink>",
  "location_name": "<nama tempat/lokasi parkir, atau null jika bukan parkir. Jika parkir tapi nama tempat tidak tertera, isi dengan '-'>"
}

Aturan klasifikasi "type":
- Struk pom bensin / SPBU -> "bensin"
- Struk parkir -> "parkir"
- Struk Teazzi atau minuman lain -> "drink"

Ambil "nominal" sebagai TOTAL AKHIR yang benar-benar dibayar pada struk.
Tanggal WAJIB diambil dari tanggal transaksi yang tertera di struk, bukan diasumsikan.
"time" WAJIB diisi jam transaksi (format 24 jam "HH:MM") jika struk mencantumkan jam.
Jika struk TIDAK mencantumkan jam sama sekali, isi "time" dengan null. Jangan mengarang jam.
Kembalikan JSON murni saja, tidak ada teks lain sebelum atau sesudahnya."""

FLAZZ_PROMPT = """Kamu adalah sistem OCR untuk screenshot riwayat transaksi e-money (Flazz/BCA).
Gambar ini berisi DAFTAR transaksi (mungkin banyak baris). Ekstrak SEMUA baris transaksi.

Kembalikan HANYA JSON array murni (tanpa markdown), setiap elemen:

{
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "label": "<teks baris transaksi apa adanya, misal: Parking, Top Up, Merchant name>",
  "nominal": <angka nominal transaksi, tanpa titik/koma/Rp>,
  "is_topup": true|false
}

Aturan:
- "is_topup" true hanya jika baris itu top up / isi saldo / topup; sisanya false.
- Baris "Parking" biasanya adalah pembayaran parkir.
- Ambil tanggal sesuai baris transaksi (format mungkin "06 Jul 2026").
- "time" diisi jam transaksi ("HH:MM", 24 jam) jika screenshot mencantumkan jam.
  Jika tidak ada jam pada baris tsb, isi null. Jangan mengarang jam.
- Urutkan elemen array sesuai urutan tampil di screenshot.
- Kembalikan JSON array murni saja, tidak ada teks lain sebelum/sesudahnya."""


# ─────────────────────────────────────────────────────────────────────────
# Description per kategori (logika dipastikan di Python, bukan di model)
# ─────────────────────────────────────────────────────────────────────────


def build_description(item: dict) -> str:
    itype = (item.get("type") or "").strip().lower()

    if itype == "bensin":
        fuel = (item.get("fuel_type") or "").strip()
        liters = item.get("liters")
        if not fuel:
            return "-"
        if "pertalite" in fuel.lower():
            return fuel
        if liters:
            try:
                liters_fmt = f"{float(liters):g}"
            except (TypeError, ValueError):
                liters_fmt = str(liters)
            return f"{fuel} {liters_fmt} Liter"
        return fuel

    if itype == "drink":
        drink = (item.get("drink_name") or "").strip()
        outlet = (item.get("outlet_name") or "").strip()
        parts = [p for p in [drink, outlet] if p]
        return " - ".join(parts) if parts else "-"

    if itype == "parkir":
        loc = (item.get("location_name") or "").strip()
        return loc if loc else "-"

    return "-"


# ─────────────────────────────────────────────────────────────────────────
# Parsing
# ─────────────────────────────────────────────────────────────────────────


def parse_date_safe(raw):
    """Parse tanggal struk Indonesia -> datetime.date, atau None.

    ATURAN PENTING (penyebab bug "tanggal berantakan"):

    Parser lama memakai `dayfirst=False, yearfirst=True`. Dua masalah:

      1. `yearfirst=True` membuat tahun 2 digit dibaca sebagai AWAL string,
         sehingga "2 Mar 26" -> 2002-03-26 dan "12/03/26" -> 2012-03-26.
         Baris-baris ini lalu terlempar ke tahun 2002/2012 saat disort,
         jadi urutan tanggal di Excel tampak kacau.
      2. `dayfirst=False` menukar hari/bulan pada format numerik seperti
         "12/03/2026" -> 2026-12-03 (12 Maret dibaca 3 Desember).

    Solusi: parser berlapis, paling spesifik dulu.
      - ISO `YYYY-MM-DD` (paling tidak ambigu) -> format eksplisit.
      - `DD/MM/YYYY` dan `DD-MM-YYYY` (4 digit tahun) -> format eksplisit.
      - Teks Indonesia ("2 Mar 2026", "02 Maret 26") -> dateutil dayfirst.
      - Fallback terakhir: dateutil dayfirst + normalisasi tahun 2 digit.
    Semua hasil selalu di-normalisasi supaya tahun 2 digit masuk abad 2000.
    """
    if not raw:
        return None
    if isinstance(raw, (int, float)):
        return None
    text = str(raw).strip()
    if not text:
        return None

    # Normalisasi ringan: buang spasi ganda & ganti nama bulan Indonesia.
    text = " ".join(text.split())
    text = _id_month_to_num(text)

    # 1) ISO / paling tidak ambigu: YYYY-MM-DD atau YYYY/MM/DD.
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        dt = _safe_date(y, mo, d)
        if dt:
            return dt
    # 1b) YYYYMMDD (8 digit rapat, format struk digital).
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", text)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        dt = _safe_date(y, mo, d)
        if dt:
            return dt

    # 2) Numerik dengan tahun 4 digit -> eksplisit DD/MM/YYYY (gaya Indonesia).
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", text)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        dt = _safe_date(y, mo, d)
        if dt:
            return dt

    # 3) Numerik dengan tahun 2 digit -> DD/MM/YY (gaya Indonesia),
    #    tahun 2 digit dipetakan ke 2000-an.
    m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})$", text)
    if m:
        d, mo, y2 = (int(x) for x in m.groups())
        dt = _safe_date(2000 + y2, mo, d)
        if dt:
            return dt

    # 4) Teks bebas ("2 Mar 2026", "02 Maret 26", "Mar 2, 2026").
    for kwargs in (
        {"dayfirst": True, "yearfirst": False},
        {"dayfirst": True},
    ):
        try:
            parsed = dateparser.parse(text, **kwargs)
        except Exception:
            parsed = None
        if parsed:
            # yearfirst bug tidak terpakai di sini, tapi jaga-jaga: tahun 2 digit
            # hasil dateutil kadang salah -> koreksi bila < 100 tahun terakhir.
            y = parsed.year
            if y < 100:
                y += 2000
            elif y < 1000:
                pass
            if 1900 <= y <= 2100:
                try:
                    return parsed.replace(year=y).date()
                except ValueError:
                    return parsed.date()
    return None


_ID_MONTHS = {
    "jan": 1, "januari": 1,
    "feb": 2, "februari": 2, "peb": 2, "pebruari": 2,
    "mar": 3, "maret": 3,
    "apr": 4, "april": 4,
    "mei": 5, "may": 5,
    "jun": 6, "juni": 6,
    "jul": 7, "juli": 7,
    "agu": 8, "ags": 8, "agustus": 8, "aug": 8,
    "sep": 9, "sept": 9, "september": 9,
    "okt": 10, "oktober": 10, "oct": 10,
    "nov": 11, "november": 11,
    "des": 12, "desember": 12, "dec": 12,
}


def _id_month_to_num(text: str) -> str:
    """Ganti nama bulan Indonesia -> angka supaya dateutil konsisten.

    Contoh: "2 Maret 2026" -> "2 3 2026", "02 Peb 26" -> "02 2 26"."""
    def repl(match):
        token = match.group(1).lower()
        return str(_ID_MONTHS[token]) if token in _ID_MONTHS else match.group(1)

    return re.sub(
        r"\b([A-Za-z]+)\b", repl, text
    )


def _safe_date(year: int, month: int, day: int):
    """Buat datetime.date dengan aman (hindari ValueError)."""
    from datetime import date as _date

    try:
        return _date(year, month, day)
    except ValueError:
        return None


def parse_time_safe(raw):
    """Parse kolom 'time' (HH:MM atau HH:MM:SS) -> datetime.timedelta sejak tengah
    malam, atau None bila kosong/tidak valid."""
    from datetime import time as _time, timedelta

    if not raw:
        return None
    if isinstance(raw, (int, float)):
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        t = dateparser.parse(text)
        if t is None:
            return None
        return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    except Exception:
        return None


def parse_nominal(value):
    """Nominal -> float. Abaikan titik/koma/Rp, pertahankan tanda minus."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.\-]", "", str(value))
    if cleaned in ("", "-", ".", "-."):
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _to_date(d):
    return d if d else __import__("datetime").date.max


def _sort_datetime(item):
    """Kunci sort gabungan: (date_obj atau date.max, time dalam detik atau -1).
    -1 dipakai untuk baris tanpa jam agar baris berjam muncul duluan di hari
    yang sama (urutan waktu memang tidak lengkap untuk baris tanpa jam)."""
    d = item.get("date")
    if not d or _is_na(d):
        d = __import__("datetime").date.max
    t = item.get("time")
    if t is None or _is_na(t):
        secs = -1
    else:
        secs = int(getattr(t, "total_seconds", lambda: 0)())
    return (d, secs)


def _is_na(v):
    try:
        import pandas as pd

        return bool(pd.isna(v))
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────
# Struk fisik -> rows
# ─────────────────────────────────────────────────────────────────────────


def receipt_sort_key(parsed: dict):
    """Kunci urutan PDF untuk satu struk fisik, dari tanggal & jam hasil OCR.

    Memakai parser yang sama dengan build_rows supaya urutan halaman PDF selalu
    konsisten dengan urutan baris Excel. Struk tanpa tanggal valid diletakkan
    paling belakang (date.max)."""
    if not isinstance(parsed, dict):
        return _sort_datetime({})
    item = {
        "date": parse_date_safe(parsed.get("date")),
        "time": parse_time_safe(parsed.get("time")),
    }
    return _sort_datetime(item)


def build_rows(extracted_items: list) -> list:
    """Ubah daftar hasil struk menjadi list dict (date, category, description,
    nominal) dan urutkan kronologis berdasarkan tanggal + jam (timestamp).
    Baris tanpa tanggal diletakkan di akhir."""
    import pandas as pd

    rows = []
    for item in extracted_items:
        rows.append(
            {
                "date": parse_date_safe(item.get("date")),
                "time": parse_time_safe(item.get("time")),
                "category": (item.get("type") or "-").strip().lower(),
                "description": build_description(item),
                "nominal": parse_nominal(item.get("nominal")),
                "location_name": (item.get("location_name") or "").strip(),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["_sort_key"] = df.apply(_sort_datetime, axis=1)
    df = df.sort_values("_sort_key", kind="stable").drop(columns=["_sort_key"])
    df = df.reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────
# Flazz: normalisasi + dedup + skip topup
# ─────────────────────────────────────────────────────────────────────────


def _is_topup(row: dict) -> bool:
    if row.get("is_topup") is True:
        return True
    label = (row.get("label") or "").strip().lower()
    return "top up" in label or "topup" in label or "top-up" in label or "isi saldo" in label


def normalise_flazz_rows(flazz_items: list) -> list:
    """Buang baris Top Up, lalu kembalikan baris parkir (label mengandung
    'park') sebagai list dict {date, nominal, label, is_parking}.

    flazz_items bisa berupa list flat (dict), ataupun list[list[dict]]
    (per-screenshot). Untuk flat, diperlakukan sebagai satu screenshot."""
    if flazz_items and isinstance(flazz_items[0], list):
        per_file = flazz_items
    else:
        per_file = [flazz_items]

    result = []
    for items in per_file:
        for it in items:
            if _is_topup(it):
                continue
            label = (it.get("label") or "").strip()
            is_parking = "park" in label.lower()
            result.append(
                {
                    "date": parse_date_safe(it.get("date")),
                    "time": parse_time_safe(it.get("time")),
                    "nominal": parse_nominal(it.get("nominal")),
                    "label": label,
                    "is_parking": is_parking,
                }
            )
    return result


def dedupe_flazz_against_receipts(flazz_rows: list, receipt_rows: list) -> tuple:
    """Cocokkan baris Flazz 'parkir' ke struk parkir fisik berdasar
    (tanggal, nominal). Baris yang match persis di-SKIP (sudah terwakili struk).

    flazz_rows dapat berupa:
      - list flat dict (hasil normalise_flazz_rows), atau
      - list[list[dict]] (per screenshot).

    Dedup antar-screenshot: bila N screenshot tumpang tindih menangkap riwayat
    yang sama, satu transaksi (date, nominal) legal muncul hingga N kali — tapi
    sebenarnya transaksi yang sama. Jadi jumlah maksimum kejadian suatu key
    dalam SATU screenshot dipakai sebagai "jumlah asli"; selebihnya di-skip.

    receipt_rows: list dict hasil build_rows (memiliki date, category, nominal).

    Return (kept: list[flazz_rows], skipped: int, matched_pairs: list[tuple]).
    """
    if flazz_rows and isinstance(flazz_rows[0], list):
        per_file = flazz_rows
    else:
        per_file = [flazz_rows]

    # Normalisasi internal: buang Top Up + tandai is_parking per baris.
    per_file = [normalise_flazz_rows(items) for items in per_file]

    # Flatten + lampirkan index file asal untuk hitung count per-file.
    receipts = [
        r
        for r in receipt_rows
        if (r.get("category") or "") == "parkir" and r.get("date") and r.get("nominal")
    ]
    receipt_pairs = {
        (r["date"], round(float(r["nominal"]), 2)) for r in receipts
    }

    def _key(fr):
        return (fr["date"], round(float(fr["nominal"]), 2))

    # Hitung berapa kali tiap key muncul di dalam SATU screenshot (maksimum).
    key_max_in_single = {}
    for items in per_file:
        src_counts = {}
        for it in items:
            if not it.get("is_parking") or not it.get("date"):
                continue
            k = _key(it)
            src_counts[k] = src_counts.get(k, 0) + 1
        for k, c in src_counts.items():
            if c > key_max_in_single.get(k, 0):
                key_max_in_single[k] = c

    # Flatten dengan urutan stabil (file per file).
    flattened = []
    for items in per_file:
        for it in items:
            flattened.append(it)

    kept = []
    skipped = 0
    matched = []
    seen = {}
    for fr in flattened:
        if not fr["is_parking"]:
            kept.append(fr)
            continue
        key = _key(fr)

        # 1) Sudah terwakili struk parkir fisik -> skip.
        if fr["date"] and key in receipt_pairs:
            skipped += 1
            matched.append((fr["date"], fr["nominal"]))
            continue

        if not fr["date"]:
            kept.append(fr)
            continue

        # 2) Dedup antar-screenshot: izinkan sampai jumlah max dalam 1 screenshot.
        allow = key_max_in_single.get(key, 1)
        already = seen.get(key, 0)
        if already >= allow:
            skipped += 1
            matched.append((fr["date"], fr["nominal"]))
            continue
        seen[key] = already + 1
        kept.append(fr)
    return kept, skipped, matched
