import { useEffect, useState } from 'react'
import { getDashboardSummary } from '../api/itsm'
import { Badge } from '../components/Badge'
import type { DashboardSummary, Ticket } from '../types/api'

export function OperationsDashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try { setData(await getDashboardSummary()) }
    catch (err) { setError(err instanceof Error ? err.message : 'Dashboard data unavailable.') }
    finally { setLoading(false) }
  }

  useEffect(() => { void load() }, [])

  return (
    <div className="page">
      <header className="topbar">
        <div><div className="eyebrow">OPERATIONS CONSOLE</div><h1>ITSM Operations</h1><p>Live visibility into ticket intake, AI resolution, escalation, and controlled automation.</p></div>
        <button className="secondary-button" onClick={() => void load()} disabled={loading}>↻ Refresh</button>
      </header>

      {error && <div className="alert error">{error}<span className="alert-hint">The dashboard requires the isolated Phase 12 backend endpoint.</span></div>}

      <section className="kpi-grid">
        <Kpi label="Total tickets" value={data?.total_tickets} icon="◈" />
        <Kpi label="Open tickets" value={data?.open_tickets} icon="○" />
        <Kpi label="AI resolved" value={data?.ai_resolved_tickets} icon="✦" tone="green" />
        <Kpi label="Escalated" value={data?.escalated_tickets} icon="!" tone="amber" />
        <Kpi label="Software requests" value={data?.software_requests} icon="▣" />
      </section>

      <section className="dashboard-grid">
        <div className="card automation-panel">
          <div className="section-heading"><div><span className="eyebrow">AUTOMATION</span><h3>Workflow health</h3></div><Badge tone="green">Controlled</Badge></div>
          <AutomationRow label="Password Reset" value={data?.automation.password_reset} />
          <AutomationRow label="Account Unlock" value={data?.automation.account_unlock} />
          <AutomationRow label="Software Provisioning" value={data?.automation.software_provisioning} />
          <div className="policy-note">Every automated action remains subject to backend policy, explicit consent, validation, ITSM correlation, and audit boundaries.</div>
        </div>

        <div className="card ticket-panel">
          <div className="section-heading"><div><span className="eyebrow">RECENT ACTIVITY</span><h3>Latest tickets</h3></div><Badge tone="blue">ITSM</Badge></div>
          <div className="ticket-list">
            {loading && <div className="empty">Loading operational data…</div>}
            {!loading && data?.recent_tickets.map((ticket) => <TicketRow key={ticket.ticket_id} ticket={ticket} />)}
            {!loading && !data?.recent_tickets.length && <div className="empty">No tickets yet.</div>}
          </div>
        </div>
      </section>

      <section className="card ai-visibility">
        <div className="section-heading"><div><span className="eyebrow">AI GOVERNANCE</span><h3>What reviewers can inspect</h3></div></div>
        <div className="visibility-grid">
          <Visibility title="Intent" text="Structured classification with deterministic routing." />
          <Visibility title="Confidence" text="Categorical confidence is surfaced instead of a fabricated probability." />
          <Visibility title="Knowledge" text="Grounded answers preserve retrieved source attribution." />
          <Visibility title="Automation" text="Actions stay behind consent, policy, validation, and audit." />
          <Visibility title="Escalation" text="Unknown requests can be explicitly converted into IT incidents." />
        </div>
      </section>
    </div>
  )
}

function Kpi({ label, value, icon, tone }: { label: string; value?: number; icon: string; tone?: 'green' | 'amber' }) {
  return <div className="kpi-card"><div className={`kpi-icon ${tone ?? ''}`}>{icon}</div><span>{label}</span><strong>{value ?? '—'}</strong></div>
}
function AutomationRow({ label, value }: { label: string; value?: number }) {
  return <div className="automation-row"><div><strong>{label}</strong><small>Persisted workflow executions</small></div><span>{value ?? '—'}</span></div>
}
function TicketRow({ ticket }: { ticket: Ticket }) {
  const tone = ticket.status === 'resolved' ? 'green' : ticket.status === 'escalated' ? 'amber' : ticket.status === 'failed' ? 'red' : 'blue'
  return <div className="ticket-row"><div className="ticket-id">{ticket.external_ticket_number ?? ticket.ticket_id}</div><div className="ticket-main"><strong>{ticket.title}</strong><small>{ticket.type} · {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '—'}</small></div><Badge tone={tone}>{ticket.status.replaceAll('_', ' ')}</Badge></div>
}
function Visibility({ title, text }: { title: string; text: string }) {
  return <div className="visibility-item"><span>✓</span><div><strong>{title}</strong><p>{text}</p></div></div>
}
