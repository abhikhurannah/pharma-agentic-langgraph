# Architecture and tradeoffs

See README for the data-flow diagram and setup.

`backend/config.py` loads validated environment settings. FastAPI lifespan owns one Qdrant client and compiled graph. Startup idempotently indexes the synthetic demo corpus. `retrieval.py` chunks abstracts, embeds title plus passage, and upserts stable UUIDs. A reentrant lock serializes access to embedded storage in thread-based API handlers. Remote Qdrant is supported through the same interface.

The graph has two explicit stages: retrieval and report. A fixed workflow does not pretend to perform autonomous planning. Retrieval is dense cosine similarity, followed by paper deduplication. Reports are either original excerpts or optional Gemini synthesis from those excerpts, with source ID checks and deterministic fallback. The UI renders plain text rather than model-produced HTML.

Collections are separated by embedding provider/model and chunking version. Updating a paper creates a new content identity; deletion/version reconciliation is not implemented. Only the top matching chunk from each retrieved paper is included; full-paper synthesis and cross-encoder reranking are future work. Local storage allows one API process; use server Qdrant for multiple workers. Warm startup re-embeds the small demo corpus; large ingestion should move to a background queue.

Tests use explicit hash embeddings to run without model downloads. The semantic encoder path must also be exercised when changing embedding dependencies. Citation checks validate source membership, not entailment. Synthetic benchmark numbers must not be presented as biomedical effectiveness.
