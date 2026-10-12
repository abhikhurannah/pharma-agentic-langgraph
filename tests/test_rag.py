import pytest
from fastapi.testclient import TestClient
from backend.config import Settings, settings
from backend.retrieval import Store, chunks
from backend.tools import generate_report

PAPERS = [{'title': 'Aspirin cardiovascular research', 'abstract': 'Aspirin cardiovascular prevention research in adults with cardiovascular disease.'}, {'title': 'Metformin cognitive study', 'abstract': 'Metformin Alzheimer cognitive memory brain research in animal models.'}]

@pytest.fixture
def store(tmp_path):
    instance = Store(Settings(qdrant_path=str(tmp_path / 'vectors'), embedding_backend='hash', min_score=0.1))
    yield instance
    instance.close()


def test_idempotent_ingestion_and_ranking(store):
    store.ingest(PAPERS)
    count = store.count()
    store.ingest(PAPERS)
    assert store.count() == count
    hits = store.search('Aspirin cardiovascular')
    assert hits[0]['title'] == PAPERS[0]['title']
    assert hits[0]['citation_id'] == 'S1'
    assert store.search('Aspirin', source='demo') == []


def test_persistence(tmp_path):
    config = Settings(qdrant_path=str(tmp_path / 'persistent'), embedding_backend='hash')
    first = Store(config)
    first.ingest(PAPERS)
    first.close()
    second = Store(config)
    assert second.count() == 2
    second.close()


def test_chunks_and_no_evidence():
    text = ' '.join(f'w{i}' for i in range(400))
    parts = list(chunks(text))
    assert parts[0].split()[-30:] == parts[1].split()[:30]
    assert parts[-1].endswith('w399')
    assert generate_report({'papers': []})[1] == 'abstained'


def test_api(tmp_path, monkeypatch):
    monkeypatch.setenv('QDRANT_PATH', str(tmp_path / 'api'))
    monkeypatch.setenv('EMBEDDING_BACKEND', 'hash')
    monkeypatch.setenv('GENERATION_MODE', 'extractive')
    monkeypatch.setenv('ADMIN_API_KEY', 'test-secret')
    settings.cache_clear()
    from backend.main import app
    with TestClient(app) as client:
        assert client.get('/health').json()['chunks'] >= 10
        assert client.post('/run', json={'drug': ' ', 'disease': 'x'}).status_code == 422
        assert client.post('/run', json={'drug': 'Aspirin', 'disease': 'cardiovascular', 'top_k': 99}).status_code == 422
        assert client.post('/ingest', json={'papers': PAPERS}).status_code == 401
        assert client.post('/ingest', json={'papers': PAPERS}, headers={'X-API-Key': 'test-secret'}).status_code == 200
        result = client.post('/run', json={'drug': 'Aspirin', 'disease': 'cardiovascular', 'source': 'uploaded'}).json()
        assert result['papers'][0]['source'] == 'uploaded'
        assert '[S1]' in result['final_report']
        assert result['generation_mode'] == 'extractive'
        assert len(result['trace']) == 2
    settings.cache_clear()


def test_missing_key_falls_back(monkeypatch):
    monkeypatch.setenv('GENERATION_MODE', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', '')
    settings.cache_clear()
    paper = {**PAPERS[0], 'citation_id': 'S1', 'source': 'uploaded'}
    report, mode, warnings = generate_report({'papers': [paper], 'drug': 'Aspirin', 'disease': 'cardiovascular'})
    assert mode == 'extractive_fallback' and warnings and '[S1]' in report
    settings.cache_clear()

@pytest.mark.parametrize('answer,expected', [('Unsupported [S99]', 'extractive_fallback'), ('No citations', 'extractive_fallback'), ('Evidence [S1]', 'gemini')])
def test_provider_citation_validation(monkeypatch, answer, expected):
    from google import genai
    from types import SimpleNamespace
    class FakeClient:
        def __init__(self, **kwargs):
            self.models = SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text=answer))
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(genai, 'Client', FakeClient)
    monkeypatch.setenv('GENERATION_MODE', 'gemini')
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-test-key')
    settings.cache_clear()
    paper = {**PAPERS[0], 'citation_id': 'S1', 'source': 'uploaded'}
    assert generate_report({'papers': [paper], 'drug': 'Aspirin', 'disease': 'cardiovascular'})[1] == expected
    settings.cache_clear()


def test_demo_links_suppressed(store):
    store.ingest([{**PAPERS[0], 'link': 'https://example.org/fake'}], source='demo')
    assert store.search('Aspirin cardiovascular', source='demo')[0]['link'] == ''
