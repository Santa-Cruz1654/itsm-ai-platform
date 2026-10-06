import { useState } from 'react'
import { searchKnowledge } from '../api/itsm'
import { Badge } from '../components/Badge'
import type { KnowledgeSearchResult } from '../types/api'

const categories = [
  ['', 'All categories'],
  ['email', 'Email'],
  ['network', 'Network / VPN / Wi-Fi'],
  ['identity', 'Identity / Password'],
  ['authentication', 'Authentication'],
  ['mfa', 'MFA / Account Lockout'],
  ['laptop', 'Laptop / Device'],
  ['software', 'Software'],
  ['access', 'Application Access'],
] as const

export function KnowledgeBase() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [results, setResults] = useState<KnowledgeSearchResult[]>([])
  const [selected, setSelected] = useState<KnowledgeSearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runSearch = async () => {
    if (!query.trim() || loading) return
    setLoading(true); setError('')
    try {
      const response = await searchKnowledge({ query: query.trim(), category: category || undefined, limit: 10, mode: 'hybrid' })
      setResults(response.results)
      setSelected(response.results[0] ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Knowledge search failed.')
    } finally { setLoading(false) }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <div className="eyebrow">KNOWLEDGE MANAGEMENT</div>
          <h1>Enterprise Knowledge Base</h1>
          <p>Inspect approved knowledge retrieval independently from the employee chatbot. Results come directly from the backend retrieval API.</p>
        </div>
      </header>

      <section className="card kb-search-card">
        <div className="search-row">
          <input className="search-input" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void runSearch() }} placeholder="Search approved IT knowledge…" />
          <select className="select-input" value={category} onChange={(event) => setCategory(event.target.value)}>
            {categories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <button className="primary-button" onClick={() => void runSearch()} disabled={loading || !query.trim()}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
        <div className="search-note">Hybrid retrieval combines semantic and lexical evidence. This screen never generates knowledge.</div>
      </section>

      {error && <div className="alert error">{error}</div>}

      <section className="kb-grid">
        <div className="card">
          <div className="section-heading">
            <div><span className="eyebrow">RETRIEVAL RESULTS</span><h3>{results.length} result{results.length === 1 ? '' : 's'}</h3></div>
            <Badge tone="blue">Hybrid</Badge>
          </div>
          <div className="kb-results">
            {!results.length && !loading && <div className="empty">Search for an approved IT topic to inspect retrieval results.</div>}
            {results.map((result) => (
              <button className={`kb-result ${selected?.chunk_id === result.chunk_id ? 'selected' : ''}`} key={result.chunk_id} onClick={() => setSelected(result)}>
                <div className="kb-result-top"><strong>{result.title}</strong><span>{result.score.toFixed(3)}</span></div>
                <small>{result.category} · {result.subcategory} · {result.retrieval_method}</small>
                <p>{result.content.slice(0, 180)}{result.content.length > 180 ? '…' : ''}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="card kb-detail">
          <div className="section-heading">
            <div><span className="eyebrow">ARTICLE / CHUNK</span><h3>{selected?.title ?? 'Select a result'}</h3></div>
            {selected && <Badge tone="green">Retrieved</Badge>}
          </div>
          {!selected ? <div className="empty">The selected knowledge chunk will appear here.</div> : (
            <>
              <div className="detail-metadata">
                <Meta label="Category" value={selected.category} />
                <Meta label="Subcategory" value={selected.subcategory} />
                <Meta label="Version" value={selected.version} />
                <Meta label="Score" value={selected.score.toFixed(3)} />
                <Meta label="Method" value={selected.retrieval_method} />
                <Meta label="Chunk" value={String(selected.chunk_index)} />
              </div>
              <div className="article-content">{selected.content}</div>
            </>
          )}
        </div>
      </section>
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><strong>{value || '—'}</strong></div>
}
