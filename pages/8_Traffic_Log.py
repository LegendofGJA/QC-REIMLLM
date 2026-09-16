import pandas as pd
import streamlit as st

from style import (
    inject_css,
    inject_sidebar_brand,
    inject_footer,
    convert_utc_to_wib,
)
from audit_core import get_supabase_client

st.set_page_config(page_title="Traffic Log", page_icon="📈", layout="wide")
inject_css()
inject_sidebar_brand()

st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">📈</div>
        <h2>Traffic Log</h2>
        <p>Riwayat pemakaian QC Image Inserter (siapa, toko mana, kapan)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "traffic_ok" not in st.session_state:
    st.session_state.traffic_ok = False

if not st.session_state.traffic_ok:
    pw = st.text_input("Password Traffic Log", type="password")
    if st.button("Masuk"):
        try:
            correct = st.secrets["TRAFFIC_LOG_PASSWORD"]
        except Exception:
            correct = None
        if correct is None:
            st.error("TRAFFIC_LOG_PASSWORD belum diatur di secrets.")
        elif pw == correct:
            st.session_state.traffic_ok = True
            st.rerun()
        else:
            st.error("Password salah.")
    st.stop()

st.success("Login berhasil.")
if st.button("Keluar"):
    st.session_state.traffic_ok = False
    st.rerun()

st.markdown("---")

if st.button("🔄 Refresh"):
    st.cache_data.clear()


@st.cache_data(ttl=60)
def fetch_log():
    supabase = get_supabase_client()
    if supabase is None:
        return []
    try:
        resp = (
            supabase.table("audit_traffic_log")
            .select("auditor", "store_name", "audit_date", "score_info", "created_at")
            .order("created_at", desc=False)
            .limit(500)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        st.error(f"Gagal mengambil data log: {e}")
        return []


try:
    data = fetch_log()
except Exception as e:
    st.error(f"Gagal mengambil data log: {e}")
    data = []

if not data:
    st.caption("Belum ada log tercatat.")
else:
    rows = []
    for r in data:
        ts = convert_utc_to_wib(r.get("created_at", ""))
        rows.append({
            "Nama Pengguna": r.get("auditor", ""),
            "Nama Toko": r.get("store_name", ""),
            "Tanggal QC": r.get("audit_date", ""),
            "Detail": r.get("score_info", ""),
            "Timestamp": ts,
        })
    df = pd.DataFrame(rows)

    st.caption(f"Total {len(df)} aktivitas tercatat.")

    with st.expander("🔍 Filter"):
        f1, f2 = st.columns(2)
        nama_filter = f1.text_input("Filter Nama Pengguna")
        toko_filter = f2.text_input("Filter Nama Toko")

    if nama_filter:
        df = df[df.get("Nama Pengguna", "").astype(str).str.contains(nama_filter, case=False, na=False)]
    if toko_filter:
        df = df[df.get("Nama Toko", "").astype(str).str.contains(toko_filter, case=False, na=False)]

    st.dataframe(df, hide_index=True, width="stretch")

st.caption(
    "Catatan: log ini disimpan di Supabase (tabel audit_traffic_log), "
    "Halaman ini hanya menampilkan (read-only)."
)

inject_footer()
