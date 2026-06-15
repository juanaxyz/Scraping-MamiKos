def _to_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_get_nested(data, *keys, default=None):
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _normalize_facility_names(items):
    if not items:
        return []
    out = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name")
            if name:
                out.append(name)
        elif item:
            out.append(item)
    return out


def _extract_poi_label(tags, category):
    if not isinstance(tags, dict):
        return category
    for k in ("name", "brand", "operator", "ref", "amenity", "shop", "office"):
        v = tags.get(k)
        if v:
            return v
    for k, v in tags.items():
        if v:
            return f"{k}={v}"
    return category


def ambil_kolom_analisis_dari_json(obj_kos: dict) -> dict:
    if not isinstance(obj_kos, dict):
        return {}

    ptf = obj_kos.get("price_title_formats") or {}
    price_daily = _safe_get_nested(ptf, "price_daily", "price") or obj_kos.get(
        "price_daily"
    )
    price_weekly = _safe_get_nested(ptf, "price_weekly", "price") or obj_kos.get(
        "price_weekly"
    )
    price_monthly = _safe_get_nested(ptf, "price_monthly", "price") or obj_kos.get(
        "price_monthly"
    )
    price_yearly = _safe_get_nested(ptf, "price_yearly", "price") or obj_kos.get(
        "price_yearly"
    )
    top_fac = _normalize_facility_names(obj_kos.get("top_facilities") or [])

    return {
        "area_subdistrict": obj_kos.get("area_subdistrict"),
        "area_city": obj_kos.get("area_city"),
        "latitude": obj_kos.get("latitude"),
        "longitude": obj_kos.get("longitude"),
        "price_daily": _to_float(price_daily),
        "price_weekly": _to_float(price_weekly),
        "price_monthly": _to_float(price_monthly),
        "price_yearly": _to_float(price_yearly),
        "price_tag": obj_kos.get("price_tag"),
        "dp_percentage": obj_kos.get("dp_percentage"),
        "fac_room": obj_kos.get("fac_room") or [],
        "fac_share": obj_kos.get("fac_share") or [],
        "fac_bath": obj_kos.get("fac_bath") or [],
        "top_facilities": top_fac,
        "view_count": obj_kos.get("view_count"),
        "love_count": obj_kos.get("love_count"),
        "review_count": obj_kos.get("review_count"),
        "rating": obj_kos.get("rating"),
        "available_room": obj_kos.get("available_room"),
        "size": obj_kos.get("size"),
        "gender": obj_kos.get("gender"),
        "booking_type": obj_kos.get("booking_type") or [],
        "building_year": obj_kos.get("building_year"),
    }
