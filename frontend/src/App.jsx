import { useState } from 'react'
import './App.css'
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [drug, setDrug] = useState('Metformin')
  const [disease, setDisease] = useState("Alzheimer's")
  const [source, setSource] = useState('demo')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  async function submit(e) {
    e.preventDefault(); setLoading(true); setError(''); setResult(null)
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 90000)
    try {
      const response = await fetch(`${API}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ drug, disease, source, top_k: 5 }), signal: controller.signal })
      if (!response.ok) throw new Error(`Request failed (${response.status}). Check API health and inputs.`)
      setResult(await response.json())
    } catch (err) { setError(err.name === 'AbortError' ? 'Request timed out. Try again after checking backend health.' : err.message) }
    finally { clearTimeout(timer); setLoading(false) }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }))
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = `evidence-${result.request_id}.json`; anchor.click(); URL.revokeObjectURL(url)
  }
  return <main className="app">
    <header className="header"><div className="eyebrow">PHARMA / EVIDENCE LAB</div><h1>Explore research.<br />Trace every finding.</h1><p>A literature retrieval workspace powered by LangGraph and Qdrant.</p></header>
    <div className="container">
      <aside className="notice">Research demonstration, not clinical advice. The bundled corpus is synthetic; its findings and numbers are fictional.</aside>
      <form onSubmit={submit} className="input-form">
        <div className="form-group"><label htmlFor="drug">Drug</label><input id="drug" value={drug} onChange={e => setDrug(e.target.value)} minLength={2} maxLength={120} required /></div>
        <div className="form-group"><label htmlFor="disease">Disease or research target</label><input id="disease" value={disease} onChange={e => setDisease(e.target.value)} minLength={2} maxLength={160} required /></div>
        <div className="form-group"><label htmlFor="source">Evidence collection</label><select id="source" value={source} onChange={e => setSource(e.target.value)}><option value="demo">Synthetic demo</option><option value="uploaded">Uploaded literature</option><option value="all">All sources</option></select></div>
        <button disabled={loading}>{loading ? 'Analyzing…' : 'Explore evidence →'}</button>
      </form>
      {loading && <p role="status">Retrieving evidence and preparing the report. Execution timings will appear when complete.</p>}
      {error && <div role="alert" className="notice error">{error}</div>}
      {result && <div className="results">
        <section className="metrics" aria-label="Execution metrics"><div><strong>{result.papers.length}</strong>retrieved sources</div><div><strong>{result.duration_ms} ms</strong>total duration</div><div><strong>{result.generation_mode}</strong>report mode</div><div><strong>{result.embedding_backend}</strong>embeddings</div></section>
        {result.warnings.map(w => <p className="notice" key={w}>{w}</p>)}
        <div className="result-grid"><section><h2>Evidence trail</h2>{result.papers.length === 0 && <p>No passages passed the similarity threshold. Try another query or ingest relevant literature.</p>}
          {result.papers.map(p => <article className="card" key={p.citation_id} id={p.citation_id}><div className="eyebrow">[{p.citation_id}] · {p.source} · similarity {p.score}</div><h3>{p.title}</h3><p>{p.abstract}</p>{/^https?:\/\//i.test(p.link) && <a href={p.link} target="_blank" rel="noreferrer">Source publication ↗</a>}</article>)}
        </section><section><div className="report-heading"><h2>Research brief</h2><button onClick={download}>Export JSON</button><button onClick={() => window.print()}>Print / PDF</button></div><article className="card report">{result.final_report}</article>
          <details><summary>Execution trace</summary><p>Request: {result.request_id}</p>{result.trace.map(t => <p key={t.stage}>{t.stage}: {t.duration_ms} ms{t.count !== undefined ? ` · ${t.count} sources` : ''}</p>)}</details>
        </section></div>
      </div>}
    </div><footer>Similarity measures retrieval relevance, not clinical confidence. Citation validation checks identifiers, not factual entailment.</footer>
  </main>
}
