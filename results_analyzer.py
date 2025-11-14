#!/usr/bin/env python3
import os, csv, json, re, glob, argparse, collections, time, requests
from typing import Dict, List, Tuple, Any, Set, DefaultDict
try:
    import pandas as pd
except Exception:
    pd = None

def norm_key(rec: Dict[str,Any]) -> str:
    doi = (rec.get("doi") or "").strip().lower()
    if doi:
        doi = re.sub(r'^(https?://(dx\.)?doi\.org/)', '', doi, flags=re.I)
        return "doi:" + doi
    title = (rec.get("title") or "").lower()
    title = re.sub(r'[^a-z0-9]+', '', title)
    return "t:" + title

def load_records_from_path(path: str) -> List[Dict[str,Any]]:
    recs = []
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "Q*_results.jsonl"))) + \
                sorted(glob.glob(os.path.join(path, "Q*_results.csv")))
    else:
        files = [path]
    for fp in files:
        if fp.endswith(".jsonl"):
            with open(fp, "r", encoding="utf-8") as f:
                for line in f:
                    try: recs.append(json.loads(line))
                    except json.JSONDecodeError: continue
        elif fp.endswith(".csv"):
            if pd is None:
                with open(fp, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f); recs.extend(list(reader))
            else:
                df = pd.read_csv(fp); recs.extend(df.to_dict(orient="records"))
    return recs

def build_membership(records: List[Dict[str,Any]]):
    info_by_key = {}
    queries_by_key = collections.defaultdict(set)
    for r in records:
        key = norm_key(r)
        if not key: continue
        info_by_key.setdefault(key, {
            "title": r.get("title",""), "doi": r.get("doi",""), "url": r.get("url",""),
            "venue": r.get("venue",""), "year": r.get("year",""), "authors": r.get("authors",""),
            "provider": r.get("provider",""),
            "cited_by_count": r.get("cited_by_count") or r.get("is-referenced-by-count") or r.get("citationCount") or ""
        })
        qid = r.get("query_id") or r.get("query") or ""
        if qid: queries_by_key[key].add(str(qid))
    return info_by_key, queries_by_key

def compute_overlap(queries_by_key):
    all_q = set()
    for qs in queries_by_key.values(): all_q.update(qs)
    q_list = sorted(all_q)
    pair_counts = collections.Counter()
    for qs in queries_by_key.values():
        qs = sorted(qs)
        for i in range(len(qs)):
            for j in range(i, len(qs)):
                pair_counts[(qs[i], qs[j])] += 1
    return q_list, pair_counts

def export_overlap_matrix(outdir, q_list, pair_counts):
    path = os.path.join(outdir, "overlap_matrix.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([""] + q_list)
        for qi in q_list:
            row = [qi]
            for qj in q_list:
                a, b = (qi, qj) if qi <= qj else (qj, qi)
                row.append(pair_counts.get((a,b), 0))
            w.writerow(row)

def export_per_paper(outdir, info_by_key, queries_by_key):
    path = os.path.join(outdir, "per_paper_queries.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key","title","doi","year","venue","n_queries","query_ids","url","authors","provider","cited_by_count"])
        for key, info in info_by_key.items():
            qs = sorted(list(queries_by_key.get(key, set())))
            w.writerow([key, info.get("title",""), info.get("doi",""), info.get("year",""),
                        info.get("venue",""), len(qs), ";".join(qs), info.get("url",""),
                        info.get("authors",""), info.get("provider",""), info.get("cited_by_count","")])

def export_top_intersections(outdir, q_list, pair_counts, topk=30):
    path = os.path.join(outdir, "top_intersections.csv")
    pairs = []
    for (a,b), c in pair_counts.items():
        if a == b: continue
        pairs.append((a,b,c))
    pairs.sort(key=lambda x: x[2], reverse=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["q1","q2","overlap_count"])
        for a,b,c in pairs[:topk]:
            w.writerow([a,b,c])

def openalex_citations_for_doi(doi: str, mailto: str) -> int:
    try:
        url = f"https://api.openalex.org/works/doi:{doi}"
        resp = requests.get(url, params={"mailto": mailto}, timeout=15)
        if resp.status_code == 200:
            j = resp.json()
            return int(j.get("cited_by_count") or 0)
    except Exception:
        return 0
    return 0

def maybe_enrich_citations(info_by_key, mailto):
    for key, info in info_by_key.items():
        if info.get("cited_by_count"): continue
        doi = (info.get("doi") or "").strip().lower()
        if not doi: continue
        c = openalex_citations_for_doi(doi, mailto=mailto)
        if c: info["cited_by_count"] = c
        time.sleep(0.2)

def export_top_cited(outdir, info_by_key, topk=100):
    rows = []
    for key, info in info_by_key.items():
        c = info.get("cited_by_count")
        try: c = int(c) if c not in ("", None) else 0
        except Exception: c = 0
        rows.append((c, key, info))
    rows.sort(key=lambda x: x[0], reverse=True)
    path = os.path.join(outdir, "top_cited.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cited_by_count","key","title","doi","year","venue","url"])
        for c, key, info in rows[:topk]:
            w.writerow([c, key, info.get("title",""), info.get("doi",""), info.get("year",""), info.get("venue",""), info.get("url","")])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True, help="Directory with Q** files or list of files")
    ap.add_argument("--outdir", required=True, help="Output directory for analysis CSVs")
    ap.add_argument("--mailto", default="", help="Email for OpenAlex enrichment polite pool")
    ap.add_argument("--enrich-openalex", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    all_records = []
    for p in args.inputs: all_records.extend(load_records_from_path(p))
    info_by_key, queries_by_key = build_membership(all_records)
    q_list, pair_counts = compute_overlap(queries_by_key)
    export_overlap_matrix(args.outdir, q_list, pair_counts)
    export_per_paper(args.outdir, info_by_key, queries_by_key)
    export_top_intersections(args.outdir, q_list, pair_counts)
    if args.enrich_openalex and args.mailto: maybe_enrich_citations(info_by_key, mailto=args.mailto)
    export_top_cited(args.outdir, info_by_key)
    print(f"Done. Papers: {len(info_by_key)}; Queries: {len(q_list)}")

if __name__ == "__main__":
    main()
