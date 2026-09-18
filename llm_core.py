"""
Modul integrasi LLM untuk halaman Detail Audit (AI).
Mendukung Auto-Scan + Health Check (Ping Test) per provider.
Hanya model yang merespons 200 OK yang akan dimasukkan ke list.
"""

from __future__ import annotations

import json
import re

import requests
import streamlit as st

from audit_core import load_structure


PROVIDER_LIST = [
    "Kagiro Proxy",
    "Bandelbanget Proxy",
    "Cartridge Proxy",
    "Kenari Proxy",
    "GateAI Proxy",
    "Juan Proxy",
    "SeekAI Proxy",
    "9router Proxy",
    "DeepSeek (Direct)",
    "Gemini (Direct)",
    "BYOK (Custom)",
]


# Gateway OpenAI-compatible generik: {nama_provider: (prefix_secret, base_url)}.
# Prefix dipakai untuk membaca <PREFIX>_API_KEY dari st.secrets. base_url boleh
# string kosong -> berarti URL diambil dari <PREFIX>_BASE_URL di secrets (dipakai
# 9router yang alamat tunnel-nya tidak boleh di-hardcode ke repo publik).
_GENERIC_GATEWAYS = {
    "Cartridge Proxy": ("CARTRIDGE", "https://router.cartridge.my.id/v1"),
    "Kenari Proxy": ("KENARI", "https://kenari.id/v1/"),
    "GateAI Proxy": ("GATEAI", "https://gateai.id/v1/"),
    "Juan Proxy": ("JUAN", "https://router.juan.web.id/v1"),
    "SeekAI Proxy": ("SEEKAI", "https://seekai.cc/v1/"),
    "9router Proxy": ("ROUTER9", ""),
}


def _resolve_base_url(prefix: str, default_url: str) -> str:
    """Base URL efektif: <PREFIX>_BASE_URL dari secrets kalau ada, jika tidak
    pakai default. Dipakai gateway yang URL-nya tidak boleh di-hardcode."""
    try:
        override = st.secrets.get(f"{prefix}_BASE_URL", "")
    except Exception:
        override = ""
    return (override or default_url).rstrip("/")


MODEL_METADATA = {
    # Bandelbanget Proxy
    "mimo-v2.5-pro": "Xiaomi MiMo V2.5 Pro (B-S) [1.4x]",
    "deepseek-v4-pro": "DeepSeek V4 Pro (B-S) [1.15x]",
    "deepseek-v4-pro-0813": "DeepSeek V4 Pro 0813 (B-S) [1.8x]",
    "kimi-k3": "Kimi K3 (B-S) [1x]",
    "deepseek-v4-mod": "DeepSeek V4 Mod (B-A) [1.25x]",
    "glm-5.3": "GLM 5.3 (B-A) [2x]",
    "glm-5.2": "GLM 5.2 (B-A) [1.25x]",
    "kimi-k2.7-code-highspeed": "Kimi K2.7 Code Highspeed (B-A) [1.5x]",
    "glm-5.1": "GLM 5.1 (B-B) [1x]",
    "hy3": "Hunyuan 3 / HY3 (B-B) [1x]",
    "deepseek-v4-flash": "DeepSeek V4 Flash (B-B) [2x]",
    "deepseek-v4-flash-0731": "DeepSeek V4 Flash 0731 (B-B) [2x]",

    # Kagiro Proxy
    "kagiro/claude-sonnet-4-6": "Claude Sonnet 4.6 (K-S) [4x]",
    "kagiro/claude-sonnet-5": "Claude Sonnet 5 (K-S) [5x]",
    "kagiro/deepseek-v4-pro": "DeepSeek V4 Pro (K-S) [2x]",
    "kagiro/claude-haiku4-5": "Claude Haiku 4.5 (K-S) [2x]",
    "kagiro/claude-opus-5": "Claude Opus 5 (K-A) [8x]",
    "kagiro/claude-opus-4-8": "Claude Opus 4.8 (K-A) [5x]",
    "kagiro/mimo-v2-5": "Xiaomi MiMo V2.5 (K-A) [1x]",
    "kagiro/glm5-3": "GLM 5.3 (K-A) [6x]",
    "kagiro/gemini-3-7-flash": "Gemini 3.7 Flash (K-B) [3x]",
    "kagiro/deepseek-v4-flash": "DeepSeek V4 Flash (K-B) [1.7x]",

    # DeepSeek V4.1 Flash (vision) — tersedia di gateway yang mendukung gambar
    "deepseek-v4.1-flash": "DeepSeek V4.1 Flash (Vision)",
    "cbai/deepseek-v4.1-flash": "DeepSeek V4.1 Flash (cbai) (Vision)",
}


FALLBACK_MODELS = {
    "Kagiro Proxy": {
        "Claude Sonnet 4.6 (K-S) [4x]": {
            "provider": "kagiro",
            "model": "kagiro/claude-sonnet-4-6",
        },
        "Claude Sonnet 5 (K-S) [5x]": {
            "provider": "kagiro",
            "model": "kagiro/claude-sonnet-5",
        },
        "DeepSeek V4 Pro (K-S) [2x]": {
            "provider": "kagiro",
            "model": "kagiro/deepseek-v4-pro",
        },
        "Claude Haiku 4.5 (K-S) [2x]": {
            "provider": "kagiro",
            "model": "kagiro/claude-haiku4-5",
        },
    },
    "Bandelbanget Proxy": {
        "Xiaomi MiMo V2.5 Pro (B-S) [1.4x]": {
            "provider": "bandelbanget",
            "model": "mimo-v2.5-pro",
        },
        "DeepSeek V4 Pro (B-S) [1.15x]": {
            "provider": "bandelbanget",
            "model": "deepseek-v4-pro",
        },
        "Kimi K3 (B-S) [1x]": {
            "provider": "bandelbanget",
            "model": "kimi-k3",
        },
        "GLM 5.1 (B-B) [1x]": {
            "provider": "bandelbanget",
            "model": "glm-5.1",
        },
    },
    "DeepSeek (Direct)": {
        "DeepSeek V4 Flash (Direct)": {
            "provider": "deepseek",
            "model": "deepseek-v4-flash",
        },
        "DeepSeek V4 Pro (Direct)": {
            "provider": "deepseek",
            "model": "deepseek-v4-pro",
        },
    },
    "Gemini (Direct)": {
        "Gemini 2.5 Flash (Direct)": {
            "provider": "gemini",
            "model": "gemini-flash-latest",
        },
        "Gemini 2.5 Flash-Lite (Direct)": {
            "provider": "gemini",
            "model": "gemini-flash-lite-latest",
        },
    },
    "Cartridge Proxy": {
        "DeepSeek V4.1 Flash (Vision)": {
            "provider": "cartridge",
            "model": "deepseek-v4.1-flash",
        },
    },
    "Kenari Proxy": {
        "DeepSeek V4.1 Flash (Vision)": {
            "provider": "kenari",
            "model": "deepseek-v4.1-flash",
        },
    },
    "GateAI Proxy": {
        "DeepSeek V4.1 Flash (Vision)": {
            "provider": "gateai",
            "model": "deepseek-v4.1-flash",
        },
    },
    "Juan Proxy": {
        "DeepSeek V4.1 Flash (Vision)": {
            "provider": "juan",
            "model": "deepseek-v4.1-flash",
        },
    },
    "SeekAI Proxy": {
        "DeepSeek V4.1 Flash (Vision)": {
            "provider": "seekai",
            "model": "deepseek-v4.1-flash",
        },
    },
    "9router Proxy": {
        # Id bervendor-prefix "cbai/" hanya ada di gateway 9router — sengaja
        # TIDAK dicantumkan di provider lain supaya tidak bocor/menggantung.
        "DeepSeek V4.1 Flash cbai (Vision)": {
            "provider": "9router",
            "model": "cbai/deepseek-v4.1-flash",
        },
        "DeepSeek V4.1 Flash (Vision)": {
            "provider": "9router",
            "model": "deepseek-v4.1-flash",
        },
    },
}


TEST_PROMPT = 'Balas HANYA: {"ok": true}'

_BYOK_DEFAULTS = {
    "base_url": "",
    "api_key": "",
}


@st.cache_data(show_spinner=False)
def get_byok_config() -> dict:
    """Config BYOK (base_url + api_key) yang dishare antar device.

    Nilai disimpan lewat st.cache_data supaya device lain yang mengakses
    app yang sama bisa membaca config yang sama tanpa perlu diinput ulang.
    """
    return dict(_BYOK_DEFAULTS)


def save_byok_config(base_url: str, api_key: str) -> None:
    """Simpan config BYOK ke cache Streamlit (shared antar device)."""
    global _BYOK_DEFAULTS
    _BYOK_DEFAULTS["base_url"] = (base_url or "").strip()
    _BYOK_DEFAULTS["api_key"] = (api_key or "").strip()
    get_byok_config.clear()
    get_byok_config()


def _ping_model(
    url: str,
    api_key: str,
    model_id: str,
    timeout: int = 6,
) -> bool:
    """Tes kesehatan mini untuk memastikan model merespons 200 OK."""
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": TEST_PROMPT,
                    }
                ],
                "max_tokens": 10,
            },
            timeout=timeout,
        )

        return response.status_code == 200

    except Exception:
        return False


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_provider_models(
    provider_name: str,
) -> dict[str, dict[str, str]]:
    """Scan + Ping Test model aktif khusus provider yang dipilih."""
    scanned_models = {}

    if provider_name == "Kagiro Proxy":
        api_key = st.secrets.get("KAGIRO_API_KEY", "")

        if api_key:
            try:
                response = requests.get(
                    "https://api.kagiro.net/v1/models",
                    headers={
                        "Authorization": f"Bearer {api_key}"
                    },
                    timeout=8,
                )

                if response.status_code == 200:
                    raw_models = [
                        model.get("id")
                        for model in response.json().get("data", [])
                        if model.get("id")
                    ]

                    for model_id in raw_models:
                        is_active = _ping_model(
                            "https://api.kagiro.net/v1/chat/completions",
                            api_key,
                            model_id,
                        )

                        if is_active:
                            label = MODEL_METADATA.get(
                                model_id,
                                (
                                    "Kagiro — "
                                    f"{model_id.replace('kagiro/', '')}"
                                ),
                            )

                            scanned_models[f"✅ {label}"] = {
                                "provider": "kagiro",
                                "model": model_id,
                            }

            except Exception:
                pass

    elif provider_name == "Bandelbanget Proxy":
        api_key = st.secrets.get("BANDEL_API_KEY", "")

        if api_key:
            try:
                response = requests.get(
                    "https://bandelbanget.xyz/v1/models",
                    headers={
                        "Authorization": f"Bearer {api_key}"
                    },
                    timeout=8,
                )

                if response.status_code == 200:
                    raw_models = [
                        model.get("id")
                        for model in response.json().get("data", [])
                        if model.get("id")
                    ]

                    for model_id in raw_models:
                        is_active = _ping_model(
                            "https://bandelbanget.xyz/v1/chat/completions",
                            api_key,
                            model_id,
                        )

                        if is_active:
                            label = MODEL_METADATA.get(
                                model_id,
                                f"Bandelbanget — {model_id}",
                            )

                            scanned_models[f"✅ {label}"] = {
                                "provider": "bandelbanget",
                                "model": model_id,
                            }

            except Exception:
                pass

    elif provider_name == "BYOK (Custom)":
        cfg = get_byok_config()
        base_url = cfg.get("base_url", "").rstrip("/")
        api_key = cfg.get("api_key", "")

        if base_url and api_key:
            try:
                response = requests.get(
                    f"{base_url}/models",
                    headers={
                        "Authorization": f"Bearer {api_key}"
                    },
                    timeout=8,
                )

                if response.status_code == 200:
                    raw_models = [
                        model.get("id")
                        for model in response.json().get("data", [])
                        if model.get("id")
                    ]

                    for model_id in raw_models:
                        is_active = _ping_model(
                            f"{base_url}/chat/completions",
                            api_key,
                            model_id,
                        )

                        if is_active:
                            label = f"BYOK — {model_id}"

                            scanned_models[f"✅ {label}"] = {
                                "provider": "byok",
                                "model": model_id,
                            }

            except Exception:
                pass

    elif provider_name in _GENERIC_GATEWAYS:
        # Gateway OpenAI-compatible generik (Cartridge / Kenari / GateAI /
        # Juan / SeekAI / 9router). Pola sama dengan Kagiro: ambil /models lalu
        # ping tiap model sebelum ditampilkan.
        prefix, default_url = _GENERIC_GATEWAYS[provider_name]
        base_url = _resolve_base_url(prefix, default_url)
        api_key = st.secrets.get(f"{prefix}_API_KEY", "")

        if base_url and api_key:
            try:
                response = requests.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=8,
                )

                if response.status_code == 200:
                    raw_models = [
                        model.get("id")
                        for model in response.json().get("data", [])
                        if model.get("id")
                    ]

                    for model_id in raw_models:
                        is_active = _ping_model(
                            f"{base_url.rstrip('/')}/chat/completions",
                            api_key,
                            model_id,
                        )

                        if is_active:
                            label = MODEL_METADATA.get(
                                model_id,
                                f"{provider_name} — {model_id}",
                            )

                            scanned_models[f"✅ {label}"] = {
                                "provider": prefix.lower(),
                                "model": model_id,
                            }

            except Exception:
                pass

    if scanned_models:
        return scanned_models

    return FALLBACK_MODELS.get(provider_name, {})


def _flat_item_list() -> list[dict]:
    structure = load_structure()
    items = []

    for category in structure:
        if category.get("name") == "ETC":
            continue

        groups = (
            [subcategory["items"] for subcategory in category["subcategories"]]
            if "subcategories" in category
            else [category.get("items", [])]
        )

        for group in groups:
            for item in group:
                items.append(
                    {
                        "number": item["number"],
                        "desc": item["desc"],
                    }
                )

    items.sort(key=lambda item: int(item["number"]))
    return items


def _build_prompt(findings_text: str) -> str:
    items = _flat_item_list()

    checklist_lines = "\n".join(
        f"{item['number']}. {item['desc']}"
        for item in items
    )

    return (
        "Kamu adalah asisten profesional yang bertugas menganalisis dan mencocokkan\n"
        "catatan temuan lapangan QC Toko Retail (Teazzi) ke nomor checklist audit resmi.\n"
        "\n"
        "DAFTAR CHECKLIST (nomor. deskripsi):\n"
        f"{checklist_lines}\n"
        "\n"
        "CATATAN TEMUAN DARI AUDITOR:\n"
        "\"\"\"\n"
        f"{findings_text}\n"
        "\"\"\"\n"
        "\n"
        "TUGAS:\n"
        "- Cocokkan setiap temuan ke NOMOR checklist yang paling spesifik.\n"
        "- Ubah teks temuan menjadi kalimat remarks ringkas dalam bahasa Indonesia.\n"
        "- Jangan menghilangkan temuan yang masih bermakna.\n"
        "- Temuan yang benar-benar tidak cocok harus dimasukkan ke \"unmatched\".\n"
        "\n"
        "ATURAN JUMLAH OUTPUT:\n"
        "- Setiap satu kalimat/baris temuan adalah satu item.\n"
        "- Jangan menggabungkan beberapa temuan menjadi satu item jika nomor checklist-nya berbeda.\n"
        "- Jika satu baris memiliki beberapa masalah yang berbeda, pisahkan jika memungkinkan.\n"
        "- Jika tidak ada nomor yang sesuai, masukkan teks aslinya ke \"unmatched\".\n"
        "- Hanya gunakan #109 Other jika benar-benar tidak ada checklist yang lebih sesuai.\n"
        "\n"
        "ATURAN PEMETAAN #37 DAN #38:\n"
        "- #37 adalah temuan produk/series habis atau sold out pada outlet/offline.\n"
        "- #38 adalah temuan produk/series habis atau sold out pada menu online.\n"
        "- Jika satu kalimat menyebut produk/series sold out atau habis melalui online DAN offline/outlet, keluarkan DUA item terpisah:\n"
        "  1. #37 untuk kondisi offline/outlet.\n"
        "  2. #38 untuk kondisi menu online.\n"
        "- Frasa \"via online maupun offline\", \"online dan offline\", \"online serta offline\", atau \"baik online maupun offline\" secara eksplisit menyatakan kedua kanal. Jangan hanya mengeluarkan #37.\n"
        "- Jangan menganggap #38 sebagai fakta baru jika kata \"online\" memang tertulis pada input.\n"
        "- Jangan mengeluarkan #38 jika hanya outlet/offline yang disebut.\n"
        "- Jangan mengeluarkan #37 jika hanya menu online yang disebut.\n"
        "- Jangan mengubah \"sold out\" atau \"habis\" menjadi expired, rusak, tidak tersedia permanen, atau rekomendasi pengadaan.\n"
        "\n"
        "CONTOH WAJIB:\n"
        "\n"
        "Input:\n"
        "Jasmine series sold out (habis) via online maupun offline\n"
        "\n"
        "Output items:\n"
        "[\n"
        "  {\n"
        "    \"number\": 37,\n"
        "    \"remark\": \"Jasmine series sold out di outlet/offline.\"\n"
        "  },\n"
        "  {\n"
        "    \"number\": 38,\n"
        "    \"remark\": \"Jasmine series sold out di menu online.\"\n"
        "  }\n"
        "]\n"
        "\n"
        "Input:\n"
        "Jasmine series habis di outlet\n"
        "\n"
        "Output items:\n"
        "[\n"
        "  {\n"
        "    \"number\": 37,\n"
        "    \"remark\": \"Jasmine series habis di outlet/offline.\"\n"
        "  }\n"
        "]\n"
        "\n"
        "Input:\n"
        "Jasmine series sold out di menu online\n"
        "\n"
        "Output items:\n"
        "[\n"
        "  {\n"
        "    \"number\": 38,\n"
        "    \"remark\": \"Jasmine series sold out di menu online.\"\n"
        "  }\n"
        "]\n"
        "\n"
        "ATURAN PEMETAAN LAINNYA:\n"
        "- Tidak menggunakan sarung tangan → #120.\n"
        "- Display cup, botol 1L, tent card, merchandise atau menu berdebu/kotor → #74.\n"
        "- Benda asing dalam topping → #126.\n"
        "- Tidak ada tanggal produksi → #123.\n"
        "- Timbangan kotor → #87.\n"
        "- Alat atau area yang harus segera dicuci → #86.\n"
        "- Rel sink atau rel lemari kotor → #85.\n"
        "- Alat kebersihan atau area lantai kotor → #83.\n"
        "- Stiker cup sobek atau potongannya tidak rapi → #56.\n"
        "- Stiker expiry date atau label yang masuk ke wadah → #126.\n"
        "- Resting teh tidak ditimer atau teh tidak disaring → #47.\n"
        "- Jigger tidak dibilas, shaker berkerak, milk jug butek, whisk kotor → #86.\n"
        "\n"
        "ATURAN NAMA STAFF:\n"
        "- Bersihkan keterangan fisik/status dalam tanda kurung.\n"
        "- Kaitkan nama staff hanya dengan temuan yang berada tepat di bawahnya.\n"
        "- Ubah nama menjadi Title Case.\n"
        "- Tambahkan nama bersih di akhir remarks dalam tanda kurung.\n"
        "- Nama staff tanpa temuan spesifik harus dimasukkan ke \"unmatched\".\n"
        "\n"
        "ATURAN:\n"
        "- Perbaiki typo secara wajar.\n"
        "- Jangan menambahkan fakta baru yang tidak ada di input.\n"
        "- Jika ada rekomendasi pengadaan atau operasional yang tidak memiliki checklist, masukkan ke \"unmatched\".\n"
        "\n"
        "INSTRUKSI PRIORITAS:\n"
        "Jangan berhenti setelah menemukan satu mapping. Untuk setiap sumber, periksa semua kanal yang disebut. Jika sumber menyebut online dan offline, hasil wajib memiliki dua item: #37 dan #38. Satu sumber boleh menghasilkan lebih dari satu item. Jangan membuang item kedua hanya karena source_id-nya sama.\n"
        "\n"
        "Kembalikan HANYA JSON object valid dengan format:\n"
        "\n"
        "{\n"
        "  \"items\": [\n"
        "    {\n"
        "      \"number\": 37,\n"
        "      \"remark\": \"Pearl habis\"\n"
        "    }\n"
        "  ],\n"
        "  \"unmatched\": [\n"
        "    \"Temuan yang tidak cocok ke checklist\"\n"
        "  ]\n"
        "}\n"
    )


def _normalise_unmatched(unmatched) -> list[str]:
    """Mengubah berbagai bentuk unmatched menjadi list string."""
    if unmatched is None:
        return []

    if isinstance(unmatched, str):
        text = unmatched.strip()
        return [text] if text else []

    if not isinstance(unmatched, list):
        unmatched = [unmatched]

    result = []

    for item in unmatched:
        if item is None:
            continue

        if isinstance(item, str):
            text = item.strip()
            if text:
                result.append(text)
            continue

        if isinstance(item, dict):
            source_ids = item.get("source_ids", [])
            text = (
                item.get("text")
                or item.get("finding")
                or item.get("remark")
                or item.get("description")
                or ""
            )

            text = str(text).strip()

            if isinstance(source_ids, list) and source_ids:
                ids = ", ".join(str(value) for value in source_ids)

                if text:
                    result.append(f"[{ids}] {text}")
                else:
                    result.append(
                        f"[{ids}] Temuan tidak masuk checklist"
                    )

            elif text:
                result.append(text)

            else:
                result.append(str(item))

            continue

        text = str(item).strip()

        if text:
            result.append(text)

    return result


def _extract_items(raw_text: str) -> tuple[list, list[str]]:
    """Membaca respons AI dalam format JSON."""
    if not raw_text:
        raise ValueError("Respons AI kosong.")

    text = raw_text.strip()

    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    try:
        data = json.loads(text)

    except json.JSONDecodeError:
        object_match = re.search(
            r"\{.*\}",
            text,
            flags=re.DOTALL,
        )

        array_match = re.search(
            r"$$.*$$",
            text,
            flags=re.DOTALL,
        )

        match = object_match or array_match

        if not match:
            raise ValueError(
                "Respons AI bukan JSON valid:\n"
                f"{raw_text[:500]}"
            )

        try:
            data = json.loads(match.group(0))

        except json.JSONDecodeError as error:
            raise ValueError(
                "JSON dari AI tidak dapat dibaca:\n"
                f"{raw_text[:500]}"
            ) from error

    if isinstance(data, dict):
        items = data.get("items", [])
        unmatched = data.get("unmatched", [])

        if not isinstance(items, list):
            items = []

        return items, _normalise_unmatched(unmatched)

    if isinstance(data, list):
        return data, []

    return [], [
        "Respons AI tidak memiliki format items/unmatched yang valid."
    ]


def _merge_remarks(existing: str, incoming: str) -> str:
    """Menggabungkan remarks untuk nomor checklist yang sama."""
    existing = (existing or "").strip()
    incoming = (incoming or "").strip()

    if not existing:
        return incoming

    if not incoming:
        return existing

    if incoming in existing or existing in incoming:
        return existing

    return f"{existing}; {incoming}"


def _ensure_online_offline_safety(
    merged: dict[int, str],
    findings_text: str,
) -> dict[int, str]:
    """
    Safety net aturan #37/#38 (penyangga validasi di sisi Python).

    Jika temuan secara eksplisit menyebut KEDUA kanal (online DAN offline),
    hasil wajib memiliki #37 (outlet/offline) dan #38 (menu online).
    Model kadang hanya mengembalikan salah satunya meski prompt sudah
    diperkuat — fungsi ini menjamin keduanya muncul.
    """
    lower = findings_text.lower()

    online_tokens = (
        "online", "gojek", "grab", "ojek", "oje", "ojk",
        "aplikasi", "delivery",
    )
    offline_tokens = (
        "offline", "outlet", "toko", "store", "gerai",
    )

    mentions_online = any(token in lower for token in online_tokens)
    mentions_offline = any(token in lower for token in offline_tokens)

    if not (mentions_online and mentions_offline):
        return merged

    if 37 in merged and 38 in merged:
        return merged

    base = merged.get(37) or merged.get(38) or ""

    if not base:
        base = next(
            (
                line.strip()
                for line in findings_text.splitlines()
                if any(
                    token in line.lower()
                    for token in ("sold out", "habis", "stok kosong", "kosong")
                )
            ),
            "",
        )

    if not base:
        base = "Produk/series"

    base = re.sub(
        r"\b(?:via online maupun offline|online maupun offline|"
        r"online dan offline|online serta offline|"
        r"baik online maupun offline)\b",
        "",
        base,
        flags=re.IGNORECASE,
    )
    base = re.sub(r"\s*\(\s*habis\s*\)", "", base, flags=re.IGNORECASE)
    base = re.sub(r"\s{2,}", " ", base).strip(" .;,")

    if not base:
        base = "Produk/series"

    if 37 not in merged:
        merged[37] = f"{base} sold out/habis di outlet/offline."
    if 38 not in merged:
        merged[38] = f"{base} sold out/habis di menu online."

    return merged


def call_llm(
    model_label: str,
    findings_text: str,
    current_models: dict,
) -> dict:
    """
    Memanggil AI dan memastikan item yang gagal diproses
    tidak hilang diam-diam.
    """

    if model_label not in current_models:
        raise ValueError(f"Model tidak dikenal: {model_label}")

    if not findings_text or not findings_text.strip():
        raise ValueError("Temuan belum diisi.")

    config = current_models[model_label]
    prompt = _build_prompt(findings_text)

    provider = config["provider"]
    model = config["model"]

    if provider == "bandelbanget":
        raw = _call_bandelbanget(model, prompt)
    elif provider == "kagiro":
        raw = _call_kagiro(model, prompt)
    elif provider == "gemini":
        raw = _call_gemini(model, prompt)
    elif provider == "byok":
        raw = _call_byok(model, prompt)
    elif provider == "deepseek":
        raw = _call_deepseek(model, prompt)
    elif provider in _PREFIX_TO_GATEWAY:
        raw = _call_generic_gateway(provider, model, prompt)
    else:
        raise ValueError(f"Provider tidak dikenal: {provider}")

    items, unmatched = _extract_items(raw)

    valid_numbers = {
        int(item["number"])
        for item in _flat_item_list()
    }

    cleaned = {}
    rejected = []

    for index, entry in enumerate(items, start=1):
        if not isinstance(entry, dict):
            rejected.append(
                f"Hasil AI #{index} memiliki format tidak valid: {entry}"
            )
            continue

        raw_number = entry.get("number")
        raw_remark = entry.get("remark", "")

        try:
            number = int(raw_number)
        except (TypeError, ValueError):
            rejected.append(
                f"Nomor checklist tidak valid pada hasil AI #{index}: "
                f"{raw_number!r}"
            )
            continue

        remark = (
            ""
            if raw_remark is None
            else str(raw_remark).strip()
        )

        if number not in valid_numbers:
            rejected.append(
                f"Nomor checklist #{number} tidak ditemukan"
                + (f": {remark}" if remark else "")
            )
            continue

        if not remark:
            rejected.append(
                f"Checklist #{number} tidak memiliki remarks."
            )
            continue

        if number in cleaned:
            cleaned[number] = _merge_remarks(cleaned[number], remark)
        else:
            cleaned[number] = remark

    merged = _ensure_online_offline_safety(cleaned, findings_text)

    final_cleaned = [
        {
            "number": number,
            "remark": remark,
        }
        for number, remark in sorted(merged.items())
    ]

    final_unmatched = list(unmatched)
    final_unmatched.extend(rejected)

    unique_unmatched = []
    seen_unmatched = set()

    for text in final_unmatched:
        text = str(text).strip()

        if not text or text in seen_unmatched:
            continue

        seen_unmatched.add(text)
        unique_unmatched.append(text)

    return {
        "matched": final_cleaned,
        "unmatched": unique_unmatched,
    }


def _call_gemini(model: str, prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY belum diatur di secrets."
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    response = requests.post(
        url,
        params={"key": api_key},
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        },
        timeout=240,
    )

    if response.status_code == 429:
        raise RuntimeError(
            "Gemini kena rate limit (429). Coba model lain."
        )

    response.raise_for_status()
    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(
            "Format respons Gemini tidak dikenali: "
            f"{str(data)[:300]}"
        )


def _call_byok(model: str, prompt: str) -> str:
    cfg = get_byok_config()
    base_url = cfg.get("base_url", "").rstrip("/")
    api_key = cfg.get("api_key", "")

    if not base_url or not api_key:
        raise RuntimeError("BYOK belum diisi (base_url & api_key kosong).")

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if resp.status_code == 429:
        raise RuntimeError("BYOK kena rate limit (429). Coba model lain.")
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Format respons BYOK tidak dikenali: {str(data)[:300]}")


def _call_deepseek(model: str, prompt: str) -> str:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY belum diatur di secrets.")

    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if resp.status_code == 429:
        raise RuntimeError("DeepSeek kena rate limit (429). Coba model lain.")
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Format respons DeepSeek tidak dikenali: {str(data)[:300]}")


def _call_bandelbanget(model: str, prompt: str) -> str:
    api_key = st.secrets.get("BANDEL_API_KEY")
    if not api_key:
        raise RuntimeError("BANDEL_API_KEY belum diatur di secrets.")

    resp = requests.post(
        "https://bandelbanget.xyz/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if resp.status_code == 429:
        raise RuntimeError("Kuota token Bandelbanget habis atau terkena rate limit (429).")
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Format respons Bandelbanget tidak dikenali: {str(data)[:300]}")


def _call_kagiro(model: str, prompt: str) -> str:
    api_key = st.secrets.get("KAGIRO_API_KEY")
    if not api_key:
        raise RuntimeError("KAGIRO_API_KEY belum diatur di secrets.")

    resp = requests.post(
        "https://api.kagiro.net/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if resp.status_code == 429:
        raise RuntimeError("Kuota token Kagiro habis atau terkena rate limit (429).")
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Format respons Kagiro tidak dikenali: {str(data)[:300]}")


# Pemetaan kunci provider pendek (yang disimpan di current_models["provider"])
# ke entri _GENERIC_GATEWAYS. Dipakai oleh _call_generic_gateway().
_PREFIX_TO_GATEWAY = {
    prefix.lower(): provider_name
    for provider_name, (prefix, _default_url) in _GENERIC_GATEWAYS.items()
}
# Alias kunci pendek / varian penamaan agar tetap dikenali (termasuk nilai
# lama yang pernah tersimpan di cache / .pyc).
_PREFIX_TO_GATEWAY["9router"] = "9router Proxy"
_PREFIX_TO_GATEWAY["router9"] = "9router Proxy"
_PREFIX_TO_GATEWAY["cart"] = "Cartridge Proxy"
_PREFIX_TO_GATEWAY["gate"] = "GateAI Proxy"


def _call_generic_gateway(provider_key: str, model: str, prompt: str) -> str:
    """Panggil gateway OpenAI-compatible generik yang didaftarkan di
    _GENERIC_GATEWAYS (Cartridge / Kenari / GateAI / Juan / SeekAI / 9router).

    Base URL diambil dari <PREFIX>_BASE_URL di secrets bila ada, kalau tidak
    pakai default gateway. Polanya sama dengan Kagiro/Bandelbanget.
    """
    provider_name = _PREFIX_TO_GATEWAY.get(provider_key.lower())
    if provider_name is None:
        raise ValueError(f"Provider tidak dikenal: {provider_key}")

    prefix, default_url = _GENERIC_GATEWAYS[provider_name]
    base_url = _resolve_base_url(prefix, default_url)
    if not base_url:
        raise RuntimeError(
            f"Base URL untuk {provider_name} belum diatur "
            f"(isi {prefix}_BASE_URL di secrets)."
        )

    api_key = st.secrets.get(f"{prefix}_API_KEY", "")
    if not api_key:
        raise RuntimeError(f"{prefix}_API_KEY belum diatur di secrets.")

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if resp.status_code == 429:
        raise RuntimeError(
            f"Kuota token {provider_name} habis atau terkena rate limit (429)."
        )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(
            f"Format respons {provider_name} tidak dikenali: {str(data)[:300]}"
        )
