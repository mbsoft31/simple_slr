import os
import csv
import json
import argparse
from typing import Dict, Any, List, Optional


def authors_from_raw(raw: Dict[str, Any]) -> List[str]:
    # Try various shapes
    a = raw.get('authors') or raw.get('author') or []
    out: List[str] = []
    if isinstance(a, list):
        for item in a:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                name = item.get('name') or item.get('display_name')
                given = item.get('given')
                family = item.get('family')
                if name:
                    out.append(str(name))
                elif given or family:
                    if given and family:
                        out.append(f"{given} {family}")
                    else:
                        out.append(str(given or family))
    elif isinstance(a, str):
        out.append(a)
    # OpenAlex authorships
    if not out and isinstance(raw.get('authorships'), list):
        for au in raw['authorships']:
            auth = au.get('author') or {}
            dn = auth.get('display_name')
            if dn:
                out.append(str(dn))
    return out


def main():
    ap = argparse.ArgumentParser(description='Prepare screening CSV from deduped.jsonl including title/abstract/authors.')
    ap.add_argument('--dedup-jsonl', required=True, help='Path to deduped.jsonl')
    ap.add_argument('--out', required=True, help='Output CSV path')
    ap.add_argument('--format', choices=['generic', 'rayyan', 'asreview'], default='generic')
    args = ap.parse_args()

    rows = []
    with open(args.dedup_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            raw = c.get('raw') or {}
            authors = authors_from_raw(raw)
            abstract = raw.get('abstract') or ''
            rows.append({
                'cluster_id': c.get('cluster_id'),
                'title': c.get('title') or '',
                'abstract': abstract,
                'authors': '; '.join(authors),
                'year': c.get('year') or '',
                'journal': c.get('venue') or '',
                'doi': c.get('doi') or '',
                'url': c.get('url') or '',
                'source': c.get('source') or '',
                'provider_id': c.get('provider_id') or '',
                'n_dois': len(c.get('dois_in_cluster') or []),
                'n_arxiv': len(c.get('arxiv_ids_in_cluster') or []),
                'size': len(c.get('members') or []),
                # empty columns for decisions
                'screener1_decision': '',
                'screener1_reason': '',
                'screener2_decision': '',
                'screener2_reason': '',
                'conflict_resolved_by': '',
                'final_decision': '',
                'final_reason': '',
            })

    # Select/export columns depending on target format
    if args.format == 'rayyan':
        cols = ['title', 'abstract', 'authors', 'journal', 'year', 'doi', 'url', 'cluster_id']
    elif args.format == 'asreview':
        cols = ['title', 'abstract', 'authors', 'year', 'doi', 'url', 'cluster_id']
    else:
        cols = [
            'cluster_id', 'title', 'abstract', 'authors', 'year', 'journal', 'doi', 'url',
            'source', 'provider_id', 'n_dois', 'n_arxiv', 'size',
            'screener1_decision', 'screener1_reason', 'screener2_decision', 'screener2_reason',
            'conflict_resolved_by', 'final_decision', 'final_reason'
        ]

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(k, '') for k in cols])

    print(f"[screening] wrote: {args.out} ({len(rows)} rows)")


if __name__ == '__main__':
    main()

