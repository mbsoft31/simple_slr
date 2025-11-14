#!/usr/bin/env python3
import os, csv, json, argparse, re
from typing import Dict, Any, List

def load_records(path: str) -> List[Dict[str,Any]]:
    recs = []
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try: recs.append(json.loads(line))
                except Exception: continue
    else:
        import pandas as pd
        df = pd.read_csv(path); recs = df.to_dict(orient="records")
    return recs

def index_existing(out_path: str):
    if not os.path.exists(out_path): return {}
    labeled = {}
    import csv as _csv
    with open(out_path, newline="", encoding="utf-8") as f:
        r = _csv.DictReader(f)
        for row in r:
            key = (row.get("doi") or "").strip().lower() or re.sub(r'[^a-z0-9]+', '', (row.get("title") or "").lower())
            labeled[key] = row
    return labeled

def pretty_print(rec, idx, total):
    print("\n" + "="*80)
    print(f"[{idx+1}/{total}] {rec.get('title','').strip()}")
    print(f"Authors: {rec.get('authors','')} | Year: {rec.get('year','')} | Venue: {rec.get('venue','')}")
    print(f"URL: {rec.get('url','')}  DOI: {rec.get('doi','')}")
    abstract = (rec.get('abstract') or '').strip()
    if abstract:
        if len(abstract) > 1200: abstract = abstract[:1200] + ' ...'
        print("\nAbstract:\n" + abstract)
    else:
        print("\nAbstract: (none)")
    print("="*80)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input CSV or JSONL")
    ap.add_argument("--out", required=True, help="Output CSV (labels)")
    args = ap.parse_args()
    records = load_records(args.input)
    existing = index_existing(args.out)
    total = len(records)
    fout = open(args.out, "a", newline="", encoding="utf-8")
    fieldnames = ["label","reason","tags","title","authors","year","venue","doi","url","abstract"]
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    if not os.path.exists(args.out) or os.stat(args.out).st_size == 0:
        writer.writeheader()
    try:
        for i, rec in enumerate(records):
            key = (rec.get("doi") or "").strip().lower() or re.sub(r'[^a-z0-9]+', '', (rec.get("title") or "").lower())
            if key in existing: continue
            pretty_print(rec, i, total)
            while True:
                choice = input("[i]nclude / [e]xclude / [m]aybe / [s]kip / [q]uit > ").strip().lower()
                if choice in {"i","e","m","s","q"}: break
            if choice == "q": print("Exiting, progress saved."); return
            if choice == "s": continue
            reason = input("Reason (optional): ").strip()
            tags = input("Tags (comma-separated, optional): ").strip()
            label = {"i":"include","e":"exclude","m":"maybe"}[choice]
            row = {"label": label,"reason": reason,"tags": tags,"title": rec.get("title",""),
                   "authors": rec.get("authors",""),"year": rec.get("year",""),"venue": rec.get("venue",""),
                   "doi": rec.get("doi",""),"url": rec.get("url",""),"abstract": rec.get("abstract","")}
            writer.writerow(row); fout.flush()
    finally:
        fout.close()

if __name__ == "__main__":
    main()
