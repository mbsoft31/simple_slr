#!/usr/bin/env python3
import os, csv, json, argparse, re
from typing import Dict, Any, List
try:
    import pandas as pd
except Exception:
    pd = None

def load_records(path: str) -> List[Dict[str,Any]]:
    recs = []
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try: recs.append(json.loads(line))
                except Exception: continue
    else:
        if pd is None:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f); recs.extend(list(reader))
        else:
            df = pd.read_csv(path); recs = df.to_dict(orient="records")
    return recs

def first_author_last(authors_field: Any) -> str:
    if not authors_field: return "anon"
    if isinstance(authors_field, str):
        first = authors_field.split(";")[0].strip()
        parts = first.split()
        return re.sub(r'[^A-Za-z]+','', parts[-1]) if parts else "anon"
    elif isinstance(authors_field, list) and authors_field:
        parts = (authors_field[0] or "").split()
        return re.sub(r'[^A-Za-z]+','', parts[-1]) if parts else "anon"
    return "anon"

def title_stub(title: str) -> str:
    title = (title or "").lower()
    title = re.sub(r'[^a-z0-9 ]+','', title)
    words = [w for w in title.split() if len(w) >= 4]
    return (words[0] if words else "paper")

def make_key(rec: Dict[str,Any]) -> str:
    fa = first_author_last(rec.get("authors")); yr = str(rec.get("year") or "n.d.")
    stub = title_stub(rec.get("title","")); return f"{fa}{yr}{stub}".replace(" ", "")

def escape_braces(s: str) -> str: return s.replace("{","\\{").replace("}","\\}")

def entry_type(rec: Dict[str,Any]) -> str:
    venue = (rec.get("venue") or "").lower()
    if "arxiv" in venue: return "misc"
    if any(x in venue for x in ["journal", "trans.", "ieee", "nature", "springer", "elsevier"]): return "article"
    if any(x in venue for x in ["conf", "conference", "proceedings", "proc."]): return "inproceedings"
    return "article" if venue else "misc"

def to_bibtex(rec: Dict[str,Any]) -> str:
    t = entry_type(rec); key = make_key(rec)
    title = escape_braces(rec.get("title",""))
    authors = rec.get("authors","")
    if isinstance(authors, list): authors = " and ".join(authors)
    else: authors = " and ".join([a.strip() for a in authors.split(";") if a.strip()])
    year = rec.get("year",""); venue = rec.get("venue","")
    doi = rec.get("doi",""); url = rec.get("url","")
    lines = [f"@{t}{{{key},", f"  title = {{{title}}},"]
    if authors: lines.append(f"  author = {{{authors}}},")
    if year: lines.append(f"  year = {{{year}}},")
    if t == "article" and venue: lines.append(f"  journal = {{{escape_braces(venue)}}},")
    if t == "inproceedings" and venue: lines.append(f"  booktitle = {{{escape_braces(venue)}}},")
    if "arxiv" in (venue or "").lower():
        m = re.search(r'arxiv\.org/(abs|pdf)/([0-9]+\.[0-9]+)', url)
        if m:
            lines.append(f"  eprint = {{{m.group(2)}}},"); lines.append("  archivePrefix = {arXiv},"); lines.append("  primaryClass = {cs.CV},")
    if doi: lines.append(f"  doi = {{{doi}}},")
    if url: lines.append(f"  url = {{{url}}},")
    lines.append("}\n"); return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    recs = load_records(args.input)
    seen = set()
    with open(args.out, "w", encoding="utf-8") as f:
        for r in recs:
            key = make_key(r)
            if key in seen: continue
            seen.add(key); f.write(to_bibtex(r))
    print(f"Wrote {args.out} with {len(seen)} entries.")

if __name__ == "__main__":
    main()
