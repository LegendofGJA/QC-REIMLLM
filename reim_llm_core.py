"""
llm_core.py — Koneksi provider AI vision (Kagiro / Bandel / 9router / custom).

Menyediakan:
  - `PROVIDERS`       : konfigurasi provider dari st.secrets (bukan hardcoded).
  - `fetch_models`    : ambil daftar model dari endpoint /models (fallback default).
  - `ping_model`      : tes API "hidup" dengan KIRIM completion kecil BENERAN,
                        bukan cuma HTTP 200 pada /models — sehingga model yang
                        terdaftar tapi tidak merespons akan terdeteksi.
  - `prepare_image`   : resize + re-encode JPEG agar payload aman (menghindari
                        HTTP 413 Payload Too Large dari server).
  - `call_vision`     : panggil chat/completions dengan timeout panjang + retry
                        + backoff (menghindari read timeout).
"""

import base64
import io
import json
import os
import re
import time

import requests
import streamlit as st
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────
# Konfigurasi provider (secrets, tidak pernah hardcoded)
# ─────────────────────────────────────────────────────────────────────────


def _get_secret(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


# Setiap provider dibaca dari secrets. `api_key` diambil dari <PREFIX>_API_KEY
# (atau <PREFIX>_KEY); `base_url` dari <PREFIX>_BASE_URL. Provider tanpa API
# key otomatis di-skip, jadi kamu bebas menambah/menghapus provider.
_PROVIDER_DEFS = [
    ("Kagiro", "KAGIRO", "https://api.kagiro.net/v1"),
    ("Bandel", "BANDEL", "https://bandelbanget.xyz/v1"),
    # URL endpoint 9router diisi lewat secrets (ROUTER9_BASE_URL) supaya alamat
    # tunnel internal tidak ikut ter-commit ke repo publik.
    ("9router", "ROUTER9", ""),
    ("Cartridge", "CARTRIDGE", "https://router.cartridge.my.id/v1"),
    ("Kenari", "KENARI", "https://kenari.id/v1/"),
    ("GateAI", "GATEAI", "https://gateai.id/v1/"),
    ("Juan", "JUAN", "https://router.juan.web.id/v1"),
    ("SeekAI", "SEEKAI", "https://seekai.cc/v1/"),
]

PROVIDERS = {}
for _name, _prefix, _default_url in _PROVIDER_DEFS:
    _key = _get_secret(f"{_prefix}_API_KEY") or _get_secret(f"{_prefix}_KEY")
    if _key:
        PROVIDERS[_name] = {
            "base_url": _get_secret(f"{_prefix}_BASE_URL", _default_url),
            "api_key": _key,
        }
del _name, _prefix, _default_url, _key

# Fallback HANYA dipakai kalau endpoint /models tidak tersedia / kosong.
# Daftar ini sengaja generik (model vision lintas-vendor) dan TIDAK memuat id
# spesifik gateway (mis. "cbai/...") supaya id milik 9router tidak bocor ke
# provider lain saat /models gagal.
FALLBACK_MODELS = [
    "qwen-vl-max",
    "qwen2.5-vl-72b-instruct",
    "qwen-vl-max-latest",
    "gpt-4o",
    "gpt-4o-mini",
    "gemini-2.0-flash",
]

# Fallback tambahan KHUSUS per provider (dipakai kalau /models gagal). Dipakai
# mis. oleh 9router yang punya id bervendor-prefix seperti "cbai/deepseek-v4.1-flash".
_PROVIDER_EXTRA_FALLBACK = {
    "9router": ["cbai/deepseek-v4.1-flash", "deepseek-v4.1-flash"],
}


def _auth_headers(cfg: dict) -> dict:
    return {"Authorization": f"Bearer {cfg['api_key']}"}


# ─────────────────────────────────────────────────────────────────────────
# Daftar model
# ─────────────────────────────────────────────────────────────────────────


# Catatan desain: TIDAK ada daftar "hint vision" yang dipakai untuk MEMPERTAHANKAN
# model. Filter hanya bersifat membuang (lihat _NON_VISION_HINTS). Ini supaya
# daftar model yang tampil benar-benar model asli dari server, bukan hasil tebakan
# dari pola nama — akar masalah "scan tidak menampilkan model sebenarnya".


def fetch_models(provider_name: str) -> list:
    """Ambil daftar model id ASLI dari /models (tanpa filter).

    Return (ids, from_server). `from_server=False` menandakan endpoint gagal /
    kosong sehingga `ids` berisi fallback default.
    """
    cfg = PROVIDERS[provider_name]
    url = f"{cfg['base_url']}/models"
    try:
        r = requests.get(url, headers=_auth_headers(cfg), timeout=12)
        if r.status_code == 200:
            data = r.json()
            models = data.get("data", data)
            ids = []
            for m in (models if isinstance(models, list) else []):
                if isinstance(m, dict):
                    mid = m.get("id")
                    if isinstance(mid, str):
                        ids.append(mid)
                elif isinstance(m, str):
                    ids.append(m)
            if ids:
                return ids, True
    except Exception:
        pass
    fallback = list(FALLBACK_MODELS) + list(_PROVIDER_EXTRA_FALLBACK.get(provider_name, []))
    return fallback, False


def _model_declares_non_vision(model_obj) -> bool:
    """True bila metadata model secara EXPLISIT menyatakan non-vision.

    Beberapa gateway mengirim field `modality`/`input_modalities`/`vision`.
    Kalau endpoint memberi info ini, kita pakai sebagai sinyal utama — bukan
    menebak dari nama. Endpoint yang tidak memberi info -> None (tidak terpakai).
    """
    if not isinstance(model_obj, dict):
        return False
    # `vision: false` eksplisit
    for k in ("vision", "supports_vision", "multimodal"):
        if k in model_obj and model_obj[k] is False:
            return True
    # input_modalities / modality tanpa "image"
    for k in ("input_modalities", "modalities", "modality"):
        v = model_obj.get(k)
        if v is None:
            continue
        vals = v if isinstance(v, (list, tuple)) else [v]
        s = " ".join(str(x).lower() for x in vals)
        if s and "image" not in s and "vision" not in s:
            return True
    return False


def fetch_models_raw(provider_name: str) -> dict:
    """Ambil daftar model + metadata mentah dari /models.

    Return {"ids": [...], "non_vision": set(ids), "from_server": bool}.
    `non_vision` berisi id yang ENDPOINT-nya bilang non-vision (kalau info ada).
    """
    cfg = PROVIDERS[provider_name]
    url = f"{cfg['base_url']}/models"
    ids, non_vision, from_server = [], set(), False
    try:
        r = requests.get(url, headers=_auth_headers(cfg), timeout=12)
        if r.status_code == 200:
            data = r.json()
            models = data.get("data", data)
            for m in (models if isinstance(models, list) else []):
                if isinstance(m, dict):
                    mid = m.get("id")
                    if isinstance(mid, str):
                        ids.append(mid)
                        if _model_declares_non_vision(m):
                            non_vision.add(mid)
                elif isinstance(m, str):
                    ids.append(m)
            if ids:
                from_server = True
    except Exception:
        pass
    if not from_server:
        ids = list(FALLBACK_MODELS) + list(_PROVIDER_EXTRA_FALLBACK.get(provider_name, []))
    return {"ids": ids, "non_vision": non_vision, "from_server": from_server}


def fetch_vision_models(provider_name: str) -> list:
    """Daftar model VISION dari /models provider ini.

    Prinsip: TAMPILKAN MODEL ASLI DARI SERVER. Penyaringan vision hanya membuang
    model yang endpoint-nya (atau polanya) secara jelas bukan vision — sisanya
    dibiarkan muncul. Kalau hasil filter kosong, kembalikan daftar aslinya
    supaya dropdown tidak pernah kosong / tidak kehilangan model nyata.
    """
    info = fetch_models_raw(provider_name)
    ids = info["ids"]
    non_vision = info["non_vision"]  # dari metadata endpoint (paling akurat)

    vision = []
    for mid in ids:
        if mid in non_vision:
            continue
        if _is_definitely_non_vision(mid):
            continue
        vision.append(mid)

    if vision:
        return vision
    # Filter terlalu agresif -> jangan sembunyikan model nyata.
    return ids


def fetch_all_models(provider_name: str) -> list:
    """Seluruh model asli dari server (tanpa filter vision).

    Dipakai untuk dropdown "Mode: semua model" di halaman Reimburse, supaya
    model yang tidak terdeteksi oleh pola nama tetap bisa dipilih manual.
    """
    return fetch_models_raw(provider_name)["ids"]


# Pola id yang PASTI bukan vision (dipakai untuk membuang, bukan untuk
# mempertahankan). Sengaja konservatif: kalau ragu, model tetap ditampilkan.
_NON_VISION_HINTS = (
    "embedding",
    "embed",
    "rerank",
    "reranker",
    "tts",
    "whisper",
    "audio",
    "speech",
    "moderation",
    "dall-e",
    "image-generation",
    "stable-diffusion",
    "flux",
    "sdxl",
    "bge-",
    "text-embedding",
)


def _is_definitely_non_vision(model_id: str) -> bool:
    m = model_id.lower()
    return any(h in m for h in _NON_VISION_HINTS)


# ─────────────────────────────────────────────────────────────────────────
# Ping API "hidup" — kirim completion asli, bukan cuma HTTP 200
# ─────────────────────────────────────────────────────────────────────────


def ping_model(provider_name: str, model: str) -> tuple:
    """Kirim chat kecil "hi" ke model dan laporkan hasilnya.

    Return (ok: bool, pesan: str, ms: int|None).
    """
    cfg = PROVIDERS[provider_name]
    url = f"{cfg['base_url']}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 20,
        "temperature": 0,
    }
    headers = {**_auth_headers(cfg), "Content-Type": "application/json"}
    start = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        ms = int((time.time() - start) * 1000)
        if r.status_code == 200:
            data = r.json()
            content = ""
            try:
                msg = data["choices"][0]["message"]
                content = msg.get("content", "")
                # Sebagian gateway mengembalikan content sebagai list of parts.
                if isinstance(content, list):
                    content = " ".join(
                        str(p.get("text", "")) if isinstance(p, dict) else str(p)
                        for p in content
                    )
            except (KeyError, IndexError, TypeError):
                content = ""
            reply = (content or "").strip()
            if not reply:
                return False, f"⚠️ HTTP 200 tapi balasan kosong ({ms} ms)", ms
            return True, f"✅ Model merespons: “{reply[:60]}” ({ms} ms)", ms
        else:
            return False, f"❌ Status {r.status_code}: {r.text[:120]}", ms
    except Exception as e:
        return False, f"❌ Gagal terhubung ({e})", None


def check_all_providers() -> dict:
    """Scan semua provider: daftar model (tanpa ping per model).

    Return {provider_name: {"models": [id vision...]}}
    """
    out = {}
    for name in PROVIDERS:
        out[name] = {"models": fetch_vision_models(name)}
    return out


# ─────────────────────────────────────────────────────────────────────────
# Siapkan gambar (hindari 413 + byte kecil)
# ─────────────────────────────────────────────────────────────────────────


def prepare_image(file_bytes: bytes, max_side: int = 1600, quality: int = 85) -> bytes:
    """Resize gambar ke max_side dan re-encode jadi JPEG sehingga payload
    base64-nya tetap kecil (teks struk tetap terbaca). Gambar asli TIDAK
    diubah (dipakai untuk PDF gabungan)."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")
    except Exception:
        return file_bytes
    w, h = img.size
    longest = max(w, h)
    if longest > max_side:
        ratio = max_side / float(longest)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────
# Panggil vision API
# ─────────────────────────────────────────────────────────────────────────


def call_vision(
    provider_name: str,
    model: str,
    image_bytes: bytes,
    prompt: str,
    timeout: int = 120,
    retries: int = 2,
) -> dict:
    """Kirim satu gambar + prompt ke model vision. Return objek JSON (dict/list).

    - image_bytes di-resize dulu (prepare_image) untuk hindari 413.
    - timeout panjang (default 120 dtk) + retry dengan backoff utk read timeout.
    """
    cfg = PROVIDERS[provider_name]
    url = f"{cfg['base_url']}/chat/completions"
    headers = {**_auth_headers(cfg), "Content-Type": "application/json"}

    prepared = prepare_image(image_bytes)
    b64 = base64.b64encode(prepared).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
        "temperature": 0.1,
    }

    last_err = None
    last_content = ""
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            r.raise_for_status()
            try:
                raw_content = r.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise ValueError(
                    f"Format respons tidak dikenali dari {provider_name}: "
                    f"{r.text[:200]}"
                )
            if isinstance(raw_content, list):
                raw_content = " ".join(
                    str(p.get("text", "")) if isinstance(p, dict) else str(p)
                    for p in raw_content
                )
            content = re.sub(r"```(?:json)?|```", "", str(raw_content or "")).strip()
            last_content = content
            if not content:
                raise ValueError("Respons model kosong (empty response).")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Coba ekstrak objek/array JSON pertama dari teks bebas.
                start = min(
                    [i for i in (content.find("{"), content.find("[")) if i != -1],
                    default=-1,
                )
                if start != -1:
                    return json.loads(content[start:])
                raise
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))  # backoff: 2s, 4s
    if isinstance(last_err, json.JSONDecodeError):
        snippet = (last_content or "")[:200]
        raise ValueError(
            f"Gagal parse JSON dari model {model}. "
            f"Raw output: '{snippet}' Error: {last_err}"
        )
    raise last_err if last_err else RuntimeError("call_vision gagal")
