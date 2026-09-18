"""
Halaman Cek Model AI — Auto Scan BYOK (Bring Your Own Key).

Fitur:
1. Pilihan URL bebas (Preset atau Custom URL/BYOK).
2. Keamanan Secrets: API key dari secrets TIDAK DITAMPILKAN secara polos.
3. Auto-Scan daftar model aktif dari endpoint `/v1/models`.
4. Tes kesehatan (latency & ketersediaan) seluruh model hasil scan.
"""

import time
import requests
import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer

st.set_page_config(page_title="Cek Model AI (Auto Scan)", page_icon="🩺", layout="wide")
inject_css()
inject_sidebar_brand()

st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">🩺</div>
        <h2>Cek Model AI — Auto Scan (BYOK)</h2>
        <p>Gunakan preset atau masukkan Base URL & API Key sendiri untuk scan daftar model secara otomatis dari server.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Preset Provider Bawaan ──
PRESET_PROVIDERS = {
    "Kagiro": {
        "url": "https://api.kagiro.net/v1",
        "secret": "KAGIRO_API_KEY",
    },
    "Bandelbanget Proxy": {
        "url": "https://bandelbanget.xyz/v1",
        "secret": "BANDEL_API_KEY",
    },
    "Cartridge": {
        "url": "https://router.cartridge.my.id/v1",
        "secret": "CARTRIDGE_API_KEY",
    },
    "Kenari": {
        "url": "https://kenari.id/v1/",
        "secret": "KENARI_API_KEY",
    },
    "GateAI": {
        "url": "https://gateai.id/v1/",
        "secret": "GATEAI_API_KEY",
    },
    "Juan": {
        "url": "https://router.juan.web.id/v1",
        "secret": "JUAN_API_KEY",
    },
    "SeekAI": {
        "url": "https://seekai.cc/v1/",
        "secret": "SEEKAI_API_KEY",
    },
    "DeepSeek Direct": {
        "url": "https://api.deepseek.com/v1",
        "secret": "DEEPSEEK_API_KEY",
    },
    "OpenRouter": {
        "url": "https://openrouter.ai/api/v1",
        "secret": None,
    },
    "Custom / Manual Input (BYOK)": {
        "url": "https://api.openai.com/v1",
        "secret": None,
    },
}

TEST_PROMPT = 'Balas HANYA JSON: {"ok": true}'


def _get_secret(name: str | None) -> str:
    if not name:
        return ""
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


# ── UI: KONFIGURASI ──
with st.expander("⚙️ Konfigurasi Server & API Key", expanded=True):
    col_p, col_t = st.columns([2, 1])
    with col_p:
        selected_preset = st.selectbox("Pilih Preset Provider / BYOK", list(PRESET_PROVIDERS.keys()))
    with col_t:
        timeout_s = st.number_input("Timeout tes per model (detik)", min_value=5, max_value=60, value=20)

    preset_cfg = PRESET_PROVIDERS[selected_preset]
    secret_key_val = _get_secret(preset_cfg["secret"])

    col_url, col_key = st.columns([2, 2])
    with col_url:
        # User bebas ubah URL apapun jika memilih Custom atau Preset
        base_url = st.text_input(
            "Base URL API (Kompatibel OpenAI /v1)",
            value=preset_cfg["url"],
            placeholder="Contoh: https://api.your-provider.com/v1",
        )

    with col_key:
        # Jika API key ada di Secrets, sembunyikan tampilan teks aslinya
        has_secret = bool(secret_key_val)
        placeholder_text = "•••••••• [Terisi dari Secrets]" if has_secret else "Masukkan sk-..."

        input_key = st.text_input(
            "API Key",
            value="",  # Kosongkan value default agar tidak membocorkan teks asli
            type="password",
            placeholder=placeholder_text,
            help="Kosongkan jika ingin menggunakan API Key bawaan dari secrets (jika ada)."
        )

        # Gunakan key input manual jika diisi, jika tidak gunakan dari secrets
        active_api_key = input_key.strip() if input_key.strip() else secret_key_val

# Format endpoint akhir
clean_base_url = base_url.rstrip("/")
models_endpoint = f"{clean_base_url}/models"
chat_endpoint = f"{clean_base_url}/chat/completions"


# ── AKSI 1: AUTO SCAN MODELS ──
st.markdown("---")
c_btn1, c_btn2 = st.columns([1, 1])

if c_btn1.button("🔍 Auto-Scan Daftar Model", type="primary", use_container_width=True):
    if not active_api_key:
        st.error("API Key belum diisi dan tidak ditemukan di Secrets!")
    else:
        with st.spinner(f"Mengkoneksikan ke {clean_base_url} & mendeteksi model..."):
            try:
                resp = requests.get(
                    models_endpoint,
                    headers={"Authorization": f"Bearer {active_api_key}"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    model_list = [m["id"] for m in data.get("data", []) if "id" in m]
                    model_list.sort()
                    st.session_state["scanned_models"] = model_list
                    st.session_state["scanned_key"] = active_api_key
                    st.session_state["scanned_url"] = chat_endpoint
                    st.session_state["check_results"] = None
                    st.success(f"Berhasil menemukan **{len(model_list)} model** dari server!")
                else:
                    st.error(f"Gagal Auto-Scan (HTTP {resp.status_code}): {resp.text[:200]}")
            except Exception as e:
                st.error(f"Error saat menghubungi server: {e}")
    # ── AKSI 2: TES KESEHATAN MODEL HASIL SCAN ──
scanned_models = st.session_state.get("scanned_models", [])

if scanned_models:
    st.subheader(f"📋 Terdeteksi {len(scanned_models)} Model Dari Server")
    st.caption("Contoh ID Model: " + ", ".join([f"`{m}`" for m in scanned_models[:8]]) + ("..." if len(scanned_models) > 8 else ""))

    if st.button("🩺 Tes Kesehatan Semua Model Hasil Scan", type="secondary", use_container_width=True):
        progress_bar = st.progress(0)
        progress_text = st.empty()
        results = []

        target_key = st.session_state.get("scanned_key", active_api_key)
        target_url = st.session_state.get("scanned_url", chat_endpoint)

        total = len(scanned_models)
        for i, model_id in enumerate(scanned_models, start=1):
            progress_text.markdown(f"🔎 Testing **{i}/{total}** — `{model_id}`...")
            
            start_time = time.time()
            try:
                resp = requests.post(
                    target_url,
                    headers={
                        "Authorization": f"Bearer {target_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": TEST_PROMPT}],
                        "max_tokens": 15,
                    },
                    timeout=timeout_s,
                )
                latency = time.time() - start_time
                if resp.status_code == 200:
                    results.append({"model": model_id, "alive": True, "latency": latency, "detail": "OK"})
                else:
                    err_msg = f"HTTP {resp.status_code}"
                    results.append({"model": model_id, "alive": False, "latency": latency, "detail": err_msg})
            except Exception as e:
                results.append({"model": model_id, "alive": False, "latency": None, "detail": str(e)[:80]})

            progress_bar.progress(i / total)

        progress_bar.empty()
        progress_text.empty()
        st.session_state["check_results"] = results


# ── DISPLAY HASIL KESEHATAN ──
results = st.session_state.get("check_results")
if results:
    alive = [r for r in results if r["alive"]]
    dead = [r for r in results if not r["alive"]]

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Model Scanned", len(results))
    c2.metric("✅ Model Aktif/Hidup", len(alive))
    c3.metric("❌ Model Error/Mati", len(dead))

    if alive:
        st.subheader("✅ Model yang Bisa Digunakan")
        for r in sorted(alive, key=lambda x: x["latency"] or 999):
            st.markdown(f"- **`{r['model']}`** — ⚡ `{r['latency']:.2f}s`")

    if dead:
        st.subheader("❌ Model Error / Tidak Merespons")
        for r in dead:
            st.markdown(f"- **`{r['model']}`** — ⚠️ {r['detail']}")

inject_footer()
