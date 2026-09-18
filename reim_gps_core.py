"""
gps_core.py — Baca metadata GPS/EXIF dari foto struk + reverse geocode.

Dipisah supaya mudah dipertahankan (lokasi foto tetap terbaca dari EXIF),
tanpa mencampur logika OCR.
"""

import io
import time

import requests
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS


def _to_decimal(value):
    """Konversi tuple rasional EXIF (deg, min, sec) -> derajat desimal."""
    if value is None:
        return None
    try:
        d, m, s = value
        return float(d) + float(m) / 60.0 + float(s) / 3600.0
    except (TypeError, ValueError):
        return None


def read_gps(file_bytes: bytes) -> dict:
    """Kembalikan {lat, lon, timestamp, source} atau {} bila tidak ada."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        exif = img._getexif() or {}
    except Exception:
        return {}

    gps = {}
    for tag, val in exif.items():
        name = TAGS.get(tag, tag)
        if name == "GPSInfo":
            gps = val
            break
    if not gps:
        return {}

    def _coord(key):
        raw = gps.get(key)
        dec = _to_decimal(raw)
        return dec

    lat = _coord(2)
    lon = _coord(4)
    if lat is None or lon is None:
        return {}

    lat_ref = gps.get(1, "N")
    lon_ref = gps.get(3, "E")
    if str(lat_ref).strip().upper() == "S":
        lat = -lat
    if str(lon_ref).strip().upper() == "W":
        lon = -lon

    timestamp = None
    for tag, val in exif.items():
        name = TAGS.get(tag, tag)
        if name in ("DateTimeOriginal", "DateTime") and val:
            timestamp = str(val)
            break

    return {"lat": lat, "lon": lon, "timestamp": timestamp, "source": "exif"}


# ─────────────────────────────────────────────────────────────────────────
# Reverse geocode: koordinat EXIF -> nama tempat parkir
# ─────────────────────────────────────────────────────────────────────────

_LOCATION_CACHE = {}


def _location_for_coords(lat: float, lon: float) -> str:
    """Cari nama tempat dari koordinat via Nominatim (tanpa API key).
    Hasil di-cache per proses supaya tidak memanggil berulang kali.
    Return '' bila gagal / offline."""
    key = (round(lat, 5), round(lon, 5))
    if key in _LOCATION_CACHE:
        return _LOCATION_CACHE[key]

    result = ""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
            "accept-language": "id",
        }
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": "reimburse-ocr/1.0"},
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            addr = data.get("address") or {}
            name = (
                data.get("name")
                or addr.get("amenity")
                or addr.get("shop")
                or addr.get("building")
                or addr.get("parking")
                or addr.get("mall")
                or addr.get("commercial")
                or addr.get("retail")
            )
            if name:
                result = str(name)
            elif addr.get("road"):
                result = str(addr.get("road"))
            elif addr.get("suburb"):
                result = str(addr.get("suburb"))
            elif addr.get("village"):
                result = str(addr.get("village"))
        time.sleep(1)  # sopan ke Nominatim (batas 1 req/detik)
    except Exception:
        result = ""

    _LOCATION_CACHE[key] = result
    return result


def gps_location_name(file_bytes: bytes) -> str:
    """Return nama lokasi parkir dari GPS EXIF ('' bila tidak ada/kosong)."""
    info = read_gps(file_bytes)
    if not info:
        return ""
    try:
        return _location_for_coords(float(info["lat"]), float(info["lon"]))
    except (TypeError, ValueError):
        return ""


# ─────────────────────────────────────────────────────────────────────────
# Reverse geocode ringkas: koordinat EXIF -> "Nama Jalan, Kota"
# ─────────────────────────────────────────────────────────────────────────

_ADDRESS_CACHE = {}


def _short_address_for_coords(lat: float, lon: float) -> str:
    """Ubah koordinat jadi 'Nama Jalan, Kota' (tanpa koordinat mentah).

    Hanya memakai komponen alamat: road / pedestrian / suburb + city /
    town / municipality / county. Return '' bila gagal / offline.
    Hasil di-cache per proses supaya tidak memanggil berulang kali.
    """
    key = (round(lat, 5), round(lon, 5))
    if key in _ADDRESS_CACHE:
        return _ADDRESS_CACHE[key]

    result = ""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
            "accept-language": "id",
        }
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": "reimburse-ocr/1.0"},
            timeout=8,
        )
        if r.status_code == 200:
            addr = (r.json().get("address") or {})

            road = (
                addr.get("road")
                or addr.get("pedestrian")
                or addr.get("footway")
                or addr.get("path")
                or addr.get("residential")
                or addr.get("neighbourhood")
            )
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("municipality")
                or addr.get("county")
                or addr.get("city_district")
                or addr.get("village")
                or addr.get("suburb")
            )

            parts = [p for p in (road, city) if p]
            # buang duplikat kalau road == city
            if len(parts) == 2 and parts[0].strip().lower() == parts[1].strip().lower():
                parts = [parts[0]]
            result = ", ".join(str(p).strip() for p in parts)
        time.sleep(1)  # sopan ke Nominatim (batas 1 req/detik)
    except Exception:
        result = ""

    _ADDRESS_CACHE[key] = result
    return result


def gps_short_address(file_bytes: bytes) -> str:
    """Return 'Nama Jalan, Kota' dari GPS EXIF ('' bila tak ada/kosong)."""
    info = read_gps(file_bytes)
    if not info:
        return ""
    try:
        return _short_address_for_coords(float(info["lat"]), float(info["lon"]))
    except (TypeError, ValueError):
        return ""
