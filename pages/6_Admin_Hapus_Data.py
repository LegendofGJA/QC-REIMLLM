import pandas as pd
import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer
from audit_core import (
    list_saved_drafts,
    fetch_draft,
    delete_draft,
    update_draft_by_id,
    delete_all_drafts,
)

st.set_page_config(page_title="Admin - Kelola Data", page_icon="🔐", layout="wide")
inject_css()
inject_sidebar_brand()

# ── Password Protection ──
if "admin_ok" not in st.session_state:
    st.session_state.admin_ok = False

if not st.session_state.admin_ok:
    pw = st.text_input("Password Admin", type="password")
    if st.button("Masuk"):
        try:
            correct = st.secrets["ADMIN_PASSWORD"]
        except Exception:
            correct = None
        if correct is None:
            st.error("ADMIN_PASSWORD belum diatur di secrets.")
        elif pw == correct:
            st.session_state.admin_ok = True
            st.rerun()
        else:
            st.error("Password salah.")
    st.stop()

# ── Header ──
st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">🔐</div>
        <h2>Admin — Kelola Data Draft</h2>
        <p>Khusus master/admin. Edit, hapus, atau hapus semua draft DETAIL AUDIT dari Supabase.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.success("Login admin berhasil.")
if st.button("Keluar"):
    st.session_state.admin_ok = False
    st.rerun()

st.markdown("---")

# ── Load Data ──
rows = list_saved_drafts(limit=1000)

if not rows:
    st.caption("Belum ada draft tersimpan.")
    inject_footer()
    st.stop()

# ── TAMPILAN TABEL (seperti Traffic Log) ──
st.caption(f"Total {len(rows)} draft tersimpan.")

df = pd.DataFrame(rows)
if "updated_at" in df.columns:
    df["updated_at"] = df["updated_at"].astype(str).str[:16].str.replace("T", " ")
df_display = df.rename(columns={
    "store_name": "Store Name",
    "audit_date": "Date",
    "updated_at": "Last Update",
})
df_display = df_display[["Store Name", "Date", "Last Update"]]

with st.expander("🔍 Filter"):
    f1, f2 = st.columns(2)
    store_filter = f1.text_input("Filter Store Name")
    date_filter = f2.text_input("Filter Date")

if store_filter:
    df_display = df_display[df_display["Store Name"].astype(str).str.contains(store_filter, case=False, na=False)]
if date_filter:
    df_display = df_display[df_display["Date"].astype(str).str.contains(date_filter, case=False, na=False)]

st.dataframe(df_display, hide_index=True, width="stretch")

st.markdown("---")

# ── HAPUS SEMUA DATA ──
st.markdown(
    """
    <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
         border-radius:10px; padding:14px 18px; margin-bottom:18px;">
        <p style="color:#fca5a5; font-size:0.82rem; margin:0; line-height:1.5;">
            <b>Hapus Semua</b> akan menghapus SELURUH draft yang tersimpan. Aksi ini tidak bisa dibatalkan.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_del_all_1, col_del_all_2 = st.columns([1, 3])
with col_del_all_1:
    if st.button("🗑️ Hapus Semua Data", type="primary"):
        st.session_state["confirm_delete_all"] = True

if st.session_state.get("confirm_delete_all"):
    st.warning(f"Yakin ingin menghapus SEMUA {len(rows)} draft? Ketik **HAPUS** untuk konfirmasi.")
    confirm_text = st.text_input("Ketik HAPUS untuk konfirmasi", key="delete_all_confirm_input")
    c_yakin, c_batal = st.columns(2)
    with c_yakin:
        if st.button("⚠️ Ya, Hapus Semua", disabled=(confirm_text.strip().upper() != "HAPUS")):
            try:
                delete_all_drafts()
                st.success(f"Semua {len(rows)} draft berhasil dihapus.")
                st.session_state["confirm_delete_all"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Gagal: {e}")
    with c_batal:
        if st.button("✖️ Batal"):
            st.session_state["confirm_delete_all"] = False
            st.rerun()

st.markdown("---")

# ── EDIT / HAPUS PER ITEM ──
st.markdown("##### Edit atau Hapus Draft Individual")

options = {
    f"{r['store_name']}  —  {r['audit_date']}": r for r in rows
}
pick = st.selectbox("Pilih draft:", ["-- pilih --"] + list(options.keys()), key="admin_pick")

if pick != "-- pilih --":
    picked = options[pick]
    draft_id = picked["id"]
    full = fetch_draft(picked["store_name"], picked["audit_date"]) or picked

    e1, e2, e3 = st.columns(3)
    with e1:
        new_name = st.text_input("Store Name", value=full.get("store_name", ""), key="admin_edit_name")
    with e2:
        new_date = st.text_input("Date", value=full.get("audit_date", ""), key="admin_edit_date")
    with e3:
        new_auditor = st.text_input("Auditor", value=full.get("auditor", ""), key="admin_edit_auditor")

    btn_edit, btn_delete = st.columns(2)
    with btn_edit:
        if st.button("💾 Simpan Perubahan", use_container_width=True):
            try:
                update_draft_by_id(draft_id, {
                    "store_name": new_name.strip(),
                    "audit_date": new_date.strip(),
                    "auditor": new_auditor.strip(),
                })
                st.success(f"Draft diperbarui: {new_name.strip()} — {new_date.strip()}")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal: {e}")

    with btn_delete:
        if st.button("🗑️ Hapus Draft Ini", use_container_width=True):
            st.session_state[f"confirm_del_{draft_id}"] = True

    if st.session_state.get(f"confirm_del_{draft_id}"):
        st.warning(f"Yakin hapus draft **{picked['store_name']} — {picked['audit_date']}**?")
        c_y, c_n = st.columns(2)
        with c_y:
            if st.button("⚠️ Ya, Hapus", key=f"yes_{draft_id}"):
                try:
                    delete_draft(picked["store_name"], picked["audit_date"])
                    st.success("Draft dihapus.")
                    st.session_state[f"confirm_del_{draft_id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")
        with c_n:
            if st.button("✖️ Batal", key=f"no_{draft_id}"):
                st.session_state[f"confirm_del_{draft_id}"] = False
                st.rerun()

inject_footer()
