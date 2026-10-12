import json
import logging
import secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models import QueryInput, IngestInput
from backend.retrieval import Store
from backend.graph import build_graph

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    store = Store()
    try:
        demo = json.loads((Path(__file__).resolve().parents[1] / 'data/mock_papers.json').read_text())
        store.ingest(demo, source='demo')
        app.state.store = store
        app.state.graph = build_graph(store)
        yield
    finally:
        store.close()


app = FastAPI(title='Pharma Evidence RAG', version='2.0.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings().cors_origins,
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'X-API-Key'])


@app.get('/health')
def health(request: Request):
    return {'status': 'ready', 'chunks': request.app.state.store.count(),
            'embedding_backend': settings().embedding_backend, 'generation_mode': settings().generation_mode}


@app.get('/')
def root():
    return {'name': 'Pharma Evidence RAG', 'docs': '/docs', 'health': '/health'}


@app.post('/ingest')
def ingest(body: IngestInput, request: Request, x_api_key: str = Header(default='')):
    key = settings().admin_api_key
    if not key:
        raise HTTPException(503, 'Set ADMIN_API_KEY to enable ingestion')
    if not secrets.compare_digest(x_api_key, key):
        raise HTTPException(401, 'Invalid ingestion credential')
    count = request.app.state.store.ingest([p.model_dump(mode='json') for p in body.papers])
    return {'chunks_upserted': count, 'total_chunks': request.app.state.store.count()}


@app.post('/run')
def run_query(body: QueryInput, request: Request):
    request_id = str(uuid.uuid4())
    start = perf_counter()
    try:
        result = request.app.state.graph.invoke(body.model_dump())
    except Exception:
        logger.exception('Analysis failed request_id=%s', request_id)
        raise HTTPException(503, detail={'message': 'Analysis unavailable', 'request_id': request_id})
    return {**result, 'request_id': request_id, 'duration_ms': round((perf_counter()-start)*1000),
            'embedding_backend': settings().embedding_backend}
