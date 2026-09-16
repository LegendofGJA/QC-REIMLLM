
import streamlit as st

from style import inject_css, inject_sidebar_brand, inject_footer
from audit_core import load_structure, sync_remark_widgets
from llm_core import (
    PROVIDER_LIST,
    fetch_provider_models,
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
    "llm_scan_status": {},
    "llm_last_unapplied": [],
    "llm_findings_text": "",
}

for state_key, default_value in DEFAULT_STATE.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


# ── HELPERS ───────────────────────────────────────────────
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
    col_provider, col_model, col_scan = st.columns([2, 3, 1])

    with col_provider:
        selected_provider = st.selectbox(
            "1. Pilih Provider",
            PROVIDER_LIST,
            key="llm_selected_provider",
        )

    is_proxy = "Proxy" in selected_provider
    is_byok = selected_provider == "BYOK (Custom)"

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
            st.success("BYOK tersimpan.")
            st.rerun()

    with col_scan:
        st.markdown(
            "<div style='height:28px;'></div>",
            unsafe_allow_html=True,
        )

        scan_clicked = st.button(
            "🔄 Scan & Test Ping",
            disabled=not (is_proxy or is_byok),
            help="Scan dan tes respons model provider yang dipilih.",
        )

    if scan_clicked:
        try:
            with st.spinner(
                f"Menguji model di {selected_provider}..."
            ):
                fetch_provider_models.clear(selected_provider)
                scanned = fetch_provider_models(selected_provider)

            # Core asli memberi awalan ✅ hanya pada hasil ping.
            # Model fallback tidak boleh diklaim lolos ping.
            verified_count = sum(
                1
                for label in scanned
                if str(label).startswith("✅ ")
            )

            if verified_count:
                scan_message = (
                    f"✅ {verified_count} model merespons HTTP 200 "
                    f"pada ping di {selected_provider}."
                )
            else:
                scan_message = (
                    "⚠️ Tidak ada hasil ping berhasil yang tersedia. "
                    "Daftar default ditampilkan jika tersedia; "
                    "ketersediaannya belum terverifikasi."
                )

            scan_status = dict(
                st.session_state["llm_scan_status"]
            )
            scan_status[selected_provider] = scan_message
            st.session_state["llm_scan_status"] = scan_status

        except Exception as error:
            st.error(f"Scan gagal: {error}")

    try:
        available_models = fetch_provider_models(
            selected_provider
        )
    except Exception as error:
        available_models = {}
        st.error(f"Gagal mengambil daftar model: {error}")

    with col_model:
        selected_model = st.selectbox(
            "2. Pilih Model AI",
            list(available_models.keys()),
            key=f"llm_model_{selected_provider}",
            disabled=not bool(available_models),
        )

    scan_message = st.session_state["llm_scan_status"].get(
        selected_provider
    )

    if scan_message:
        st.caption(scan_message)

    if available_models and not any(
        str(label).startswith("✅ ")
        for label in available_models
    ):
        st.caption(
            "Daftar model default. Model dalam daftar ini "
            "belum terverifikasi melalui ping."
        )

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
            
