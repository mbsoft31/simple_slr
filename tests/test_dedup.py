from enhanced_query_script import global_dedup

def test_global_dedup_doi_and_title():
    recs = [
        {"title": "Paper A", "doi": "10.1000/xyz", "venue": "arXiv", "provider": "arXiv"},
        {"title": "Paper A", "doi": "https://doi.org/10.1000/xyz", "venue": "Journal X", "provider": "Crossref"},
        {"title": "Paper B", "doi": "", "venue": "Conference Y", "provider": "Crossref"},
        {"title": "paper b", "doi": "", "venue": "arXiv", "provider": "arXiv"},
    ]
    dedup = global_dedup(recs)
    assert len(dedup) == 2
    titles_venues = {r["title"].lower(): r["venue"] for r in dedup}
    assert titles_venues["paper a"] == "Journal X"
