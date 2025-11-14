# deduplicate_providers.py
# Robust cross-provider deduplication (OpenAlex, Crossref, arXiv, S2)
# Conservative defaults to minimize false merges.

import os, sys, csv, json, glob, hashlib, argparse, unicodedata, re, ast
from collections import defaultdict
from typing import Dict, Any, List, Tuple, Optional

# --- Optional fast fuzzy; graceful fallback to difflib ---
try:
    from rapidfuzz import fuzz
    def token_set_ratio(a: str, b: str) -> int:
        return int(fuzz.token_set_ratio(a, b))
except Exception:
    import difflib
    def _tokenize(s: str) -> List[str]:
        return sorted(set(re.findall(r"[a-z0-9]+", s.lower())))
    def token_set_ratio(a: str, b: str) -> int:
        ta, tb = _tokenize(a), _tokenize(b)
        sm = difflib.SequenceMatcher(a=" ".join(ta), b=" ".join(tb))
        return int(round(100 * sm.ratio()))

STOP = set("""
a an and the for of on to with without within under over from in by at into as is are were was be being been
""".split())

ARXIV_PAT = re.compile(r'arxiv\.org/(abs|pdf)/([0-9]{4}\.[0-9]{4,5}(v\d+)?|[a-z\-]+(\.[A-Z]{2})?/\d{7})(\.pdf)?', re.I)
DOI_URL_PAT = re.compile(r'(https?://(dx\.)?doi\.org/)', re.I)
DOI_PREFIX_PAT = re.compile(r'^(doi:)\s*', re.I)
NON_ALNUM = re.compile(r'[^a-z0-9]+')

def ascii_fold(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def norm_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def normalize_title(s: Optional[str]) -> str:
    if not s: return ""
    s = ascii_fold(s).lower()
    s = norm_whitespace(s)
    return s

def title_fingerprint(s: str, keep_n_tokens: int = 30) -> str:
    toks = [t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP]
    toks = toks[:keep_n_tokens]
    # order-insensitive fingerprint
    uniq = sorted(set(toks))
    return " ".join(uniq)

def normalize_doi(x: Optional[str]) -> str:
    if not x: return ""
    x = x.strip()
    x = DOI_URL_PAT.sub("", x)          # strip https://doi.org/
    x = DOI_PREFIX_PAT.sub("", x)       # strip doi:
    x = x.strip().strip('.').strip('/')
    return x.lower()

def extract_arxiv_id(record: Dict[str, Any]) -> str:
    # 1) explicit field
    for key in ("arxiv_id","arXiv","arXivId","arxivId","arxiv"):
        v = record.get(key)
        if isinstance(v, str) and v:
            return v.lower().replace("arxiv:", "").strip()
    # 2) external IDs container patterns (S2/OpenAlex)
    for key in ("externalIds","external_ids","ids"):
        ex = record.get(key) or {}
        if isinstance(ex, dict):
            for k in ex.keys():
                if k.lower() == "arxiv":
                    return str(ex.get(k,"")).lower().replace("arxiv:", "").strip()
    # 3) URLs
    for key in ("url", "URL", "link"):
        v = record.get(key)
        if isinstance(v, str) and v:
            m = ARXIV_PAT.search(v)
            if m:
                return m.group(2).lower()
    # 4) best_oa_location url (OpenAlex)
    bol = record.get("best_oa_location") or {}
    if isinstance(bol, dict):
        v = bol.get("url")
        if isinstance(v, str):
            m = ARXIV_PAT.search(v)
            if m:
                return m.group(2).lower()
    return ""

def first_author_family(record: Dict[str, Any]) -> str:
    # Try several shapes
    # Crossref style: authors = [{given, family, ORCID}, ...]
    auths = record.get("authors") or record.get("author") or []
    # If authors is a stringified list/dict (often in CSV), try to parse
    if isinstance(auths, str):
        try:
            parsed = ast.literal_eval(auths)
            if isinstance(parsed, list):
                auths = parsed
            elif isinstance(parsed, dict):
                auths = [parsed]
        except Exception:
            pass
    if isinstance(auths, list) and auths:
        a0 = auths[0]
        if isinstance(a0, dict):
            fam = a0.get("family") or a0.get("last_name") or a0.get("last") or ""
            if not fam:
                # OpenAlex authorships style
                if "display_name" in a0:
                    fam = a0["display_name"].split()[-1]
            return NON_ALNUM.sub("", fam.lower())
        if isinstance(a0, str):
            return NON_ALNUM.sub("", a0.strip().split()[-1].lower())
    # OpenAlex: authorships -> author -> display_name
    aus = record.get("authorships") or []
    if isinstance(aus, list) and aus:
        a0 = aus[0] or {}
        auth = a0.get("author") or {}
        dn = auth.get("display_name") or ""
        if dn:
            return NON_ALNUM.sub("", dn.strip().split()[-1].lower())
    # Fallback: try a single author string
    a = record.get("author")
    if isinstance(a, str) and a:
        return NON_ALNUM.sub("", a.strip().split()[-1].lower())
    return ""

def record_provider_id(rec: Dict[str, Any]) -> str:
    # Keep original provider-specific IDs to preserve provenance
    src = (rec.get("source") or rec.get("provider") or "").lower()
    # Prefer already present provider_id if any
    pid = rec.get("provider_id") or None
    if src == "openalex":
        return rec.get("id") or rec.get("openalex_id") or pid or rec.get("doi") or rec.get("url") or ""
    if src == "s2" or src == "semanticscholar":
        return rec.get("paperId") or rec.get("s2_id") or pid or rec.get("doi") or rec.get("url") or ""
    if src == "arxiv":
        return rec.get("arxiv_id") or extract_arxiv_id(rec) or rec.get("id") or pid or rec.get("doi") or rec.get("url") or ""
    if src == "crossref":
        return rec.get("doi") or rec.get("DOI") or rec.get("id") or pid or rec.get("url") or ""
    # generic
    return pid or rec.get("id") or rec.get("doi") or rec.get("url") or ""

def get_year(rec: Dict[str, Any]) -> Optional[int]:
    y = rec.get("year") or rec.get("publication_year")
    try:
        return int(y) if y is not None else None
    except Exception:
        return None

def safe_title(rec: Dict[str, Any]) -> str:
    t = rec.get("title") or rec.get("display_name") or ""
    if isinstance(t, list): t = t[0] if t else ""
    return t

def load_records(input_dir: str) -> List[Dict[str, Any]]:
    records = []
    skip_basenames = {
        "all_results.csv", "all_results.jsonl",
        "clusters.csv", "members.csv", "deduped.jsonl", "problems.jsonl",
        # new optional outputs to avoid self-ingestion
        "representatives.csv", "representatives.jsonl",
        "doi_to_cluster.csv", "arxiv_to_cluster.csv",
        "cluster_sources.csv"
    }
    for path in glob.glob(os.path.join(input_dir, "**", "*.*"), recursive=True):
        pnorm = path.replace("\\", "/")
        base = os.path.basename(path)
        # Avoid self-ingesting previous dedup outputs
        if any(seg.startswith("dedup_") for seg in pnorm.split("/")):
            continue
        if base in skip_basenames:
            continue
        if path.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if isinstance(rec, dict):
                            rec["__path"] = path
                        records.append(rec)
                    except Exception:
                        continue
        elif path.endswith(".csv"):
            with open(path, "r", encoding="utf-8-sig") as f:
                rdr = csv.DictReader(f)
                for row in rdr:
                    rowd = dict(row)
                    rowd["__path"] = path
                    records.append(rowd)
    return records

class DSU:
    def __init__(self, n:int):
        self.p = list(range(n))
        self.r = [0]*n
    def find(self, x:int)->int:
        while self.p[x]!=x:
            self.p[x]=self.p[self.p[x]]
            x=self.p[x]
        return x
    def union(self, a:int, b:int):
        ra, rb = self.find(a), self.find(b)
        if ra==rb: return
        if self.r[ra]<self.r[rb]: ra, rb = rb, ra
        self.p[rb]=ra
        if self.r[ra]==self.r[rb]: self.r[ra]+=1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Directory containing provider results (jsonl/csv)")
    ap.add_argument("--outdir", required=True, help="Where to write dedup outputs")
    ap.add_argument("--min-fuzzy", type=int, default=97, help="Min token_set fuzzy score to merge")
    ap.add_argument("--max-year-gap", type=int, default=1, help="Max |yearA-yearB| allowed for fuzzy merge")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true", help="Strict mode (default)")
    mode.add_argument("--loose", action="store_true", help="Looser fuzzy (95) + allows year gap 2")
    args = ap.parse_args()

    if args.loose:
        min_fuzzy = min(95, args.min_fuzzy)
        max_year_gap = max(2, args.max_year_gap)
    else:
        min_fuzzy = args.min_fuzzy
        max_year_gap = args.max_year_gap

    os.makedirs(args.outdir, exist_ok=True)

    raw = load_records(args.input)
    cleaned = []
    problems = []

    # Normalize/minimal schema
    for r in raw:
        title = safe_title(r)
        year  = get_year(r)
        if not title or year is None:
            problems.append({"reason":"missing_title_or_year", "raw":r})
            continue

        src = (r.get("source") or r.get("provider") or "").lower()
        if not src:
            # heuristic: infer source from fields
            if "openalex" in (r.get("id") or ""): src="openalex"
            elif r.get("paperId"): src="s2"
            elif (r.get("DOI") or r.get("doi")) and r.get("publisher"): src="crossref"
            elif extract_arxiv_id(r): src="arxiv"
        if not src:
            # fallback: infer from file path
            p = (r.get("__path") or "").lower()
            for key in ("openalex","crossref","arxiv","s2"):
                if key in p:
                    src = key
                    break
        # normalize known aliases
        if src in ("semanticscholar", "semantic_scholar", "ss"):
            src = "s2"

        doi = normalize_doi(r.get("doi") or r.get("DOI") or "")
        arx = extract_arxiv_id(r)
        tnorm = normalize_title(title)
        tfp = title_fingerprint(tnorm)
        fa = first_author_family(r)

        canonical = {
            "source": src or None,
            "provider_id": record_provider_id(r),
            "doi": doi or None,
            "arxiv_id": arx or None,
            "openalex_id": (r.get("openalex_id") or r.get("id") or r.get("provider_id")) if src=="openalex" else None,
            "s2_id": (r.get("paperId") or r.get("s2_id") or r.get("provider_id")) if src=="s2" else None,
            "title": title,
            "title_norm": tnorm,
            "title_fp": tfp,
            "year": year,
            "first_author_family": fa or None,
            "url": r.get("url") or r.get("URL") or None,
            "venue": r.get("venue") or r.get("container-title") or None,
            "cited_by_count": r.get("cited_by_count") or r.get("is_referenced_by_count") or None,
            "raw": r,  # keep full raw for provenance
        }
        cleaned.append(canonical)

    n = len(cleaned)
    dsu = DSU(n)

    # --- 1) Merge by DOI ---
    by_doi = defaultdict(list)
    for i, rec in enumerate(cleaned):
        if rec["doi"]:
            by_doi[rec["doi"]].append(i)
    for k, idxs in by_doi.items():
        for i in range(1, len(idxs)):
            dsu.union(idxs[0], idxs[i])

    # --- 2) Merge by arXiv ID ---
    by_arx = defaultdict(list)
    for i, rec in enumerate(cleaned):
        if rec["arxiv_id"]:
            by_arx[rec["arxiv_id"]].append(i)
    for k, idxs in by_arx.items():
        for i in range(1, len(idxs)):
            dsu.union(idxs[0], idxs[i])

    # --- 3) Title EXACT equality (normalized) + year match ---
    by_title_year = defaultdict(list)
    for i, rec in enumerate(cleaned):
        by_title_year[(rec["title_norm"], rec["year"])].append(i)
    for k, idxs in by_title_year.items():
        if len(idxs) > 1:
            base = idxs[0]
            for j in idxs[1:]:
                dsu.union(base, j)

    # --- 4) Block by (year, first12 of fp hash) then fuzzy within block ---
    def fp_block_key(rec):
        h = hashlib.sha1(rec["title_fp"].encode("utf-8")).hexdigest()
        return (rec["year"], h[:12])

    blocks = defaultdict(list)
    for i, rec in enumerate(cleaned):
        blocks[fp_block_key(rec)].append(i)

    for key, idxs in blocks.items():
        if len(idxs) < 2:
            continue
        # pairwise within block (small)
        for a in range(len(idxs)):
            ia = idxs[a]; ra = cleaned[ia]
            for b in range(a+1, len(idxs)):
                ib = idxs[b]; rb = cleaned[ib]
                # already merged by DOI/arXiv/exact? skip
                if dsu.find(ia) == dsu.find(ib): continue

                # must satisfy strong textual agreement
                score = token_set_ratio(ra["title"], rb["title"])
                if score < min_fuzzy:
                    continue

                ya, yb = ra["year"], rb["year"]
                if ya is None or yb is None or abs(ya - yb) > max_year_gap:
                    continue

                # Require first-author family name match if present on both
                fa, fb = ra.get("first_author_family"), rb.get("first_author_family")
                if fa and fb and fa != fb:
                    continue

                dsu.union(ia, ib)

    # Build clusters
    roots = defaultdict(list)
    for i in range(n):
        roots[dsu.find(i)].append(i)

    clusters = []
    members_rows = []
    for cid, (root, idxs) in enumerate(roots.items(), start=1):
        # Choose representative: prefer DOI; else arXiv; else highest citations; else longest title
        choice = idxs[0]
        def rep_key(i):
            r = cleaned[i]
            has_doi = 1 if r["doi"] else 0
            has_arx = 1 if r["arxiv_id"] else 0
            cits = int(r["cited_by_count"] or 0)
            tlen = len(r["title"] or "")
            return (has_doi, has_arx, cits, tlen)
        choice = max(idxs, key=rep_key)

        rep = dict(cleaned[choice])
        rep["cluster_id"] = cid

        # collect provenance
        prov = []
        dois = set(); arxs = set()
        for i in idxs:
            r = cleaned[i]
            prov.append({
                "source": r["source"],
                "provider_id": r["provider_id"],
                "doi": r["doi"],
                "arxiv_id": r["arxiv_id"],
                "year": r["year"],
                "title": r["title"],
                "url": r["url"],
            })
            if r["doi"]: dois.add(r["doi"])
            if r["arxiv_id"]: arxs.add(r["arxiv_id"])
            members_rows.append({
                "cluster_id": cid,
                "source": r["source"],
                "provider_id": r["provider_id"],
                "doi": r["doi"] or "",
                "arxiv_id": r["arxiv_id"] or "",
                "year": r["year"] or "",
                "title": r["title"],
                "url": r["url"] or "",
            })

        rep["members"] = prov
        rep["dois_in_cluster"] = sorted(dois)
        rep["arxiv_ids_in_cluster"] = sorted(arxs)
        clusters.append(rep)

    # Write outputs
    outdir = args.outdir
    with open(os.path.join(outdir, "deduped.jsonl"), "w", encoding="utf-8") as f:
        for c in clusters:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    with open(os.path.join(outdir, "clusters.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id","size","rep_year","rep_title","rep_doi","rep_arxiv","n_dois","n_arxiv"])
        for c in clusters:
            w.writerow([
                c["cluster_id"],
                len(c["members"]),
                c.get("year") or "",
                (c.get("title") or "")[:160],
                c.get("doi") or "",
                c.get("arxiv_id") or "",
                len(c.get("dois_in_cluster") or []),
                len(c.get("arxiv_ids_in_cluster") or []),
            ])

    with open(os.path.join(outdir, "members.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id","source","provider_id","doi","arxiv_id","year","title","url"])
        for row in members_rows:
            w.writerow([
                row["cluster_id"], row["source"], row["provider_id"], row["doi"],
                row["arxiv_id"], row["year"], row["title"], row["url"]
            ])

    if problems:
        with open(os.path.join(outdir, "problems.jsonl"), "w", encoding="utf-8") as f:
            for p in problems:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # --- Optional extras ---
    # 1) Representative-only JSONL/CSV (one row per cluster)
    reps_csv_rows = []
    with open(os.path.join(outdir, "representatives.jsonl"), "w", encoding="utf-8") as f:
        for c in clusters:
            rep_only = dict(c)
            # drop heavy/internal fields
            rep_only.pop("members", None)
            rep_only.pop("raw", None)
            rep_only.pop("title_norm", None)
            rep_only.pop("title_fp", None)
            rep_only.pop("first_author_family", None)
            f.write(json.dumps(rep_only, ensure_ascii=False) + "\n")
            reps_csv_rows.append({
                "cluster_id": rep_only.get("cluster_id"),
                "source": rep_only.get("source") or "",
                "provider_id": rep_only.get("provider_id") or "",
                "year": rep_only.get("year") or "",
                "title": rep_only.get("title") or "",
                "doi": rep_only.get("doi") or "",
                "arxiv_id": rep_only.get("arxiv_id") or "",
                "url": rep_only.get("url") or "",
                "venue": rep_only.get("venue") or "",
                "cited_by_count": rep_only.get("cited_by_count") or "",
                "n_dois": len(rep_only.get("dois_in_cluster") or []),
                "n_arxiv": len(rep_only.get("arxiv_ids_in_cluster") or []),
                "size": len(c.get("members") or []),
            })

    with open(os.path.join(outdir, "representatives.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id","size","year","title","source","provider_id","doi","arxiv_id","url","venue","cited_by_count","n_dois","n_arxiv"])
        for r in reps_csv_rows:
            w.writerow([
                r["cluster_id"], r["size"], r["year"], (r["title"] or "")[:160], r["source"], r["provider_id"],
                r["doi"], r["arxiv_id"], r["url"], r["venue"], r["cited_by_count"], r["n_dois"], r["n_arxiv"]
            ])

    # 2) Per-source breakdown per cluster (long format)
    source_counts = defaultdict(lambda: defaultdict(int))  # cluster_id -> source -> count
    for row in members_rows:
        cid = row.get("cluster_id")
        src = (row.get("source") or "").lower() or "unknown"
        source_counts[cid][src] += 1
    with open(os.path.join(outdir, "cluster_sources.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster_id","source","count"])
        for cid, cts in source_counts.items():
            for src, cnt in cts.items():
                w.writerow([cid, src, cnt])

    # 3) DOI -> cluster and arXiv -> cluster maps
    doi_map = {}
    arxiv_map = {}
    for row in members_rows:
        cid = row.get("cluster_id")
        doi = (row.get("doi") or "").strip().lower()
        arx = (row.get("arxiv_id") or "").strip().lower()
        if doi:
            doi_map.setdefault(doi, cid)
        if arx:
            arxiv_map.setdefault(arx, cid)

    with open(os.path.join(outdir, "doi_to_cluster.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doi","cluster_id"])
        for doi, cid in sorted(doi_map.items()):
            w.writerow([doi, cid])

    with open(os.path.join(outdir, "arxiv_to_cluster.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arxiv_id","cluster_id"])
        for arx, cid in sorted(arxiv_map.items()):
            w.writerow([arx, cid])

    print(f"[dedup] clusters: {len(clusters)}; members: {len(members_rows)}; problems: {len(problems)}")
    print(f"[dedup] wrote: {outdir}/deduped.jsonl, clusters.csv, members.csv, problems.jsonl")
    print(f"[dedup] wrote extras: {outdir}/representatives.csv, representatives.jsonl, cluster_sources.csv, doi_to_cluster.csv, arxiv_to_cluster.csv")

if __name__ == "__main__":
    main()
