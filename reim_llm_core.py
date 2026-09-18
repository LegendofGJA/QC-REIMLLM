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

# Fallback kalau endpoint /models tidak tersedia / kosong.
FALLBACK_MODELS = [
    "deepseek-v4.1-flash",
    "cbai/deepseek-v4.1-flash",
    "qwen-vl-max",
    "qwen2.5-vl-72b-instruct",
    "qwen-vl-max-latest",
    "gpt-4o",
    "gpt-4o-mini",
]


def _auth_headers(cfg: dict) -> dict:
    return {"Authorization": f"Bearer {cfg['api_key']}"}


# ─────────────────────────────────────────────────────────────────────────
# Daftar model
# ─────────────────────────────────────────────────────────────────────────


# Pola id yang lazim untuk model VISION (bisa menerima input gambar).
# Jika endpoint /models tidak memberi flag "vision"/"image", kita filter
# berdasarkan nama id supaya dropdown hanya menampilkan model vision.
_VISION_HINTS = (
    "vl",
    "vision",
    # DeepSeek V4.1 Flash mendukung input gambar (vision) di gateway yang
    # menyediakannya, jadi ikut ditampilkan di dropdown OCR — termasuk varian
    # bervendor-prefix seperti "cbai/deepseek-v4.1-flash".
    "deepseek-v4.1-flash",
    "deepseek-v4.1",
    # Catatan: TIDAK memakai hint generik "flash"/"deepseek", karena banyak
    # model non-vision (mis. cbai/deepseek-v4-flash) ikut lolos padahal
    # tidak bisa OCR gambar. Model vision di bawah ini dipilih lewat pola
    # id yang spesifik.
    "gpt-4o",  # gpt-4o sebenarnya multimodal, pertahankan sebagai vision hint
    "gpt-4.1",
    "gemini",
    "claude",
    "minimax-vl",
    "internvl",
    "glm-4v",
    "glm-4.5v",
    "qwen-vl",
    "qwen2.5-vl",
    "kimi-k",
    "kimi-latest",
)


def _is_vision(model_id: str) -> bool:
    m = model_id.lower()
    return any(h in m for h in _VISION_HINTS)


def fetch_models(provider_name: str) -> list:
    """Ambil daftar model id dari /models. Gagal -> fallback default."""
    cfg = PROVIDERS[provider_name]
    url = f"{cfg['base_url']}/models"
    try:
        r = requests.get(url, headers=_auth_headers(cfg), timeout=12)
        if r.status_code == 200:
            data = r.json()
            models = data.get("data", data)
            ids = [
                (m.get("id") if isinstance(m, dict) else m)
                for m in (models if isinstance(models, list) else [])
            ]
            ids = [i for i in ids if isinstance(i, str)]
            if ids:
                return ids
    except Exception:
        pass
    return list(FALLBACK_MODELS)


def fetch_vision_models(provider_name: str) -> list:
    """Daftar model VISION saja (tanpa ping) dari /models. Gagal -> fallback
    default yang sudah difilter vision; kalau kosong sama sekali, kembalikan
    fallback mentah supaya dropdown tidak kosong."""
    all_ids = fetch_models(provider_name)
    vision = [m for m in all_ids if _is_vision(m)]
    if vision:
        return vision
    # Tidak ada yang terdeteksi vision -> fallback ke daftar default (vision).
    fallback_vision = [m for m in FALLBACK_MODELS if _is_vision(m)]
    return fallback_vision or all_ids


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
