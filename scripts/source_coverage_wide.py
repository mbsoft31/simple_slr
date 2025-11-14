import os
import csv
import argparse
from collections import defaultdict


def pivot_long_to_wide(path_long: str, out_path: str) -> None:
    # Read long: cluster_id,source,count
    sources = set()
    by_cluster = defaultdict(dict)
    with open(path_long, 'r', encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            cid = row.get('cluster_id')
            src = (row.get('source') or '').lower()
            try:
                cnt = int(row.get('count') or '0')
            except ValueError:
                cnt = 0
            sources.add(src)
            by_cluster[cid][src] = cnt

    sources = sorted(s for s in sources if s)
    cols = ['cluster_id'] + [f'{s}_count' for s in sources]

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for cid in sorted(by_cluster.keys(), key=lambda x: int(x)):
            row = [cid]
            for s in sources:
                row.append(by_cluster[cid].get(s, 0))
            w.writerow(row)

    print(f"[coverage] wrote: {out_path} (sources: {', '.join(sources)})")


def main():
    ap = argparse.ArgumentParser(description='Pivot cluster_sources.csv to wide format.')
    ap.add_argument('--long', required=True, help='Path to cluster_sources.csv')
    ap.add_argument('--out', required=True, help='Output CSV path for wide coverage table')
    args = ap.parse_args()

    pivot_long_to_wide(args.long, args.out)


if __name__ == '__main__':
    main()

