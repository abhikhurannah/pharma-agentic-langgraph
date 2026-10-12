"""Small synthetic retrieval smoke benchmark, not a clinical/quality benchmark."""
import json
import tempfile
from pathlib import Path
from backend.config import Settings
from backend.retrieval import Store

cases = [('aspirin cardiovascular', 'Aspirin and cardiovascular'), ('rapamycin autophagy', 'Rapamycin promotes'), ('statin cholesterol', 'Statin therapy')]
with tempfile.TemporaryDirectory() as directory:
    config = Settings(qdrant_path=directory)
    store = Store(config)
    try:
        store.ingest(json.loads(Path('data/mock_papers.json').read_text()), source='demo')
        ranks = []
        for query, expected in cases:
            hits = store.search(query, top_k=5)
            rank = next((i for i, hit in enumerate(hits, 1) if hit['title'].startswith(expected)), 0)
            ranks.append(rank)
        print(json.dumps({'dataset': 'synthetic smoke cases', 'cases': len(cases), 'embedding_backend': config.embedding_backend,
                          'hit_rate_at_5': sum(r > 0 for r in ranks)/len(ranks), 'mrr_at_5': sum(1/r if r else 0 for r in ranks)/len(ranks)}, indent=2))
    finally:
        store.close()
