# crossref_provider.py (loop-proof)
import time, requests
from typing import Optional, Callable, Dict, Any, List, Set

ALLOWED_TYPES = {"journal-article", "proceedings-article", "posted-content"}

def _norm_year(msg_item: Dict[str, Any]) -> Optional[int]:
    issued = msg_item.get("issued") or {}
    parts = issued.get("date-parts") or []
    return parts[0][0] if parts and parts[0] else None

def norm_crossref(msg_item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": "crossref",
        "id": f"crossref:{msg_item.get('DOI') or ''}",
        "doi": msg_item.get("DOI"),
        "title": (msg_item.get("title") or [""])[0],
        "year": _norm_year(msg_item),
        "type": msg_item.get("type"),
        "venue": (msg_item.get("container-title") or [""])[0],
        "url": msg_item.get("URL"),
        "is_referenced_by_count": msg_item.get("is-referenced-by-count"),
        "abstract": msg_item.get("abstract"),
        "authors": [
            {"given": a.get("given"), "family": a.get("family"), "orcid": a.get("ORCID")}
            for a in (msg_item.get("author") or [])
        ],
        "link": (msg_item.get("link") or [{}])[0].get("URL"),
        "subject": msg_item.get("subject"),
        "publisher": msg_item.get("publisher"),
    }

def search_crossref(
    query: str,
    on_record: Optional[Callable[[Dict[str, Any]], None]] = None,
    year_min: int = 2018,
    mailto: Optional[str] = None,
    types: Optional[List[str]] = None,
    has_abstract: Optional[bool] = None,
    rows: int = 200,
    sort: Optional[str] = "is-referenced-by-count",
    order: str = "desc",
    polite_delay: float = 1.0,
    client_side_year_filter: bool = True,
    max_pages: int = 500,                  # hard stop
    disable_sort_with_cursor: bool = True, # avoid Crossref cursor instability
    verbose: bool = True,
):
    base = "https://api.crossref.org/works"
    headers = {
        "User-Agent": f"AgriReviewBot/1.0 ({mailto or 'no-email'})",
        "Accept": "application/json",
    }

    filters = [f"from-pub-date:{year_min}-01-01"]
    if types:
        for t in types:
            if t in ALLOWED_TYPES:
                filters.append(f"type:{t}")
    if has_abstract is True:
        filters.append("has-abstract:true")

    params = {
        "query": query,
        "rows": str(rows),
        "cursor": "*",
        "filter": ",".join(filters),
    }
    if mailto:
        params["mailto"] = mailto
    # select: keep a safe subset (Crossref can still reject; we’ll drop if needed)
    params["select"] = ",".join([
        "DOI","title","author","container-title","issued","type","URL",
        "is-referenced-by-count","link","abstract","subject","publisher","license"
    ])
    # Sorting + cursor can cause weird loops; disable server-sort during cursor paging
    if sort and not disable_sort_with_cursor:
        params["sort"] = sort
        params["order"] = order

    def _req(p):
        time.sleep(max(0.0, polite_delay))
        r = requests.get(base, params=p, headers=headers, timeout=30)
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.5)
            r = requests.get(base, params=p, headers=headers, timeout=30)
        return r

    out, seen_cursors, seen_ids = [], set(), set()
    pages = 0
    current_cursor = params["cursor"]

    while True:
        if current_cursor in seen_cursors:
            if verbose: print("[Crossref] Repeated cursor detected; breaking:", current_cursor[:32], "…")
            break
        seen_cursors.add(current_cursor)

        if verbose:
            print("Crossref request:", requests.Request('GET', base, params=params).prepare().url)

        resp = _req(dict(params))
        if resp.status_code == 400:
            # Heal common 400s (mostly select issues). Drop 'select' once.
            try:
                err = resp.json()
            except Exception:
                err = {}
            msg_list = err.get("message") or []
            if any(m.get("type") == "select-not-available" for m in msg_list):
                if verbose: print("[Crossref 400] Dropping select; server said:", err)
                params.pop("select", None)
                resp = _req(dict(params))
        resp.raise_for_status()

        payload = resp.json() or {}
        message = payload.get("message") or {}
        items = message.get("items") or []

        new_count = 0
        for it in items:
            rec = norm_crossref(it)
            if client_side_year_filter and rec.get("year") and rec["year"] < year_min:
                continue
            rid = rec.get("id")
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)
            if on_record: on_record(rec)
            out.append(rec)
            new_count += 1

        next_cursor = message.get("next-cursor")

        # Break conditions to prevent infinite loops
        if not next_cursor:
            if verbose: print("[Crossref] No next-cursor; done.")
            break
        if next_cursor == current_cursor:
            if verbose: print("[Crossref] next-cursor equals current cursor; breaking.")
            break
        if new_count == 0:
            if verbose: print("[Crossref] No new items in page; breaking.")
            break

        params["cursor"] = next_cursor
        current_cursor = next_cursor
        pages += 1
        if pages >= max_pages:
            if verbose: print(f"[Crossref] Reached max_pages={max_pages}; stopping.")
            break

    # Optional client-side sort by citations (if you disabled server sort)
    if disable_sort_with_cursor and sort == "is-referenced-by-count":
        out.sort(key=lambda r: (r.get("is_referenced_by_count") or 0), reverse=(order=="desc"))

    return out
