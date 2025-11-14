import os
import csv
import json
import argparse
from typing import Dict, Tuple


def count_lines_jsonl(path: str) -> int:
    n = 0
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def count_rows_csv(path: str) -> int:
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        r = csv.reader(f)
        try:
            header = next(r)
        except StopIteration:
            return 0
        return sum(1 for _ in r)


def provider_from_run_dir(dirname: str) -> str:
    # e.g., "openalex_run_20251114_023358" -> "openalex"
    base = os.path.basename(dirname).lower()
    if '_run_' in base:
        return base.split('_run_', 1)[0]
    # fallback: look for known provider names
    for p in ('openalex', 'crossref', 'arxiv', 's2', 'semanticscholar'):
        if p in base:
            return 's2' if p == 'semanticscholar' else p
    return base


def collect_identified_counts(raw_dir: str) -> Tuple[int, Dict[str, int]]:
    by_source: Dict[str, int] = {}
    total = 0
    # Walk immediate subdirs of raw_dir
    for root, dirs, files in os.walk(raw_dir):
        # Only consider leaf run dirs that contain provider results
        if not files:
            continue
        # Prefer all_results.* if present to avoid double-counting CSV+JSONL per query
        ar_jsonl = os.path.join(root, 'all_results.jsonl')
        ar_csv = os.path.join(root, 'all_results.csv')
        if os.path.exists(ar_jsonl) or os.path.exists(ar_csv):
            src = provider_from_run_dir(root)
            cnt = 0
            if os.path.exists(ar_jsonl):
                cnt = count_lines_jsonl(ar_jsonl)
            elif os.path.exists(ar_csv):
                cnt = count_rows_csv(ar_csv)
            if cnt:
                by_source[src] = by_source.get(src, 0) + cnt
                total += cnt
            continue
    return total, by_source


def load_dedup_counts(dedup_dir: str) -> Tuple[int, int]:
    members_csv = os.path.join(dedup_dir, 'members.csv')
    clusters_csv = os.path.join(dedup_dir, 'clusters.csv')
    if not (os.path.exists(members_csv) and os.path.exists(clusters_csv)):
        raise FileNotFoundError('Expected members.csv and clusters.csv in dedup_dir')
    members = count_rows_csv(members_csv)
    clusters = count_rows_csv(clusters_csv)
    return members, clusters


def main():
    ap = argparse.ArgumentParser(description='Compute PRISMA-style counts from raw and deduplicated outputs.')
    ap.add_argument('--raw-dir', required=True, help='Root directory containing provider run outputs (e.g., outputs)')
    ap.add_argument('--dedup-dir', required=True, help='Directory containing dedup results (clusters.csv, members.csv)')
    ap.add_argument('--out-dir', default=None, help='Where to write counts (default: dedup-dir)')
    args = ap.parse_args()

    out_dir = args.out_dir or args.dedup_dir
    os.makedirs(out_dir, exist_ok=True)

    records_identified_total, by_source = collect_identified_counts(args.raw_dir)
    members, clusters = load_dedup_counts(args.dedup_dir)
    duplicates_removed = max(0, members - clusters)

    summary = {
        'records_identified_total': records_identified_total,
        'records_identified_by_source': by_source,
        'dedup_members_count': members,
        'dedup_clusters_count': clusters,
        'duplicates_removed': duplicates_removed,
        'records_after_dedup': clusters,
        # Fill these after screening
        'screening': {
            'title_abstract_screened': None,
            'title_abstract_excluded': None,
            'full_text_screened': None,
            'full_text_excluded': None,
            'included': None,
        },
    }

    # JSON summary
    with open(os.path.join(out_dir, 'prisma_counts.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # CSV summaries
    with open(os.path.join(out_dir, 'prisma_summary.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value'])
        w.writerow(['records_identified_total', records_identified_total])
        w.writerow(['dedup_members_count', members])
        w.writerow(['dedup_clusters_count', clusters])
        w.writerow(['duplicates_removed', duplicates_removed])
        w.writerow(['records_after_dedup', clusters])

    with open(os.path.join(out_dir, 'prisma_by_source.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['source', 'count'])
        for src, cnt in sorted(by_source.items()):
            w.writerow([src, cnt])

    print(f"[prisma] wrote: {out_dir}/prisma_counts.json, prisma_summary.csv, prisma_by_source.csv")


if __name__ == '__main__':
    main()

