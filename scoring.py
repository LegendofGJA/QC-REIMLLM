"""
Logika perhitungan skor, direplikasi persis dari rumus di file Excel
template terbaru (sheet DETAIL AUDIT), supaya hasil di web SAMA dengan
hasil kalau dihitung manual di Excel.

Model penilaian terbaru (rekap baris 169-184 di Excel):
  - Tiap detail kategori punya BASIC (C#) dan ACTUAL (D#) subtotal.
  - Kelompok bobot:
      SERVICE    (bobot 30) = Personal Grooming, Attitude, Sequence of
                              Service, Environment
      FOOD SAFETY(bobot 40) = Food Safety, Product Handling, Pest Control
      CLEANLINESS(bobot 30) = Display, Bar Area, Equipment, Seating Area
  - BOBOT DETAIL (E#) = bobot_kelompok * ACTUAL_detail / SUM(BASIC_detail
    semua detail dalam kelompok yang sama).
  - Subtotal kelompok = SUM(BOBOT DETAIL).
  - TOTAL (E184) = Subtotal SERVICE + FOOD SAFETY + CLEANLINESS.
  - FINAL SCORE (E9) = E184 (langsung rentang 0-100, tanpa dibagi 10).
  - Grade (E2): >=96 A | >=91 B+ | >=86 B | >=81 B- | else C
"""

from __future__ import annotations

GROUP_WEIGHTS = {
    "SERVICE": 30,
    "FOOD SAFETY": 40,
    "CLEANLINESS": 30,
}

# Nama detail per kelompok (key = nama "detail" Excel; value = pemetaan ke
# nama kategori di structure.json, atau ke subkategori CLEANLINESS).
# SERVICE: semuanya kategori utama.
# FOOD SAFETY: semuanya kategori utama.
# CLEANLINESS: subkategori dari kategori utama CLEANLINESS.
SERVICE_DETAILS = [
    ("Personal Grooming", "PERSONAL GROOMING"),
    ("Attitude", "ATTITUDE"),
    ("Sequence of Service", "SQUENCE OF SERVICE"),
    ("Environment", "ENVIRONMENT"),
]

FOOD_SAFETY_DETAILS = [
    ("Food Safety", "FOOD SAFETY"),
    ("Product Handling", "PRODUCT HANDLING"),
    ("Pest Control", "PEST CONTROL"),
]

CLEANLINESS_SUBCATS = [
    "Display",
    "Bar Area",
    "Equipment",
    "Seating Area",
]


def item_actual_score(basic: float, remark: str | None,
                      exclude_from_score: bool = False) -> float:
    """Actual score = 0 jika remarks diisi, selain itu = basic score.

    `exclude_from_score` (sesuai rumus Excel yang melewati baris tertentu)
    membuat item tidak menyumbang sama sekali ke subtotal kategori.
    """
    if exclude_from_score:
        return 0
    if remark and str(remark).strip():
        return 0
    return basic


def _iter_items(cat: dict):
    """Iterasi semua item kategori, tangani struktur dengan/ tanpa subkategori."""
    if "subcategories" in cat:
        for sub in cat["subcategories"]:
            for it in sub["items"]:
                yield it
    else:
        for it in cat.get("items", []):
            yield it


def _category_totals(cat: dict, remarks: dict[str, str]):
    """Basic & actual subtotal satu kategori utama (remap/subcat akumulasi).

    Item bertanda `exclude_from_score` (sesuai rumus Excel yang melewati
    baris tertentu, mis. "Putar musik") tidak menyumbang ke basic maupun
    actual subtotal, tetapi tetap dicantumkan agar tampil di UI.
    """
    basic = 0
    actual = 0
    item_rows = []
    for it in _iter_items(cat):
        r = remarks.get(str(it["number"]), "")
        excluded = it.get("exclude_from_score", False)
        a = item_actual_score(it["basic"], r, excluded)
        if not excluded:
            basic += it["basic"]
            actual += a
        item_rows.append({**it, "remark": r, "actual": a})
    return basic, actual, item_rows


def _subcat_totals(cat: dict, remarks: dict[str, str]):
    """Basic & actual subtotal per subkategori dari sebuah kategori utama."""
    out = []
    if "subcategories" not in cat:
        return out
    for sub in cat["subcategories"]:
        basic = 0
        actual = 0
        item_rows = []
        for it in sub["items"]:
            r = remarks.get(str(it["number"]), "")
            excluded = it.get("exclude_from_score", False)
            a = item_actual_score(it["basic"], r, excluded)
            if not excluded:
                basic += it["basic"]
                actual += a
            item_rows.append({**it, "remark": r, "actual": a})
        out.append({"name": sub["name"], "basic": basic, "actual": actual,
                    "row": sub["row"], "items": item_rows})
    return out


def compute_all(structure: list[dict], remarks: dict[str, str]) -> dict:
    """
    structure: hasil parse structure.json (kategori terbaru).
    remarks: dict {str(item_number): remark_text}
    Mengembalikan dict berisi rincian per kategori, per kelompok bobot,
    total & grade — persis seperti rekap E170-E184 & E2/E9 di Excel.
    """
    # ── kumpulkan kategori utama ──
    cat_map: dict[str, dict] = {}
    cat_totals: dict[str, dict] = {}
    for cat in structure:
        if cat.get("name") == "ETC":
            continue
        cat_map[cat["name"]] = cat
        b, a, item_rows = _category_totals(cat, remarks)
        percent = (a / b * 100) if b else 0.0
        cat_totals[cat["name"]] = {
            "name": cat["name"],
            "basic": b,
            "actual": a,
            "percent": percent,
            "items": item_rows,
        }

    def strip_prefix(name: str) -> str:
        # "C. Equipment" -> "Equipment"
        if name and len(name) >= 2 and name[1] == ".":
            return name.split(".", 1)[-1].strip()
        return name

    # ── kelompok CLEANLINESS dipecah per subkategori ──
    cleanliness_sub = {
        strip_prefix(s["name"]): {"name": s["name"], "basic": s["basic"],
                                  "actual": s["actual"], "items": s["items"]}
        for s in _subcat_totals(cat_map.get("CLEANLINESS", {}), remarks)
    }

    # detail entries per kelompok: (label_tampilan, key_penyimpanan)
    group_details = {
        "SERVICE": [(d[1], d[1]) for d in SERVICE_DETAILS],
        "FOOD SAFETY": [(d[1], d[1]) for d in FOOD_SAFETY_DETAILS],
        "CLEANLINESS": [(d, d) for d in CLEANLINESS_SUBCATS],
    }

    def detail_basic_actual(key: str, group: str):
        if group == "CLEANLINESS":
            target = cleanliness_sub.get(key)
            if target is None:
                return 0, 0
            return target["basic"], target["actual"]
        return cat_totals[key]["basic"], cat_totals[key]["actual"]

    # Basic subtotal per detail (untuk denominator tiap kelompok)
    group_basic_sums = {}
    for group, details in group_details.items():
        group_basic_sums[group] = sum(
            detail_basic_actual(key, group)[0] for _, key in details
        )

    # ── hitung bobot detail & subtotal kelompok ──
    groups = []
    for group, details in group_details.items():
        weight = GROUP_WEIGHTS[group]
        denom = group_basic_sums[group]
        detail_scores = []
        for label, key in details:
            b, a = detail_basic_actual(key, group)
            bobot = (weight * a / denom) if denom else 0.0
            detail_scores.append({"name": label, "basic": b, "actual": a,
                                  "bobot": bobot})
        groups.append({
            "name": group,
            "weight": weight,
            "denom": denom,
            "details": detail_scores,
            "subtotal": sum(x["bobot"] for x in detail_scores),
        })

    final_score = sum(g["subtotal"] for g in groups)  # = E184 = E9

    if final_score >= 96:
        grade = "A"
    elif final_score >= 91:
        grade = "B+"
    elif final_score >= 86:
        grade = "B"
    elif final_score >= 81:
        grade = "B-"
    else:
        grade = "C"

    total_basic = sum(c["basic"] for c in cat_totals.values())
    total_actual = sum(c["actual"] for c in cat_totals.values())

    return {
        "categories": list(cat_totals.values()),
        "groups": groups,
        "total_basic": total_basic,
        "total_actual": total_actual,
        "grand_percent_sum": final_score,
        "final_score": final_score,
        "grade": grade,
    }
