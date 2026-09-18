"""
excel_core.py — Isi data ke template Excel FORM_REIMBURSE.

Menangani:
  - header info (Name/Department/Purpose/Bank Acc),
  - periode E6/E7 (timestamp struk pertama & terakhir),
  - penulisan baris data mulai DATA_START_ROW,
  - perluasan baris otomatis bila data > baris tersedia,
  - total otomatis (formula SUM).
"""

import io
import re
import zipfile
from datetime import date

import openpyxl

TEMPLATE_PATH = "FORM_REIMBURSE_template.xlsx"
DATA_START_ROW = 12
DATA_END_ROW_DEFAULT = 61
TOTAL_ROW_DEFAULT = 62
SHEET_NAME = "FORM"

# Sheet index (1-based, urutan di workbook.xml) yang punya gambar header.
# template FORM_REIMBURSE menaruh logo perusahaan di sheet pertama.
_SHEET_XML = "xl/worksheets/sheet1.xml"
_SHEET_RELS = "xl/worksheets/_rels/sheet1.xml.rels"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_DRAWING_NS = ("http://schemas.openxmlformats.org/officeDocument/2006/"
               "relationships/drawing")


def _guess_sheet(ws):
    return ws


def _reinsert_media(out_bytes: bytes, src_path: str) -> bytes:
    """
    openpyxl membuang gambar yang ada di dalam *grouped shape* (grpSp) saat
    load+save -- logo header FORM_REIMBURSE hilang. Fungsi ini menyalin
    kembali part drawing + media + rels dari template ASLI ke hasil openpyxl,
    lalu menambal referensi <drawing> di sheet + [Content_Types].xml.

    Dipakai supaya logo & alamat perusahaan tetap muncul di file hasil unduh.
    """
    try:
        src = zipfile.ZipFile(src_path)
    except Exception:
        return out_bytes

    src_names = set(src.namelist())
    drawing_parts = [n for n in src_names if n.startswith("xl/drawings/")
                     and n.endswith(".xml")]
    media_parts = [n for n in src_names if n.startswith("xl/media/")]
    if not drawing_parts and not media_parts:
        return out_bytes  # template memang tanpa gambar

    out = zipfile.ZipFile(io.BytesIO(out_bytes))
    out_names = set(out.namelist())

    # Kalau openpyxl sudah membawa drawing (template non-grouped, mis. audit),
    # tidak perlu intervensi.
    if any(n.startswith("xl/drawings/") for n in out_names):
        return out_bytes

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in out.infolist():
            data = out.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = _patch_content_types(data, media_parts, drawing_parts)
            elif item.filename == _SHEET_XML:
                data = _patch_sheet_drawing(data)
            dst.writestr(item, data)

        # Salin drawing + media + rels apa adanya dari template asli.
        for n in drawing_parts + media_parts:
            dst.writestr(n, src.read(n))

        # Rels sheet -> drawing (dan drawing -> media ikut tersalin di atas).
        sheet_rels_name = _SHEET_RELS
        if sheet_rels_name in src_names:
            dst.writestr(sheet_rels_name, src.read(sheet_rels_name))
        else:
            dst.writestr(sheet_rels_name, _make_sheet_rels(len(drawing_parts)))

    buf.seek(0)
    return buf.getvalue()


def _patch_sheet_drawing(sheet_xml: bytes) -> bytes:
    text = sheet_xml.decode("utf-8")

    # Pastikan namespace "r:" terdeklarasi di <worksheet ...> supaya
    # atribut r:id pada <drawing> tidak jadi "unbound prefix".
    if "xmlns:r=" not in text:
        text = re.sub(
            r"<worksheet\b",
            '<worksheet xmlns:r="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships"',
            text,
            count=1,
        )

    if "<drawing" in text:
        return text.encode("utf-8")

    tag = '<drawing r:id="rId1"/>'
    if "</worksheet>" in text:
        text = text.replace("</worksheet>", tag + "</worksheet>", 1)
    else:
        text = text + tag
    return text.encode("utf-8")


def _patch_content_types(ct_xml: bytes, media_parts, drawing_parts) -> bytes:
    text = ct_xml.decode("utf-8")
    additions = []
    if ".png" in " ".join(media_parts) and 'Extension="png"' not in text:
        additions.append('<Default Extension="png" '
                         'ContentType="image/png"/>')
    for n in drawing_parts:
        override = ('<Override PartName="/%s" ContentType="application/'
                    'vnd.openxmlformats-officedocument.drawing+xml"/>' % n)
        if ('PartName="/%s"' % n) not in text:
            additions.append(override)
    if additions:
        text = text.replace("</Types>", "".join(additions) + "</Types>", 1)
    return text.encode("utf-8")


def _make_sheet_rels(n_drawings: int) -> bytes:
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="%s">' % _REL_NS]
    for i in range(n_drawings):
        rels.append('<Relationship Id="rId%d" Type="%s" '
                    'Target="../drawings/drawing%d.xml"/>'
                    % (i + 1, _DRAWING_NS, i + 1))
    rels.append("</Relationships>")
    return "".join(rels).encode("utf-8")


def _is_na(v):
    try:
        import pandas as pd

        return bool(pd.isna(v))
    except Exception:
        return False


def fill_excel_template(df, template_path: str, header_info: dict) -> bytes:
    wb = openpyxl.load_workbook(template_path)
    ws = wb[SHEET_NAME]

    if header_info.get("name"):
        ws["C6"] = header_info["name"]
    if header_info.get("department"):
        ws["C7"] = header_info["department"]
    if header_info.get("purpose"):
        ws["C8"] = header_info["purpose"]
    if header_info.get("bank_acc"):
        ws["C9"] = header_info["bank_acc"]

    # Periode E6 = timestamp struk/transaksi pertama, E7 = terakhir
    # (baris sudah terurut kronologis; jam hanya penentu urutan, sel menampilkan tanggal).
    if not df.empty:
        valid_dates = [d for d in df["date"] if d and not _is_na(d)]
        if valid_dates:
            period_start = valid_dates[0]
            period_end = valid_dates[-1]
        else:
            period_start = period_end = date.today()
    else:
        period_start = period_end = date.today()
    for cell, val in (("E6", period_start), ("E7", period_end)):
        ws[cell].number_format = "d mmm yyyy"
        ws[cell] = val

    n = len(df)
    available_rows = DATA_END_ROW_DEFAULT - DATA_START_ROW + 1

    if n > available_rows:
        extra = n - available_rows
        ws.insert_rows(DATA_END_ROW_DEFAULT + 1, amount=extra)
        for i in range(extra):
            src_row = DATA_END_ROW_DEFAULT
            dst_row = DATA_END_ROW_DEFAULT + 1 + i
            for col in range(2, 6):
                src_cell = ws.cell(row=src_row, column=col)
                dst_cell = ws.cell(row=dst_row, column=col)
                dst_cell.number_format = src_cell.number_format
                dst_cell.font = src_cell.font.copy()
                dst_cell.border = src_cell.border.copy()
                dst_cell.fill = src_cell.fill.copy()
                dst_cell.alignment = src_cell.alignment.copy()
        total_row = TOTAL_ROW_DEFAULT + extra
        data_end_row = DATA_END_ROW_DEFAULT + extra
    else:
        total_row = TOTAL_ROW_DEFAULT
        data_end_row = DATA_END_ROW_DEFAULT

    for i, row in df.iterrows():
        r = DATA_START_ROW + i
        d = row["date"]
        ws.cell(row=r, column=2, value=d)
        if d:
            ws.cell(row=r, column=2).number_format = "d mmm yyyy"
        ws.cell(row=r, column=3, value=row["category"])
        ws.cell(row=r, column=4, value=row["description"])
        ws.cell(row=r, column=5, value=row["nominal"])
        ws.cell(row=r, column=5).number_format = "#,##0"

    ws.cell(row=total_row, column=5, value=f"=SUM(E{DATA_START_ROW}:E{data_end_row})")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    out = buf.getvalue()

    # openpyxl membuang gambar grouped-shape (logo header) saat save.
    # Kembalikan dari template asli supaya logo & alamat tetap tampil.
    out = _reinsert_media(out, template_path)

    return out
