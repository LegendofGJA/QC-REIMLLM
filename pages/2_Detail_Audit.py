import pandas as pd
import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer
from scoring import compute_all
from audit_core import (
    load_structure,
    get_supabase_client,
    list_saved_drafts,
    fetch_draft,
    save_draft,
    update_draft_by_id,
    build_filled_workbook,
    workbook_to_bytes,
    log_audit_traffic,
)

st.set_page_config(page_title="DETAIL AUDIT", page_icon="📋", layout="wide")
inject_css()
inject_sidebar_brand()

# Panel tombol kecil melayang di kiri bawah
st.markdown(
    """
    <style>
    .cat-banner {
        background: linear-gradient(135deg, var(--accent), #c0242a);
        color: #fff;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 7px 14px;
        border-radius: 8px;
        margin: 16px 0 6px 0;
        letter-spacing: .03em;
    }
    .subcat-label {
        font-weight: 700;
        text-decoration: underline;
        margin: 8px 0 4px 4px;
        color: var(--accent);
    }
    div.st-key-floating_actions {
        position: fixed;
        left: 14px;
        bottom: 14px;
        z-index: 9999;
        background: var(--surface);
        padding: 6px;
        border-radius: 999px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.35);
        border: 1px solid var(--border);
        width: auto;
        display: inline-block;
    }
    div.st-key-floating_actions [data-testid="stHorizontalBlock"] {
        gap: 6px !important;
    }
    div.st-key-floating_actions button,
    div.st-key-floating_actions a {
        font-size: 1.1rem !important;
        padding: 0.45rem !important;
        width: 42px !important;
        height: 42px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
    }
    /* ── Tombol gulir cepat (scroll to top / bottom) ── */
    .scroll-nav-btn {
        position: fixed;
        right: 18px;
        z-index: 9998;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: var(--surface);
        color: var(--accent);
        border: 1px solid var(--border);
        box-shadow: 0 3px 14px rgba(0,0,0,0.28);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
        line-height: 1;
        text-decoration: none !important;
        transition: transform .12s ease, background .12s ease;
    }
    .scroll-nav-btn:hover {
        background: var(--accent);
        color: #fff;
        transform: translateY(-1px);
    }
    .scroll-nav-btn:focus-visible {
        outline: 2px solid var(--accent);
        outline-offset: 2px;
    }
    .scroll-top-btn { top: 14px; }
    .scroll-bottom-btn { bottom: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Penanda jangkar untuk tombol gulir ke atas/bawah
st.markdown(
    "<span id='page-top'></span>"
    "<a class='scroll-nav-btn scroll-top-btn' href='#page-top' "
    "title='Ke atas' aria-label='Gulir ke atas'>&#9650;</a>"
    "<a class='scroll-nav-btn scroll-bottom-btn' href='#page-bottom' "
    "title='Ke bawah' aria-label='Gulir ke bawah'>&#9660;</a>",
    unsafe_allow_html=True,
)

structure = load_structure()
supabase = get_supabase_client()

defaults = {
    "store_name": "", "date1": "", "date2": "",
    "auditor": "", "pic_on_duty": "", "remarks": {},
    "loaded_key": None, "loaded_id": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _safe_remark(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return ""
    return str(v)


def _sync_remark_widgets(remarks: dict):
    """Timpa LANGSUNG nilai di setiap widget key remark sesuai data
    yang baru dimuat."""
    for cat in structure:
        if cat.get("name") == "ETC":
            continue
        if "subcategories" in cat:
            for sub in cat["subcategories"]:
                prefix = f"editor_{sub['row']}"
                for it in sub["items"]:
                    num = str(it["number"])
                    wk = f"{prefix}_remark_{num}"
                    st.session_state[wk] = _safe_remark(remarks.get(num, ""))
        else:
            prefix = f"editor_{cat['row']}"
            for it in cat.get("items", []):
                num = str(it["number"])
                wk = f"{prefix}_remark_{num}"
                st.session_state[wk] = _safe_remark(remarks.get(num, ""))


def reset_form():
    _sync_remark_widgets({})
    for k, v in defaults.items():
        st.session_state[k] = v if not isinstance(v, dict) else {}
    st.query_params.clear()


def load_into_state(row: dict):
    st.session_state["store_name"] = row.get("store_name", "") or ""
    st.session_state["date1"] = row.get("audit_date", "") or ""
    st.session_state["date2"] = row.get("date2", "") or ""
    st.session_state["auditor"] = row.get("auditor", "") or ""
    st.session_state["pic_on_duty"] = row.get("pic_on_duty", "") or ""
    new_remarks = row.get("remarks", {}) or {}
    st.session_state["remarks"] = new_remarks
    st.session_state["loaded_key"] = (row.get("store_name"), row.get("audit_date"))
    st.session_state["loaded_id"] = row.get("id")
    _sync_remark_widgets(new_remarks)


qp = st.query_params
if supabase is not None and "store" in qp and "date" in qp and st.session_state["loaded_key"] is None:
    row = fetch_draft(qp["store"], qp["date"])
    if row:
        load_into_state(row)

st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">📋</div>
        <h2>DETAIL AUDIT</h2>
        <p>Isi penilaian audit toko, simpan, lanjut ke QC Image Inserter untuk foto</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if supabase is None:
    st.error("Supabase belum terkoneksi. Isi SUPABASE_URL & SUPABASE_KEY di secrets.")

with st.expander("📂 Buka data toko yang tersimpan (lanjutkan audit)"):
    rows = list_saved_drafts()
    if rows:
        options = {
            f"{r['store_name']}  —  {r['audit_date']}  (update: {r['updated_at'][:16].replace('T',' ')})": r
            for r in rows
        }
        choice = st.selectbox("Pilih draft", ["-- pilih --"] + list(options.keys()))
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("🔄 Muat Draft", disabled=(choice == "-- pilih --")):
                picked = options[choice]
                full = fetch_draft(picked["store_name"], picked["audit_date"])
                if full:
                    load_into_state(full)
                    st.query_params["store"] = picked["store_name"]
                    st.query_params["date"] = picked["audit_date"]
                    st.rerun()
        with col_b:
            if st.button("🆕 Mulai Audit Baru"):
                reset_form()
                st.rerun()
        with col_c:
            update_disabled = st.session_state["loaded_id"] is None
            if st.button("✏️ Update Draft Ini", disabled=update_disabled):
                try:
                    update_draft_by_id(st.session_state["loaded_id"], {
                        "store_name": st.session_state["store_name"],
                        "audit_date": st.session_state["date1"],
                        "date2": st.session_state["date2"],
                        "auditor": st.session_state["auditor"],
                        "pic_on_duty": st.session_state["pic_on_duty"],
                        "remarks": st.session_state["remarks"],
                    })
                    st.session_state["loaded_key"] = (st.session_state["store_name"], st.session_state["date1"])
                    st.query_params["store"] = st.session_state["store_name"]
                    st.query_params["date"] = st.session_state["date1"]
                    # ── LOG: Update ──
                    _upd_result = compute_all(structure, st.session_state["remarks"])
                    _upd_score = f"{round(_upd_result['final_score'], 2)}, {_upd_result['grade']}"
                    log_audit_traffic(
                        st.session_state.get("auditor", ""),
                        st.session_state.get("store_name", ""),
                        st.session_state.get("date1", ""),
                        _upd_score,
                        "Update",
                    )
                    st.success("Draft ini berhasil diperbarui (nama/tanggal ikut berubah kalau memang diubah, tidak membuat draft baru).")
                except Exception as e:
                    st.error(f"Gagal update: {e}")
        st.caption(
            "**Muat Draft** = buka draft lain. **Update Draft Ini** = simpan perubahan "
            "(termasuk ganti Store Name/Date) ke draft yang sedang aktif di form ini, "
            "tanpa membuat draft baru. Aktif hanya kalau ada draft yang sedang dimuat."
        )
    else:
        st.caption("Belum ada draft tersimpan.")

st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    st.session_state["store_name"] = st.text_input("STORE NAME", value=st.session_state["store_name"])
    st.session_state["date1"] = st.text_input("DATE", value=st.session_state["date1"])
    st.session_state["date2"] = st.text_input("DATE (2)", value=st.session_state["date2"])
with c2:
    st.session_state["auditor"] = st.text_input("AUDITOR", value=st.session_state["auditor"])
    st.session_state["pic_on_duty"] = st.text_input("PIC ON DUTY", value=st.session_state["pic_on_duty"])

st.markdown("---")
st.subheader("DETAIL TO VERIFY")
st.caption("Isi kolom Remarks kalau ada temuan. Remarks terisi -> Actual Score poin itu otomatis 0.")

remarks_state = st.session_state["remarks"]
ROW_COLS = [0.5, 4.2, 0.9, 0.9, 3.5]


def render_header_row():
    h = st.columns(ROW_COLS)
    h[0].markdown("**No**")
    h[1].markdown("**Deskripsi**")
    h[2].markdown("**Basic**")
    h[3].markdown("**Actual**")
    h[4].markdown("**Remarks**")


def render_table(items: list[dict], key: str):
    render_header_row()
    for it in items:
        number = str(it["number"])
        widget_key = f"{key}_remark_{number}"

        if widget_key in st.session_state:
            current = _safe_remark(st.session_state[widget_key])
        else:
            current = _safe_remark(remarks_state.get(number, ""))

        actual = 0 if current.strip() else it["basic"]

        cols = st.columns(ROW_COLS)
        cols[0].markdown(str(it["number"]))
        cols[1].markdown(it["desc"])
        cols[2].markdown(str(it["basic"]))
        if actual == 0:
            cols[3].markdown(f":red[**{actual}**]")
        else:
            cols[3].markdown(str(actual))

        new_val = cols[4].text_area(
            "Remarks", value=current, key=widget_key,
            label_visibility="collapsed", height=68,
        )
        remarks_state[number] = _safe_remark(new_val)
        st.markdown("<hr style='margin:4px 0;opacity:0.15'>", unsafe_allow_html=True)


def category_banner(name: str):
    st.markdown(f"<div class='cat-banner'>{name}</div>", unsafe_allow_html=True)


for cat in structure:
    category_banner(cat["name"])
    note = cat.get("note")
    if note:
        st.info(f"{note['note_number']}. {note['note_text']}")
    if "subcategories" in cat:
        for sub in cat["subcategories"]:
            st.markdown(f"<div class='subcat-label'>{sub['name']}</div>", unsafe_allow_html=True)
            render_table(sub["items"], key=f"editor_{sub['row']}")
    else:
        render_table(cat.get("items", []), key=f"editor_{cat['row']}")

st.session_state["remarks"] = remarks_state

result = compute_all(structure, remarks_state)

st.markdown("---")
st.subheader("📊 Rincian Nilai per Kategori")
summary_df = pd.DataFrame([
    {"Kategori": c["name"], "Basic Score": c["basic"], "Actual Score": c["actual"], "%": round(c["percent"], 2)}
    for c in result["categories"]
])
st.dataframe(summary_df, hide_index=True, width="stretch")

m1, m2, m3 = st.columns(3)
m1.metric("TOTAL SCORE (E184)", round(result["grand_percent_sum"], 2))
m2.metric("FINAL SCORE", round(result["final_score"], 2))
m3.metric("GRADING", result["grade"])

st.markdown("<div style=\"height:110px\"></div><span id='page-bottom'></span>", unsafe_allow_html=True)

# ── Format score untuk log (Save & Download pakai ini) ──
_score_str = f"{round(result['final_score'], 2)}, {result['grade']}"

with st.container(key="floating_actions"):
    fc1, fc2 = st.columns(2)
    with fc1:
        if st.button("💾", help="Save draft ke Supabase"):
            if not st.session_state["store_name"] or not st.session_state["date1"]:
                st.error("STORE NAME & DATE wajib diisi.")
            else:
                try:
                    save_draft({
                        "store_name": st.session_state["store_name"],
                        "audit_date": st.session_state["date1"],
                        "date2": st.session_state["date2"],
                        "auditor": st.session_state["auditor"],
                        "pic_on_duty": st.session_state["pic_on_duty"],
                        "remarks": remarks_state,
                    })
                    st.query_params["store"] = st.session_state["store_name"]
                    st.query_params["date"] = st.session_state["date1"]
                    st.session_state["loaded_key"] = (st.session_state["store_name"], st.session_state["date1"])
                    # ── LOG: Save ──
                    log_audit_traffic(
                        st.session_state.get("auditor", ""),
                        st.session_state.get("store_name", ""),
                        st.session_state.get("date1", ""),
                        _score_str,
                        "Save",
                    )
                    st.success("Tersimpan!")
                except Exception as e:
                    st.error(f"Gagal: {e}")

    with fc2:
        wb = build_filled_workbook(
            st.session_state["store_name"], st.session_state["date1"], st.session_state["date2"],
            st.session_state["auditor"], st.session_state["pic_on_duty"], remarks_state,
        )
        fname = f"Audit_{st.session_state['store_name'] or 'Store'}_{st.session_state['date1'] or 'Date'}.xlsx".replace(" ", "_")
        if st.download_button(
            "⬇️",
            data=workbook_to_bytes(wb),
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download Excel",
        ):
            # ── LOG: Download ──
            log_audit_traffic(
                st.session_state.get("auditor", ""),
                st.session_state.get("store_name", ""),
                st.session_state.get("date1", ""),
                _score_str,
                "Download",
            )

inject_footer()
