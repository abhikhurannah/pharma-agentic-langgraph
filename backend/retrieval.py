"""Persistent chunk-level vector retrieval with deterministic, idempotent ingestion."""
import hashlib
import math
import re
import threading
import uuid
from qdrant_client import QdrantClient, models
from backend.config import settings


def chunks(text, size=180, overlap=30):
    words = text.split()
    for start in range(0, len(words), size - overlap):
        yield ' '.join(words[start:start + size])
        if start + size >= len(words):
            break


class Store:
    def __init__(self, config=None):
        self.config = config or settings()
        self.lock = threading.RLock()
        self.encoder = None
        if self.config.embedding_backend == 'fastembed':
            from fastembed import TextEmbedding
            self.encoder = TextEmbedding(model_name=self.config.embedding_model)
            dimension = len(next(self.encoder.embed(['dimension probe'])))
        elif self.config.embedding_backend == 'hash':
            dimension = 384
        else:
            raise ValueError('EMBEDDING_BACKEND must be fastembed or hash')
        signature = hashlib.sha256(f'{self.config.embedding_backend}:{self.config.embedding_model}:chunks180-30:v1'.encode()).hexdigest()[:12]
        self.collection = f'papers_{signature}'
        self.client = QdrantClient(url=self.config.qdrant_url, api_key=self.config.qdrant_api_key or None, timeout=15) if self.config.qdrant_url else QdrantClient(path=self.config.qdrant_path)
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(self.collection, vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE))

    def embed(self, texts):
        if self.encoder:
            return [vector.tolist() for vector in self.encoder.embed(texts)]
        # Explicit offline baseline; not a semantic language model.
        vectors = []
        for text in texts:
            vector = [0.] * 384
            for token in re.findall(r'[a-z0-9]+', text.lower()):
                digest = hashlib.sha256(token.encode()).digest()
                vector[int.from_bytes(digest[:4], 'big') % 384] += 1
            norm = math.sqrt(sum(x*x for x in vector)) or 1
            vectors.append([x / norm for x in vector])
        return vectors

    def ingest(self, papers, source='uploaded'):
        points = []
        for paper in papers:
            content = f"{paper['title']}\n{paper['abstract']}"
            paper_id = hashlib.sha256(f'{source}:{content}'.encode()).hexdigest()
            passages = list(chunks(paper['abstract']))
            vectors = self.embed([paper['title'] + '\n' + p for p in passages])
            for i, (passage, vector) in enumerate(zip(passages, vectors)):
                points.append(models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f'{paper_id}:{i}')), vector=vector, payload={
                    'paper_id': paper_id, 'title': paper['title'], 'abstract': passage,
                    'link': str(paper.get('link') or '') if source != 'demo' else '',
                    'source': source, 'chunk_index': i,
                }))
        with self.lock:
            if points:
                self.client.upsert(self.collection, points=points, wait=True)
        return len(points)

    def search(self, query, top_k=5, source='all'):
        filters = None if source == 'all' else models.Filter(must=[models.FieldCondition(key='source', match=models.MatchValue(value=source))])
        with self.lock:
            hits = self.client.query_points(self.collection, query=self.embed([query])[0], query_filter=filters,
                limit=top_k * 8, score_threshold=self.config.min_score, with_payload=True).points
        result, seen = [], set()
        for hit in hits:
            p = hit.payload
            if p['paper_id'] in seen:
                continue
            seen.add(p['paper_id'])
            result.append({**p, 'score': round(hit.score, 4), 'citation_id': f'S{len(result)+1}'})
            if len(result) == top_k:
                break
        return result

    def count(self):
        with self.lock:
            return self.client.count(self.collection, exact=True).count

    def close(self):
        self.client.close()
