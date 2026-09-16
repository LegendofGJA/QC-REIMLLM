"""
pdf_core.py — Gabungkan gambar asli menjadi PDF TANPA kompresi/downsizing.

Pakai img2pdf yang menyisipkan byte gambar apa adanya (lossless embedding).
Untuk JPEG asli, byte dipertahankan (rotation=Rotation.ifvalid menangani EXIF
orientation tidak standar). Untuk PNG (mis. screenshot Flazz/BCA), img2pdf
kadang melempar "invalid png" bila chunk/header-nya tidak sempurna — maka PNG
di-normalisasi lewat Pillow (re-encode PNG lossless) dulu sebelum digabung.
Resolusi gambar TIDAK dikecilkan di sini.
"""

import io

import img2pdf
from PIL import Image, ImageOps


def _normalize_png(image_bytes: bytes) -> bytes:
    """Re-encode PNG lossless lewat Pillow agar selalu valid bagi img2pdf.

    Jika PNG bermasalah/truncated hingga tidak bisa dibuka Pillow, kembalikan
    byte asli sebagai upaya terakhir."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception:
        return image_bytes

    img = ImageOps.exif_transpose(img)

    # Flatten alpha ke latar putih agar konsisten (receipt/screenshot).
    if img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    ):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=False)
    return out.getvalue()


def _to_io(image_bytes: bytes) -> io.BytesIO:
    return io.BytesIO(image_bytes)


def merge_images_to_pdf(image_bytes_list: list) -> bytes:
    """Return bytes PDF dari list bytes gambar (JPEG/PNG), tanpa kompresi."""
    if not image_bytes_list:
        return b""

    normalized = []
    for b in image_bytes_list:
        # Deteksi format via header untuk memutuskan perlu normalisasi.
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            normalized.append(_normalize_png(b))
        else:
            normalized.append(b)

    streams = [_to_io(b) for b in normalized]
    kwargs = {"rotation": img2pdf.Rotation.ifvalid}
    try:
        return img2pdf.convert(streams, **kwargs)
    except img2pdf.ExifOrientationError:
        # Fallback terakhir: paksa orientasi default tanpa membaca EXIF rotation.
        return img2pdf.convert(streams)
    except Exception:
        # Jika tetap gagal (format tak dikenal), coba sekali tanpa opsi rotation.
        return img2pdf.convert(streams)
