#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced multi-provider scholarly search for UDA/TTA/SFDA/CL in agricultural vision.
"""
import os, re, csv, sys, json, time, html, argparse, datetime, logging
from typing import Any, Dict, List, Optional, Callable
import requests
import xml.etree.ElementTree as ET

DEFAULT_YEAR_MIN = 2019
DEFAULT_LANGUAGE = "en"
OPENALEX_TYPE_FILTER = "type:article|preprint"
DEFAULT_TYPES_CROSSREF = {"journal-article", "proceedings-article", "posted-content"}
S2_ALLOWED_TYPES = {"journalarticle", "conference", "preprint"}
USER_AGENT_TEMPLATE = "AgriReviewBot/1.0 (mailto:{email})"
OPENALEX_SELECT = "id,ids,doi,display_name,publication_year,abstract_inverted_index,authorships,primary_location,locations,cited_by_count"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

def wait_for_rate_limit(seconds: float = 0.2): time.sleep(seconds)
def clean_text(s: Optional[str]) -> str: return " ".join(html.unescape(s or "").split())
def normalize_doi(doi: Optional[str]) -> str:
    if not doi: return ""
    return re.sub(r'^(https?://(dx\.)?doi\.org/)', '', doi.strip(), flags=re.I).lower()

def reconstruct_abstract_from_inverted_index(inv):
    max_pos = 0
    for positions in inv.values():
        if positions: max_pos = max(max_pos, max(positions))
    seq = [""] * (max_pos + 1)
    for word, positions in inv.items():
        for p in positions: seq[p] = word
    return " ".join(w for w in seq if w)

def boolean_groups(query: str):
    q = query.strip().replace("“","\"").replace("”","\"").replace("’","'")
    parts = re.split(r'\s+AND\s+', q, flags=re.IGNORECASE)
    groups = []
    for part in parts:
        part = part.strip()
        if part.startswith("(") and part.endswith(")"): part = part[1:-1].strip()
        alts = re.split(r'\s+OR\s+', part, flags=re.IGNORECASE)
        alts = [a.strip().strip('"').strip("'") for a in alts if a.strip()]
        if alts: groups.append(alts)
    return groups

def translate_query_openalex(boolean_q: str) -> str: return " ".join(boolean_q.split())

def translate_query_s2(boolean_q: str) -> str:
    groups = boolean_groups(boolean_q)
    if not groups: return boolean_q
    s2_groups = []
    for alts in groups:
        joined = " | ".join([f"\"{a}\"" if " " in a else a for a in alts])
        s2_groups.append(f"({joined})")
    return " + ".join(s2_groups)

def translate_query_crossref(boolean_q: str) -> str:
    tokens = re.split(r'\s+(AND|OR|NOT)\s+', boolean_q, flags=re.IGNORECASE)
    toks = []
    for t in tokens:
        t = t.strip()
        if not t or t.upper() in {"AND","OR","NOT"}: continue
        t = t.strip("()").strip('"').strip("'")
        toks.append(t)
    return " ".join(toks)

def translate_query_arxiv(boolean_q: str) -> str:
    groups = boolean_groups(boolean_q)
    if not groups:
        term = boolean_q.strip().strip('"').strip("'")
        return f'all:("{term}")' if " " in term else f"all:{term}"
    parts = []
    for alts in groups:
        or_parts = []
        for a in alts:
            or_parts.append(f'all:("{a}")' if " " in a else f'all:{a}')
        parts.append("(" + " OR ".join(or_parts) + ")")
    return " AND ".join(parts)

def postfilter_crossref_boolean(item, boolean_q: str) -> bool:
    title = " ".join(item.get("title") or [])
    abstract = item.get("abstract") or ""
    text = f"{title} {abstract}".lower()
    groups = boolean_groups(boolean_q)
    if not groups: return True
    for alts in groups:
        if not any(a.lower() in text for a in alts):
            return False
    return True

# Topic resolution
def resolve_openalex_topics(names: List[str], mailto: str, k_per_name: int = 1) -> List[str]:
    ids: List[str] = []
    base = "https://api.openalex.org/topics"
    for raw in names:
        q = raw.strip()
        if not q: continue
        params = {"search": q, "per-page": 25, "mailto": mailto}
        r = requests.get(base, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        cand = data.get("results", [])
        cand.sort(key=lambda x: (-(x.get("works_count") or 0), -(x.get("cited_by_count") or 0), x.get("display_name","")))
        for t in cand[:k_per_name]:
            tid = (t.get("id") or "").rsplit("/", 1)[-1]
            if tid and tid not in ids: ids.append(tid)
        wait_for_rate_limit(0.2)
    return ids

def add_topic_filter_to_openalex_params(params: dict, topic_ids: List[str], primary_only: bool = False):
    if not topic_ids: return
    key = "primary_topic.id" if primary_only else "topics.id"
    join = "|".join(topic_ids)
    params["filter"] = (params.get("filter") + f",{key}:{join}") if params.get("filter") else f"{key}:{join}"

# Normalizers
def norm_openalex(item):
    title = item.get("display_name")
    if not title: return None
    year = item.get("publication_year")
    ids = item.get("ids") or {}
    doi = ids.get("doi") or item.get("doi")
    url = (item.get("primary_location") or {}).get("landing_page_url") or item.get("id")
    abs_inv = item.get("abstract_inverted_index")
    abstract = reconstruct_abstract_from_inverted_index(abs_inv) if abs_inv else ""
    authors = [a["author"]["display_name"] for a in (item.get("authorships") or []) if a.get("author")]
    venue = ((item.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    return {
        "title": clean_text(title),
        "year": int(year) if year else None,
        "url": url,
        "doi": normalize_doi(doi),
        "abstract": clean_text(abstract),
        "authors": authors,
        "venue": venue or "",
        "provider_id": item.get("id"),
        "provider": "OpenAlex",
        "cited_by_count": item.get("cited_by_count", None),
    }

def norm_crossref(item):
    titles = item.get("title") or []
    title = titles[0] if titles else None
    if not title: return None
    issued = item.get("issued") or item.get("published-print") or item.get("published-online") or {}
    year = None
    if "date-parts" in issued and issued["date-parts"] and issued["date-parts"][0]:
        year = issued["date-parts"][0][0]
    url = item.get("URL")
    doi = item.get("DOI")
    abstract = item.get("abstract") or ""
    authors = [" ".join(filter(None, [a.get("given"), a.get("family")])) for a in item.get("author", [])]
    venue = (item.get("container-title") or [None])[0]
    return {
        "title": clean_text(title),
        "year": int(year) if year else None,
        "url": url,
        "doi": normalize_doi(doi),
        "abstract": clean_text(abstract),
        "authors": authors,
        "venue": venue or "",
        "provider_id": doi or url,
        "provider": "Crossref",
    }

def norm_s2(item):
    title = item.get("title")
    if not title: return None
    year = item.get("year")
    url = item.get("url")
    extern = item.get("externalIds") or {}
    doi = extern.get("DOI")
    abstract = item.get("abstract") or ""
    authors = [a.get("name") for a in item.get("authors", [])]
    venue = item.get("venue").get("name") if isinstance(item.get("venue"), dict) else item.get("venue")
    return {
        "title": clean_text(title),
        "year": int(year) if year else None,
        "url": url,
        "doi": normalize_doi(doi),
        "abstract": clean_text(abstract),
        "authors": authors,
        "venue": venue or "",
        "provider_id": extern.get("CorpusId") or extern.get("ArXiv") or extern.get("DBLP"),
        "provider": "SemanticScholar",
        "citationCount": item.get("citationCount"),
    }

def norm_arxiv(entry):
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom", "prism": "http://prismstandard.org/namespaces/basic/2.0/"}
    title_el = entry.find("atom:title", ns)
    if title_el is None: return None
    title = title_el.text or ""
    url = (entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else "").strip()
    abstract = (entry.find("atom:summary", ns).text or "").strip()
    pub = entry.find("atom:published", ns)
    year = int(pub.text.split("-")[0]) if pub is not None and pub.text else None
    authors = [a.text for a in entry.findall("atom:author/atom:name", ns)]
    doi_el = entry.find("arxiv:doi", ns) or entry.find("prism:doi", ns)
    doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""
    pdf_url = None
    for l in entry.findall("atom:link", ns):
        if l.get("type") == "application/pdf":
            pdf_url = l.get("href"); break
    return {
        "title": clean_text(title),
        "year": year,
        "url": pdf_url or url,
        "doi": normalize_doi(doi),
        "abstract": clean_text(abstract),
        "authors": authors,
        "venue": "arXiv",
        "provider_id": url,
        "provider": "arXiv",
    }

def to_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records: f.write(json.dumps(r, ensure_ascii=False) + "\n")

def append_jsonl_line(path, record):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def to_csv(path, records):
    records = list(records)
    for r in records:
        if r.get("authors") is not None and isinstance(r.get("authors"), list):
            auths = [str(a).strip() for a in r["authors"] if a is not None and str(a).strip()]
            r["authors"] = "; ".join(auths) if auths else ""
    fieldnames = ["query_id","query","title","year","venue","authors","provider","doi","url","abstract"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for r in records:
            w.writerow({
                "query_id": r.get("query_id",""), "query": r.get("query",""),
                "title": r.get("title",""), "year": r.get("year",""),
                "venue": r.get("venue",""), "authors": r.get("authors",""),
                "provider": r.get("provider",""), "doi": r.get("doi",""),
                "url": r.get("url",""), "abstract": r.get("abstract",""),
            })

def global_dedup(records):
    seen = {}
    for r in records:
        key = r.get("doi") or re.sub(r'[^a-z0-9]+', '', (r.get("title") or "").lower())
        if not key: continue
        if key not in seen:
            seen[key] = r
        else:
            if seen[key].get("venue") == "arXiv" and r.get("venue") and r["venue"] != "arXiv":
                seen[key] = r
            seen[key]["provider"] = "+".join(sorted(set((seen[key]["provider"] or "").split("+")) | {r.get("provider","")})).strip("+")
    return list(seen.values())

def search_openalex(boolean_q, email, year_min=DEFAULT_YEAR_MIN, language=DEFAULT_LANGUAGE,
                    topic_ids: Optional[List[str]] = None, primary_only: bool = False,
                    on_record: Optional[Callable[[Dict[str,Any]], None]]=None):
    base_url = "https://api.openalex.org/works"
    query = translate_query_openalex(boolean_q)
    current_year = datetime.datetime.now(datetime.UTC).year
    year_filter = f"publication_year:{year_min}-{current_year}"
    params = {
        "search": query,
        "filter": f"{year_filter},language:{language},{OPENALEX_TYPE_FILTER}",
        "per-page": 200,
        "cursor": "*",
        "select": OPENALEX_SELECT,
        "mailto": email
    }
    add_topic_filter_to_openalex_params(params, topic_ids or [], primary_only=primary_only)

    out = []
    while True:
        wait_for_rate_limit(0.2)
        r = requests.get(base_url, params=params, timeout=30)
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.0); continue
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAlex {r.status_code}: {r.text[:500]}")
        data = r.json()
        for item in data.get("results", []):
            rec = norm_openalex(item)
            if rec and (not rec["year"] or rec["year"] >= year_min):
                out.append(rec)
                if on_record: on_record(rec)
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor: break
        params["cursor"] = cursor
    return out

def search_crossref(boolean_q, email, year_min=DEFAULT_YEAR_MIN, language=DEFAULT_LANGUAGE,
                    on_record: Optional[Callable[[Dict[str,Any]], None]]=None):
    base_url = "https://api.crossref.org/works"
    bag = translate_query_crossref(boolean_q)
    params = {
        "query.bibliographic": bag,
        "filter": f"from-pub-date:{year_min}-01-01",
        "rows": 1000,
        "cursor": "*",
    }
    headers = {"User-Agent": USER_AGENT_TEMPLATE.format(email=email)}
    out = []
    while True:
        wait_for_rate_limit(0.2)
        r = requests.get(base_url, params=params, headers=headers, timeout=30)
        if r.status_code in (429, 500, 502, 503): time.sleep(1.0); continue
        r.raise_for_status()
        msg = r.json().get("message", {})
        items = msg.get("items", [])
        for it in items:
            t = (it.get("type") or "").lower()
            if t and t not in DEFAULT_TYPES_CROSSREF: continue
            if not postfilter_crossref_boolean(it, boolean_q): continue
            rec = norm_crossref(it)
            if rec and (not rec["year"] or rec["year"] >= year_min):
                out.append(rec)
                if on_record: on_record(rec)
        nxt = msg.get("next-cursor")
        if not nxt: break
        params["cursor"] = nxt
    return out

def search_semantic_scholar(boolean_q, api_key, year_min=DEFAULT_YEAR_MIN,
                            on_record: Optional[Callable[[Dict[str,Any]], None]]=None):
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    query = translate_query_s2(boolean_q)
    params = {
        "query": query,
        "year": f"{year_min}-",
        "limit": 100,
    }
    headers = {"x-api-key": api_key} if api_key else {}
    out = []
    while True:
        wait_for_rate_limit(1.0)
        r = requests.get(base_url, params=params, headers=headers, timeout=30)
        if r.status_code in (429, 500, 502, 503): time.sleep(1.5); continue
        r.raise_for_status()
        data = r.json()
        for item in data.get("data", []):
            pts = [p.lower() for p in (item.get("publicationTypes") or [])]
            if pts and not any(p in S2_ALLOWED_TYPES for p in pts): continue
            rec = norm_s2(item)
            if rec and (not rec["year"] or rec["year"] >= year_min):
                out.append(rec)
                if on_record: on_record(rec)
        nxt = data.get("next")
        if not nxt: break
        params["token"] = nxt
    return out

def search_arxiv(boolean_q, year_min=DEFAULT_YEAR_MIN, on_record: Optional[Callable[[Dict[str,Any]], None]]=None):
    base_url = "http://export.arxiv.org/api/query"
    query = translate_query_arxiv(boolean_q)
    start, max_results = 0, 200
    out = []
    while True:
        params = {"search_query": query, "sortBy": "relevance", "start": start, "max_results": max_results}
        wait_for_rate_limit(0.3)
        r = requests.get(base_url, params=params, timeout=30)
        if r.status_code in (429, 500, 502, 503): time.sleep(1.0); continue
        r.raise_for_status()
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if not entries: break
        for e in entries:
            rec = norm_arxiv(e)
            if rec and rec.get("year") and rec["year"] >= year_min:
                out.append(rec)
                if on_record: on_record(rec)
        start += max_results
        if len(entries) < max_results: break
    return out

def run_once(boolean_q, providers, email, s2_key, year_min, topic_ids=None, primary_only=False, on_record=None):
    all_recs = []
    if "openalex" in providers:
        all_recs += search_openalex(boolean_q, email=email, year_min=year_min,
                                    topic_ids=topic_ids, primary_only=primary_only,
                                    on_record=on_record)
    if "crossref" in providers:
        all_recs += search_crossref(boolean_q, email=email, year_min=year_min, on_record=on_record)
    if "s2" in providers or "semanticscholar" in providers:
        all_recs += search_semantic_scholar(boolean_q, api_key=s2_key, year_min=year_min, on_record=on_record)
    if "arxiv" in providers:
        all_recs += search_arxiv(boolean_q, year_min=year_min, on_record=on_record)
    return all_recs

def main():
    ap = argparse.ArgumentParser(description="Multi-provider scholarly search with normalization, streaming & exports.")
    ap.add_argument("--queries-file", type=str, default="queries.json", help="JSON file with list of boolean queries")
    ap.add_argument("--providers", type=str, default="openalex,crossref,s2,arxiv", help="Comma list of providers")
    ap.add_argument("--year-min", type=int, default=DEFAULT_YEAR_MIN, help="Earliest publication year to include")
    ap.add_argument("--mailto", type=str, required=True, help="Email (OpenAlex polite pool & Crossref UA)")
    ap.add_argument("--s2-api-key", type=str, default=os.getenv("S2_API_KEY", ""), help="Semantic Scholar API key")
    ap.add_argument("--outdir", type=str, default="outputs", help="Directory to write non-streaming outputs")
    ap.add_argument("--stream-dir", type=str, default="", help="If set, write NDJSON streams to this directory while crawling")
    ap.add_argument("--topic-names", type=str, default="", help="Comma-separated topic names to resolve via OpenAlex /topics")
    ap.add_argument("--topic-scope", choices=["any","primary"], default="any", help="topics.id (any) or primary_topic.id (primary)")
    ap.add_argument("--topics-topk", type=int, default=1, help="How many topic IDs per provided name")
    args = ap.parse_args()

    providers = [p.strip().lower() for p in args.providers.split(",") if p.strip()]
    with open(args.queries_file, "r", encoding="utf-8") as f:
        queries = json.load(f)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = os.path.join(args.outdir, f"run_{timestamp}")
    os.makedirs(outdir, exist_ok=True)

    topic_ids = []
    if args.topic_names:
        names = [s.strip() for s in args.topic_names.split(",") if s.strip()]
        topic_ids = resolve_openalex_topics(names, mailto=args.mailto, k_per_name=args.topics_topk)
        print("Resolved topic IDs:", topic_ids)

    stream_global_path = None
    if args.stream_dir:
        os.makedirs(args.stream_dir, exist_ok=True)
        stream_global_path = os.path.join(args.stream_dir, "stream_global.ndjson")

    global_records = []
    for idx, q in enumerate(queries, start=1):
        per_stream_path = None
        if args.stream_dir:
            per_stream_path = os.path.join(args.stream_dir, f"Q{idx:02d}_stream.ndjson")
        def on_record(rec):
            rec2 = dict(rec); rec2["query"] = q; rec2["query_id"] = f"Q{idx:02d}"
            if per_stream_path: append_jsonl_line(per_stream_path, rec2)
            if stream_global_path: append_jsonl_line(stream_global_path, rec2)
        recs = run_once(q, providers=providers, email=args.mailto, s2_key=(args.s2_api_key or None),
                        year_min=args.year_min, topic_ids=topic_ids, primary_only=(args.topic_scope=="primary"),
                        on_record=(on_record if args.stream_dir else None))
        for r in recs:
            r["query"] = q; r["query_id"] = f"Q{idx:02d}"
        to_jsonl(os.path.join(outdir, f"Q{idx:02d}_results.jsonl"), recs)
        to_csv(os.path.join(outdir, f"Q{idx:02d}_results.csv"), recs)
        global_records.extend(recs)

    dedup = global_dedup(global_records)
    to_jsonl(os.path.join(outdir, "global_dedup.jsonl"), dedup)
    to_csv(os.path.join(outdir, "global_dedup.csv"), dedup)
    print(f"Done. Global dedup records: {len(dedup)}")

if __name__ == "__main__":
    main()
