# arxiv_provider.py
import time
import datetime as dt
import re
from typing import Optional, Callable, Dict, Any, List
import requests
import xml.etree.ElementTree as ET

# ---- optional import for your shared helpers --------------------------------
try:
    from enhanced_query_script import wait_for_rate_limit  # your throttler
except Exception:
    def wait_for_rate_limit(seconds: float) -> None:
        time.sleep(seconds)

# -----------------------------------------------------------------------------


ARXIV_ATOM_NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
ARXIV_BASE = "https://export.arxiv.org/api/query"

DEFAULT_UA = "AgriReviewBot/1.0 (+arXiv provider)"
DEFAULT_CATEGORIES = ("cs.CV", "cs.LG", "stat.ML", "eess.IV")  # edit if needed


def _is_arxiv_search_syntax(q: str) -> bool:
    """Heuristic: does the query already use arXiv field prefixes or cat:?"""
    return any(tok in q for tok in ("ti:", "abs:", "all:", "cat:", "au:", "ti-abs:"))


def _attach_categories(search_query: str, categories: Optional[List[str]]) -> str:
    if not categories:
        return search_query
    cat_clause = " OR ".join([f"cat:{c}" for c in categories])
    # If user already included cat: terms, don't force add again.
    if "cat:" in search_query:
        return search_query
    return f"({search_query}) AND ({cat_clause})"


def _to_arxiv_query(user_query: str, categories: Optional[List[str]]) -> str:
    """
    If the user query is already arXiv-style, use it as-is and (optionally) AND categories.
    Otherwise, search in title OR abstract OR general 'all:' with simple wrapping.
    """
    if _is_arxiv_search_syntax(user_query):
        return _attach_categories(user_query, categories)

    # naive wrap: look for the phrase in title or abstract or anywhere
    safe = user_query.strip()
    # prefer 'all:' to preserve any boolean-ish words; still treat as a free string
    base = f'(ti:"{safe}" OR abs:"{safe}" OR all:"{safe}")'
    return _attach_categories(base, categories)


def _parse_year(iso_date: Optional[str]) -> Optional[int]:
    if not iso_date:
        return None
    try:
        return int(iso_date[:4])
    except Exception:
        return None


def _extract_pdf_and_abs_links(entry) -> (Optional[str], Optional[str]):
    pdf_url, abs_url = None, None
    for link in entry.findall("a:link", ARXIV_ATOM_NS):
        href = link.attrib.get("href")
        rel = link.attrib.get("rel", "")
        typ = link.attrib.get("type", "")
        title = link.attrib.get("title", "")
        if not href:
            continue
        # arXiv typically: rel="alternate" is the abstract page
        if rel == "alternate" and "arxiv.org" in href:
            abs_url = href
        # pdf link often has type application/pdf OR title="pdf"
        if typ == "application/pdf" or title.lower() == "pdf":
            pdf_url = href
    # fallback: guess pdf from abs link
    if (not pdf_url) and abs_url and "/abs/" in abs_url:
        pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"
    return pdf_url, abs_url


def _extract_arxiv_id_from_idurl(id_url: str) -> Optional[str]:
    # Examples: http(s)://arxiv.org/abs/YYMM.NNNNvX  or http(s)://arxiv.org/abs/XXXX.YYYY
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", id_url or "")
    if m:
        val = m.group(1)
        # normalize to "arXiv:<id>" style
        if not val.lower().startswith("arxiv:"):
            return f"arXiv:{val}"
        return val
    # sometimes id is just the ID
    if id_url and id_url.lower().startswith("arxiv:"):
        return id_url
    return None


def norm_arxiv(entry) -> Dict[str, Any]:
    """Normalize a single <entry> into a provider-agnostic record."""
    title = (entry.findtext("a:title", default="", namespaces=ARXIV_ATOM_NS) or "").strip()
    summary = (entry.findtext("a:summary", default="", namespaces=ARXIV_ATOM_NS) or "").strip()
    published = entry.findtext("a:published", default="", namespaces=ARXIV_ATOM_NS)
    updated = entry.findtext("a:updated", default="", namespaces=ARXIV_ATOM_NS)
    year = _parse_year(published) or _parse_year(updated)

    # authors
    authors = []
    for a in entry.findall("a:author", ARXIV_ATOM_NS):
        name = a.findtext("a:name", default="", namespaces=ARXIV_ATOM_NS)
        if name:
            authors.append({"name": name.strip()})

    # categories
    categories = [c.attrib.get("term") for c in entry.findall("a:category", ARXIV_ATOM_NS) if c.attrib.get("term")]
    primary_cat_elem = entry.find("arxiv:primary_category", ARXIV_ATOM_NS)
    primary_category = primary_cat_elem.attrib.get("term") if primary_cat_elem is not None else None

    # links
    id_url = entry.findtext("a:id", default="", namespaces=ARXIV_ATOM_NS)
    pdf_url, abs_url = _extract_pdf_and_abs_links(entry)

    # DOI (optional extension)
    doi = entry.findtext("arxiv:doi", default=None, namespaces=ARXIV_ATOM_NS)
    arxiv_id = _extract_arxiv_id_from_idurl(id_url)

    return {
        "provider": "arxiv",
        "id": arxiv_id or id_url or None,
        "doi": doi,
        "title": title,
        "abstract": summary,
        "year": year,
        "authors": authors,
        "venue": f"arXiv{f' ({primary_category})' if primary_category else ''}",
        "url": abs_url or id_url or None,
        "pdf_url": pdf_url,
        "publicationTypes": ["Preprint"],
        "categories": categories,
        "primary_category": primary_category,
        "published": published,
        "updated": updated,
        # keep slots used by your CSV/JSONL unifier (safe to include None)
        "citationCount": None,
        "isOpenAccess": True
    }


def search_arxiv(
    query: str,
    on_record: Optional[Callable[[Dict[str, Any]], None]] = None,
    year_min: int = 2018,
    categories: Optional[List[str]] = list(DEFAULT_CATEGORIES),
    per_page: int = 100,
    max_total: Optional[int] = None,
    sort_by: str = "submittedDate",            # arXiv: "relevance"|"lastUpdatedDate"|"submittedDate"
    sort_order: str = "descending",            # "ascending"|"descending"
    polite_delay: float = 3.0,                 # be nice to arXiv API
    user_agent: str = DEFAULT_UA
) -> List[Dict[str, Any]]:
    """
    Call arXiv Atom API, paginate, and normalize results.
    Accepts either a ready-to-go arXiv search_query OR a human query to be wrapped.
    """
    headers = {"User-Agent": user_agent}
    out: List[Dict[str, Any]] = []

    search_q = _to_arxiv_query(query, categories=categories)
    start = 0
    total_results = None

    session = requests.Session()

    while True:
        wait_for_rate_limit(polite_delay)

        params = {
            "search_query": search_q,
            "start": start,
            "max_results": per_page,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        resp = session.get(ARXIV_BASE, params=params, headers=headers, timeout=30)
        if resp.status_code in (429, 500, 502, 503):
            # backoff a little and retry
            time.sleep(2.0)
            continue
        resp.raise_for_status()

        root = ET.fromstring(resp.text)

        # read total only once
        if total_results is None:
            tot_text = root.findtext("os:totalResults", default="0", namespaces=ARXIV_ATOM_NS)
            try:
                total_results = int(tot_text)
            except Exception:
                total_results = 0

        entries = root.findall("a:entry", ARXIV_ATOM_NS)
        if not entries:
            break

        for entry in entries:
            rec = norm_arxiv(entry)
            # client-side year filter (arXiv doesn't provide year filter server-side)
            if rec.get("year") is not None and rec["year"] < year_min:
                continue
            out.append(rec)
            if on_record:
                on_record(rec)
            if max_total is not None and len(out) >= max_total:
                return out

        start += per_page
        if total_results is not None and start >= total_results:
            break

    return out
