import pandas as pd
import streamlit as st

from style import (
    inject_css,
    inject_sidebar_brand,
    inject_footer,
    convert_utc_to_wib,
)
from audit_core import (
    get_supabase_client,
    delete_all_audit_logs,
    delete_audit_log_by_id,
)

st.set_page_config(page_title="Audit Log", page_icon="📝", layout="wide")
inject_css()
inject_sidebar_brand()

st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">📝</div>
        <h2>Audit Log</h2>
        <p>Riwayat Save, Download & Update di halaman DETAIL AUDIT</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Password protection ──
if "audit_log_ok" not in st.session_state:
    st.session_state.audit_log_ok = False

if not st.session_state.audit_log_ok:
    pw = st.text_input("Password", type="password")
    if st.button("Masuk"):
        try:
            correct = st.secrets["TRAFFIC_LOG_PASSWORD"]
        except Exception:
            correct = None
        if correct is None:
            st.error("TRAFFIC_LOG_PASSWORD belum diatur di secrets.")
        elif pw == correct:
            st.session_state.audit_log_ok = True
            st.rerun()
        else:
            st.error("Password salah.")
    st.stop()

st.success("Login berhasil.")
if st.button("Keluar"):
    st.session_state.audit_log_ok = False
    st.rerun()

st.markdown("---")

if st.button("🔄 Refresh"):
    st.cache_data.clear()


@st.cache_data(ttl=60)
def fetch_audit_log():
    supabase = get_supabase_client()
    if supabase is None:
        return [], []
    try:
        resp = (
            supabase.table("audit_traffic_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        data = resp.data or []
        formatted = []
        for r in data:
            ts = convert_utc_to_wib(r.get("created_at", ""))
            formatted.append({
                "id": r.get("id", ""),
                "Auditor": r.get("auditor", ""),
                "Store": r.get("store_name", ""),
                "Date QC": r.get("audit_date", ""),
                "Score": r.get("score_info", ""),
                "Action": r.get("action", ""),
                "Timestamp": ts,
            })
        return formatted, data
    except Exception:
        return [], []


try:
    display_data, raw_data = fetch_audit_log()
except Exception as e:
    st.error(f"Gagal mengambil data log: {e}")
    display_data, raw_data = [], []

if not display_data:
    st.caption("Belum ada log tercatat.")
    inject_footer()
    st.stop()

# ── TABEL + FILTER ──
st.caption(f"Total {len(display_data)} aktivitas tercatat.")

df = pd.DataFrame(display_data)

with st.expander("🔍 Filter"):
    f1, f2, f3 = st.columns(3)
    auditor_filter = f1.text_input("Filter Auditor")
    store_filter = f2.text_input("Filter Store")
    action_filter = f3.selectbox("Filter Action", ["Semua", "Save", "Download", "Update"])

df_display = df[["Auditor", "Store", "Date QC", "Score", "Action", "Timestamp"]].copy()

if auditor_filter:
    df_display = df_display[df_display["Auditor"].astype(str).str.contains(auditor_filter, case=False, na=False)]
if store_filter:
    df_display = df_display[df_display["Store"].astype(str).str.contains(store_filter, case=False, na=False)]
if action_filter != "Semua":
    df_display = df_display[df_display["Action"] == action_filter]

st.dataframe(df_display, hide_index=True, width="stretch")

st.markdown("---")

# ── HAPUS SEMUA LOG ──
st.markdown(
    """
    <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
         border-radius:10px; padding:14px 18px; margin-bottom:18px;">
        <p style="color:#fca5a5; font-size:0.82rem; margin:0; line-height:1.5;">
            <b>Hapus Semua</b> akan menghapus SELURUH log aktivitas. Aksi ini tidak bisa dibatalkan.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_del_all_1, col_del_all_2 = st.columns([1, 3])
with col_del_all_1:
    if st.button("🗑️ Hapus Semua Log", type="primary"):
        st.session_state["confirm_delete_all_logs"] = True

if st.session_state.get("confirm_delete_all_logs"):
    st.warning(f"Yakin ingin menghapus SEMUA {len(display_data)} log? Ketik **HAPUS** untuk konfirmasi.")
    confirm_text = st.text_input("Ketik HAPUS untuk konfirmasi", key="delete_all_logs_confirm")
    c_yakin, c_batal = st.columns(2)
    with c_yakin:
        if st.button("⚠️ Ya, Hapus Semua", disabled=(confirm_text.strip().upper() != "HAPUS")):
            try:
                delete_all_audit_logs()
                st.success(f"Semua {len(display_data)} log berhasil dihapus.")
                st.session_state["confirm_delete_all_logs"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Gagal: {e}")
    with c_batal:
        if st.button("✖️ Batal"):
            st.session_state["confirm_delete_all_logs"] = False
            st.rerun()

st.markdown("---")

# ── HAPUS PER ITEM ──
st.markdown("##### Hapus Log Individual")

options = {
    f"{r['Auditor']}  —  {r['Store']}  —  {r['Date QC']}  ({r['Action']}, {r['Timestamp']})": r
    for r in display_data
}
pick = st.selectbox("Pilih log:", ["-- pilih --"] + list(options.keys()), key="log_pick")

if pick != "-- pilih --":
    picked = options[pick]
    log_id = picked["id"]

    st.info(
        f"**Auditor:** {picked['Auditor']}  \n"
        f"**Store:** {picked['Store']}  \n"
        f"**Date QC:** {picked['Date QC']}  \n"
        f"**Score:** {picked['Score']}  \n"
        f"**Action:** {picked['Action']}  \n"
        f"**Timestamp:** {picked['Timestamp']}"
    )

    if st.button("🗑️ Hapus Log Ini"):
        st.session_state[f"confirm_del_log_{log_id}"] = True

    if st.session_state.get(f"confirm_del_log_{log_id}"):
        st.warning("Yakin hapus log ini?")
        c_y, c_n = st.columns(2)
        with c_y:
            if st.button("⚠️ Ya, Hapus", key=f"yes_log_{log_id}"):
                try:
                    delete_audit_log_by_id(log_id)
                    st.success("Log dihapus.")
                    st.session_state[f"confirm_del_log_{log_id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")
        with c_n:
            if st.button("✖️ Batal", key=f"no_log_{log_id}"):
                st.session_state[f"confirm_del_log_{log_id}"] = False
                st.rerun()

inject_footer()
