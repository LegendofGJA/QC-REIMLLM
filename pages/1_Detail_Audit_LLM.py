from datetime import datetime, timedelta, timezone

import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer
from audit_core import load_structure, sync_remark_widgets
from llm_core import (
    PROVIDER_LIST,
    FALLBACK_MODELS,
    scan_provider_models,
    ping_provider_model,
    get_provider_cache,
    save_provider_scan,
    save_provider_test,
    clear_provider_cache,
    call_llm,
    get_byok_config,
    save_byok_config,
)


st.set_page_config(
    page_title="Detail Audit (AI)",
    page_icon="🤖",
    layout="wide",
)

inject_css()
inject_sidebar_brand()


# ── SESSION STATE ─────────────────────────────────────────
DEFAULT_STATE = {
    "llm_suggestions": [],
    "llm_unmatched": [],
    "llm_msg": None,
    "llm_run_id": 0,
    "llm_last_processed_text": None,
    "llm_last_processed_model": None,
    "llm_last_unapplied": [],
    "llm_findings_text": "",
}

for state_key, default_value in DEFAULT_STATE.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


# ── HELPERS ───────────────────────────────────────────────
def _now_wib_str() -> str:
    """Jam sekarang format WIB (UTC+7) untuk penanda waktu cache bersama."""
    return datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M WIB")


def normalise_unmatched(value):
    """Membuat hasil unmatched aman ditampilkan sebagai teks."""
    if value is None:
        return []

    entries = value if isinstance(value, list) else [value]
    result = []

    for entry in entries:
        if entry is None:
            continue

        if isinstance(entry, dict):
            text = (
                entry.get("text")
                or entry.get("finding")
                or entry.get("remark")
                or entry.get("description")
                or str(entry)
            )

            reason = entry.get("reason")
            source_ids = entry.get("source_ids", [])

            if isinstance(source_ids, str):
                source_ids = [source_ids]

            prefix = ""
            if isinstance(source_ids, list) and source_ids:
                prefix = "[" + ", ".join(
                    str(source_id) for source_id in source_ids
                ) + "] "

            text = prefix + str(text).strip()

            if reason:
                text += f"\nAlasan: {reason}"
        else:
            text = str(entry).strip()

        if text:
            result.append(text)

    return result


def show_findings(entries):
    """Tidak merender teks temuan sebagai HTML."""
    for index, text in enumerate(entries, start=1):
        st.text(f"{index}. {text}")


def clear_review_widgets():
    """Hapus nilai widget review dari proses AI sebelumnya."""
    prefixes = (
        "sugg_accept_",
        "sugg_remark_",
        "llm_review_accept_",
        "llm_review_remark_",
    )

    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(prefixes):
            del st.session_state[key]


# ── HEADER ───────────────────────────────────────────────
st.markdown(
    """
    <div class="page-head">
        <div class="page-head-icon">🤖</div>
        <h2>Detail Audit — Bantuan AI</h2>
        <p>
            Paste catatan temuan bebas, AI usulkan pemetaan ke
            checklist. Penerapan hasil membuat draft baru.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── MASTER CHECKLIST ──────────────────────────────────────
structure = load_structure()

item_lookup = {}

for category in structure:
    if category.get("name") == "ETC":
        continue

    groups = (
        [
            subcategory["items"]
            for subcategory in category["subcategories"]
        ]
        if "subcategories" in category
        else [category.get("items", [])]
    )

    for group in groups:
        for item in group:
            item_lookup[int(item["number"])] = item["desc"]


# ── FORM PROSES TEMUAN ────────────────────────────────────
with st.expander("🤖 Proses Temuan dengan AI", expanded=True):
    col_provider, col_model = st.columns([2, 3])

    with col_provider:
        selected_provider = st.selectbox(
            "1. Pilih Provider",
            PROVIDER_LIST,
            key="llm_selected_provider",
        )

    is_byok = selected_provider == "BYOK (Custom)"

    # Sumber daftar model dropdown (dibaca dari cache bersama lintas tab & device):
    # 1) Jika sudah klik Test  -> hanya model yang hidup (lolos ping)
    # 2) Jika sudah klik Scan  -> semua model hasil Auto-Scan (0 token)
    # 3) Belum Scan            -> daftar default FALLBACK_MODELS (0 token)
    provider_cache = get_provider_cache(selected_provider)

    if provider_cache["has_tested"]:
        available_models = provider_cache["tested_models"]
        model_source = "tested"
    elif provider_cache["has_scanned"]:
        available_models = provider_cache["scanned_models"]
        model_source = "scanned"
    else:
        available_models = FALLBACK_MODELS.get(selected_provider, {})
        model_source = "fallback"

    model_widget_key = f"llm_model_{selected_provider}"
    model_options = list(available_models.keys())
    if (
        model_widget_key in st.session_state
        and st.session_state[model_widget_key] not in model_options
    ):
        del st.session_state[model_widget_key]

    with col_model:
        selected_model = st.selectbox(
            "2. Pilih Model AI",
            model_options,
            key=model_widget_key,
            disabled=not bool(model_options),
        )

    byok_url = ""
    byok_key = ""
    if is_byok:
        byok_cfg = get_byok_config()
        st.markdown(
            "<div style='height:8px;'></div>",
            unsafe_allow_html=True,
        )
        col_burl, col_bkey = st.columns(2)
        byok_url = col_burl.text_input(
            "BYOK Base URL",
            value=byok_cfg.get("base_url", ""),
            placeholder="https://api.provider.com/v1",
            key="byok_base_url",
        )
        byok_key = col_bkey.text_input(
            "BYOK API Key",
            value=byok_cfg.get("api_key", ""),
            placeholder="sk-...",
            key="byok_api_key",
        )
        if st.button("💾 Simpan BYOK (share ke device lain)", use_container_width=True):
            save_byok_config(byok_url, byok_key)
            clear_provider_cache(selected_provider)
            st.session_state.pop(model_widget_key, None)
            st.success("BYOK tersimpan.")
            st.rerun()

    # ── 2 BUTTON DI BAWAH: SCAN (0 TOKEN) & TEST (PING HIDUP) ──
    models_to_test = (
        provider_cache["scanned_models"]
        if provider_cache["has_scanned"]
        else FALLBACK_MODELS.get(selected_provider, {})
    )

    col_btn_scan, col_btn_test = st.columns(2)
    with col_btn_scan:
        scan_clicked = st.button(
            "🔍 Scan",
            use_container_width=True,
            help="Auto-scan daftar model dari server (/models) tanpa memakan token.",
        )
    with col_btn_test:
        test_clicked = st.button(
            "🩺 Test",
            use_container_width=True,
            disabled=not bool(models_to_test),
            help=(
                "Tes kesehatan (ping) semua model untuk menyaring "
                "hanya model yang hidup di dropdown (tersimpan lintas tab & device)."
            ),
        )

    if scan_clicked:
        if is_byok and byok_url.strip() and byok_key.strip():
            save_byok_config(byok_url, byok_key)
        try:
            with st.spinner(
                f"Auto-scan daftar model dari {selected_provider}..."
            ):
                scanned = scan_provider_models(selected_provider)

            status_msg = (
                f"🔍 Berhasil menemukan **{len(scanned)} model** dari "
                f"{selected_provider} (0 token · {_now_wib_str()}). "
                "Klik **Test** jika ingin menyaring model yang hidup saja."
            )
            save_provider_scan(selected_provider, scanned, status_msg)

            st.session_state.pop(model_widget_key, None)
            st.rerun()

        except Exception as error:
            st.error(f"Scan gagal: {error}")

    if test_clicked:
        if is_byok and byok_url.strip() and byok_key.strip():
            save_byok_config(byok_url, byok_key)

        progress_bar = st.progress(0)
        progress_text = st.empty()
        results = []

        target_items = list(models_to_test.items())
        total = len(target_items)

        for index, (label, cfg) in enumerate(target_items, start=1):
            model_id = cfg["model"]
            progress_text.markdown(
                f"🔎 Testing **{index}/{total}** — `{model_id}`..."
            )
            res = ping_provider_model(
                selected_provider,
                model_id,
                timeout=20,
            )
            res["label"] = label
            res["provider"] = cfg["provider"]
            results.append(res)
            progress_bar.progress(index / total)

        progress_bar.empty()
        progress_text.empty()

        alive_results = sorted(
            [r for r in results if r["alive"]],
            key=lambda x: x["latency"] if x["latency"] is not None else 999,
        )

        alive_models = {}
        for r in alive_results:
            model_id = r["model"]
            alive_models[model_id] = {
                "provider": r["provider"],
                "model": model_id,
            }

        if alive_models:
            status_msg = (
                f"✅ {len(alive_models)} dari {len(results)} model hidup "
                f"di {selected_provider} (tersimpan lintas tab/device · {_now_wib_str()}). "
                "Dropdown hanya menampilkan model yang aktif."
            )
        else:
            status_msg = (
                f"❌ Tidak ada model yang merespons hidup di {selected_provider} "
                f"(0 dari {len(results)} · {_now_wib_str()}). "
                "Klik **Scan** untuk melihat semua model kembali."
            )
        save_provider_test(selected_provider, alive_models, results, status_msg)

        st.session_state.pop(model_widget_key, None)
        st.rerun()

    # ── STATUS SCAN & HASIL TEST (SEPERTI CEK MODEL AI) ──
    scan_message = provider_cache["scan_status"]
    if scan_message:
        st.caption(scan_message)

    if model_source == "scanned" and available_models:
        sample_ids = [cfg["model"] for cfg in available_models.values()]
        st.caption(
            "Contoh ID Model: "
            + ", ".join([f"`{m}`" for m in sample_ids[:8]])
            + ("..." if len(sample_ids) > 8 else "")
        )
    elif model_source == "fallback" and available_models:
        st.caption(
            "Daftar model default (belum di-scan, 0 token terpakai). "
            "Klik **Scan** untuk memuat semua model dari server."
        )

    test_results = provider_cache["test_results"]
    if test_results:
        alive = [r for r in test_results if r["alive"]]
        dead = [r for r in test_results if not r["alive"]]

        c_tot, c_ok, c_err = st.columns(3)
        c_tot.metric("Total Model Scanned", len(test_results))
        c_ok.metric("✅ Model Aktif/Hidup", len(alive))
        c_err.metric("❌ Model Error/Mati", len(dead))

        if st.toggle(
            "📋 Tampilkan Detail Hasil Test Model",
            value=False,
            key=f"llm_show_test_detail_{selected_provider}",
        ):
            if alive:
                st.markdown("**✅ Model yang Bisa Digunakan**")
                for r in sorted(
                    alive,
                    key=lambda x: x["latency"] if x["latency"] is not None else 999,
                ):
                    st.markdown(f"- **`{r['model']}`** — ⚡ `{r['latency']:.2f}s`")
            if dead:
                st.markdown("**❌ Model Error / Tidak Merespons**")
                for r in dead:
                    st.markdown(f"- **`{r['model']}`** — ⚠️ {r['detail']}")


    findings_text = st.text_area(
        "Paste temuan (bebas, boleh tidak rapi)",
        height=220,
        placeholder=(
            "Contoh:\n"
            "Pearl habis\n"
            "Tent card berdebu\n"
            "Rama\n"
            "Tidak menggunakan sarung tangan"
        ),
        key="llm_findings_text",
    )

    process_clicked = st.button(
        "🤖 Proses dengan AI",
        type="primary",
        use_container_width=True,
        disabled=not bool(available_models),
    )

    if process_clicked:
        if not findings_text.strip():
            st.warning("Tulis/paste dulu temuannya.")
        else:
            # Kosongkan hasil lama agar kegagalan proses baru
            # tidak membuat hasil sebelumnya dianggap hasil baru.
            clear_review_widgets()
            st.session_state["llm_suggestions"] = []
            st.session_state["llm_unmatched"] = []
            st.session_state["llm_msg"] = None
            st.session_state["llm_last_processed_text"] = None
            st.session_state["llm_last_processed_model"] = None

            try:
                with st.spinner(
                    f"Memproses dengan {selected_model}..."
                ):
                    result = call_llm(
                        selected_model,
                        findings_text,
                        current_models=available_models,
                    )

                if not isinstance(result, dict):
                    raise ValueError(
                        "Hasil core AI harus berupa dictionary."
                    )

                matched = result.get("matched", [])
                unmatched = normalise_unmatched(
                    result.get("unmatched", [])
                )

                if not isinstance(matched, list):
                    unmatched.append(
                        "Format matched dari core tidak valid: "
                        f"{matched!r}"
                    )
                    matched = []

                # Validasi tambahan di UI.
                # Nomor sama digabung jika core mengembalikannya.
                grouped = {}

                for index, entry in enumerate(matched, start=1):
                    if not isinstance(entry, dict):
                        unmatched.append(
                            f"Hasil #{index} tidak valid: {entry!r}"
                        )
                        continue

                    raw_number = entry.get("number")
                    raw_remark = entry.get("remark")

                    if (
                        isinstance(raw_number, bool)
                        or not str(raw_number).strip().isdigit()
                    ):
                        unmatched.append(
                            "Nomor checklist tidak valid: "
                            f"{entry!r}"
                        )
                        continue

                    number = int(str(raw_number).strip())

                    if number not in item_lookup:
                        unmatched.append(
                            f"Checklist #{number} tidak tersedia: "
                            f"{entry!r}"
                        )
                        continue

                    if (
                        not isinstance(raw_remark, str)
                        or not raw_remark.strip()
                    ):
                        unmatched.append(
                            f"Remarks checklist #{number} kosong "
                            f"atau tidak valid: {entry!r}"
                        )
                        continue

                    remark = raw_remark.strip()

                    if number not in grouped:
                        grouped[number] = []

                    if remark not in grouped[number]:
                        grouped[number].append(remark)

                suggestions = [
                    {
                        "number": number,
                        "desc": item_lookup[number],
                        "remark": "; ".join(remarks),
                        "accept": True,
                    }
                    for number, remarks in sorted(grouped.items())
                ]

                if not suggestions and not unmatched:
                    unmatched = [
                        "AI tidak mengembalikan mapping maupun "
                        "daftar unmatched. Periksa seluruh input:\n"
                        + findings_text
                    ]

                st.session_state["llm_run_id"] += 1
                st.session_state["llm_suggestions"] = suggestions
                st.session_state["llm_unmatched"] = unmatched
                st.session_state["llm_last_processed_text"] = (
                    findings_text
                )
                st.session_state["llm_last_processed_model"] = (
                    selected_model
                )
                st.session_state["llm_msg"] = (
                    f"{len(suggestions)} box checklist berisi "
                    f"usulan AI. {len(unmatched)} catatan "
                    "belum masuk box dan perlu diperiksa."
                )

            except Exception as error:
                st.session_state["llm_unmatched"] = [
                    "Proses AI gagal. Seluruh input berikut "
                    "belum diterapkan:\n" + findings_text
                ]
                st.session_state["llm_msg"] = (
                    "Proses gagal. Input tetap tersedia "
                    "untuk diperiksa atau diproses ulang."
                )
                st.error(f"Gagal memproses: {error}")


# ── STATUS HASIL ──────────────────────────────────────────
message = st.session_state["llm_msg"]

if message:
    st.markdown("---")

    if st.session_state["llm_unmatched"]:
        st.warning(message)
    else:
        st.success(message)

last_processed_text = st.session_state["llm_last_processed_text"]

input_changed = (
    last_processed_text is not None
    and findings_text != last_processed_text
)

if input_changed:
    st.warning(
        "Input sudah berubah setelah proses terakhir. "
        "Proses ulang dengan AI sebelum menerapkan hasil."
    )

if last_processed_text is not None:
    with st.expander("📄 Input yang digunakan pada hasil ini"):
        st.caption(
            "Model: "
            + str(st.session_state["llm_last_processed_model"])
        )
        st.text(last_processed_text)


# ── TEMUAN TIDAK MASUK BOX ─────────────────────────────────
unmatched = normalise_unmatched(
    st.session_state["llm_unmatched"]
)

if unmatched:
    st.subheader("⚠️ Temuan yang Tidak Masuk Box Checklist")

    st.info(
        "Catatan berikut belum masuk ke remarks checklist. "
        "Periksa secara manual. Bagian ini tidak diterapkan "
        "ke DETAIL AUDIT dan tidak langsung memengaruhi skor."
    )

    show_findings(unmatched)

    st.download_button(
        "📥 Download catatan yang belum masuk box",
        data="\n\n".join(unmatched),
        file_name="temuan_belum_masuk_checklist.txt",
        mime="text/plain",
        key="llm_download_unmatched",
    )


# ── REVIEW USULAN ─────────────────────────────────────────
suggestions = st.session_state["llm_suggestions"]

if suggestions:
    st.subheader("📝 Review Usulan AI")
    st.caption(
        "Hilangkan centang untuk menolak usulan, atau edit "
        "remarks sebelum diterapkan. Beberapa temuan pada "
        "nomor yang sama dapat berada dalam satu box."
    )

    run_id = st.session_state["llm_run_id"]

    for index, suggestion in enumerate(suggestions):
        col_accept, col_number, col_desc, col_remark = (
            st.columns([0.6, 0.6, 3, 5])
        )

        accepted_value = col_accept.checkbox(
            f"Terapkan checklist {suggestion['number']}",
            value=suggestion.get("accept", True),
            key=f"llm_review_accept_{run_id}_{index}",
            label_visibility="collapsed",
        )

        col_number.markdown(
            f"**{suggestion['number']}**"
        )
        col_desc.write(suggestion["desc"])

        edited_remark = col_remark.text_area(
            f"Remarks checklist {suggestion['number']}",
            value=suggestion["remark"],
            key=f"llm_review_remark_{run_id}_{index}",
            height=90,
            label_visibility="collapsed",
        )

        suggestions[index]["accept"] = accepted_value
        suggestions[index]["remark"] = edited_remark

        st.markdown(
            "<hr style='margin:2px 0;opacity:0.12'>",
            unsafe_allow_html=True,
        )

    st.session_state["llm_suggestions"] = suggestions

    accepted_items = [
        item
        for item in suggestions
        if item["accept"] and item["remark"].strip()
    ]

    excluded_items = [
        item
        for item in suggestions
        if not item["accept"] or not item["remark"].strip()
    ]

    st.caption(
        f"**{len(accepted_items)}** dari "
        f"**{len(suggestions)}** box akan diterapkan."
    )

    if excluded_items:
        with st.expander(
            "Catatan yang tidak diterapkan dari hasil review",
            expanded=True,
        ):
            for item in excluded_items:
                reason = (
                    "Tidak dicentang"
                    if not item["accept"]
                    else "Remarks dikosongkan"
                )
                st.text(
                    f"#{item['number']} — {reason}\n"
                    f"{item['remark'].strip() or '(kosong)'}"
                )

    st.caption(
        "Penerapan hasil akan mengganti isian audit aktif "
        "dengan draft baru. Simpan draft lama terlebih dahulu "
        "jika masih diperlukan."
    )

    apply_clicked = st.button(
        "✅ Terapkan ke DETAIL AUDIT (draft baru)",
        type="primary",
        disabled=(
            not accepted_items
            or input_changed
            or last_processed_text is None
        ),
    )

    if apply_clicked:
        remarks = {}

        for item in accepted_items:
            number = str(item["number"])
            remark = item["remark"].strip()

            if number in remarks:
                remarks[number] += "; " + remark
            else:
                remarks[number] = remark

        # Simpan catatan belum diterapkan agar tidak hilang
        # saat pindah halaman. Ini hanya session state,
        # bukan penyimpanan permanen di database.
        unapplied = list(unmatched)

        for item in excluded_items:
            reason = (
                "Tidak dicentang"
                if not item["accept"]
                else "Remarks dikosongkan"
            )
            unapplied.append(
                f"#{item['number']} — {reason}: "
                f"{item['remark'].strip() or '(kosong)'}"
            )

        st.session_state["llm_last_unapplied"] = unapplied

        st.session_state["store_name"] = ""
        st.session_state["date1"] = ""
        st.session_state["date2"] = ""
        st.session_state["auditor"] = ""
        st.session_state["pic_on_duty"] = ""
        st.session_state["remarks"] = remarks
        st.session_state["loaded_key"] = None
        st.session_state["loaded_id"] = None

        sync_remark_widgets(structure, remarks)

        st.session_state["llm_suggestions"] = []
        st.session_state["llm_unmatched"] = []
        st.session_state["llm_msg"] = None
        st.session_state["llm_last_processed_text"] = None
        st.session_state["llm_last_processed_model"] = None

        st.switch_page("pages/2_Detail_Audit.py")


# ── CATATAN PENERAPAN TERAKHIR ─────────────────────────────
previous_unapplied = st.session_state["llm_last_unapplied"]

if previous_unapplied:
    with st.expander(
        "📌 Catatan belum diterapkan dari penerapan terakhir"
    ):
        st.caption(
            "Tersimpan sementara selama sesi Streamlit ini. "
            "Download jika ingin menyimpannya secara permanen."
        )

        show_findings(previous_unapplied)

        st.download_button(
            "📥 Download catatan penerapan terakhir",
            data="\n\n".join(previous_unapplied),
            file_name="catatan_belum_diterapkan_terakhir.txt",
            mime="text/plain",
            key="llm_download_previous_unapplied",
        )


inject_footer()
            
