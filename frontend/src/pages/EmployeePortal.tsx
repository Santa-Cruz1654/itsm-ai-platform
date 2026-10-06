import { useMemo, useState } from 'react'
import { analyzeRequest, askKnowledge, createEscalation, executeSelfHealing } from '../api/itsm'
import { Badge } from '../components/Badge'
import type { IntentWorkflowResponse, KnowledgeAnswer, SelfHealingResponse, SoftwareProvisioningResponse } from '../types/api'

const USER_ID = import.meta.env.VITE_DEMO_USER_ID ?? 'USR-DEMO-001'

const examples = [
  'My password has expired.',
  'My VPN is not connecting.',
  'How do I troubleshoot Outlook synchronization?',
  'I need Visual Studio Code installed on my laptop.',
  'How do I configure the company SAP production database replication?',
]

export function EmployeePortal() {
  const [request, setRequest] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [workflow, setWorkflow] = useState<IntentWorkflowResponse | null>(null)
  const [knowledge, setKnowledge] = useState<KnowledgeAnswer | null>(null)
  const [selfHealing, setSelfHealing] = useState<SelfHealingResponse | null>(null)

  const resetResult = () => {
    setWorkflow(null); setKnowledge(null); setSelfHealing(null); setError('')
  }

  const submit = async () => {
    const value = request.trim()
    if (!value || loading) return
    setLoading(true); resetResult()
    try {
      const result = await analyzeRequest({ employee_request: value, user_id: USER_ID })
      setWorkflow(result)
      if (result.analysis.intent === 'knowledge_question') setKnowledge(await askKnowledge(value))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to process the request.')
    } finally { setLoading(false) }
  }

  const runApprovedFix = async () => {
    if (!workflow || workflow.analysis.intent !== 'automatable_issue' || loading) return
    setLoading(true); setError('')
    try {
      setSelfHealing(await executeSelfHealing({ employee_request: request.trim(), user_id: USER_ID }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The approved automation could not be started.')
    } finally { setLoading(false) }
  }

  const escalate = async () => {
    if (!request.trim() || loading) return
    setLoading(true); setError('')
    try { setWorkflow(await createEscalation({ employee_request: request.trim(), user_id: USER_ID })) }
    catch (err) { setError(err instanceof Error ? err.message : 'Escalation could not be created.') }
    finally { setLoading(false) }
  }

  const confidenceTone = workflow?.analysis.confidence === 'high' ? 'green' : workflow?.analysis.confidence === 'medium' ? 'amber' : 'red'

  const actionDescription = useMemo(() => {
    if (!workflow) return ''
    switch (workflow.analysis.intent) {
      case 'automatable_issue':
        return 'This request is eligible for a controlled automation path. No action is executed until you explicitly approve it.'
      case 'knowledge_question':
        return 'The knowledge layer answers only from approved enterprise content and exposes supporting sources.'
      case 'service_request':
        return workflow.analysis.software_name
          ? `The request has been classified for approved software provisioning: ${workflow.analysis.software_name}.`
          : 'The request has been routed through the service-request workflow.'
      case 'incident':
        return 'The request has been routed through the ITSM incident boundary.'
      default:
        return 'The system could not establish a reliable supported workflow. Escalation prevents an invented answer.'
    }
  }, [workflow])

  const responseTicket = getTicketReference(workflow?.response)
  const workflowMessage = getMessage(workflow?.response)
  const workflowProvisioning =
    workflow?.analysis.intent === 'service_request'
      ? getProvisioningResponse(workflow.response)
      : null

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <div className="eyebrow">EMPLOYEE SELF-SERVICE</div>
          <h1>How can we help you?</h1>
          <p>Describe an IT problem or request in plain language. IT Assist will analyze it and route it safely.</p>
        </div>
        <div className="user-chip"><span>KR</span><div><strong>Employee</strong><small>{USER_ID}</small></div></div>
      </header>

      <section className="hero-card">
        <div className="hero-glow" />
        <div className="assistant-orb">✦</div>
        <div className="hero-copy">
          <span className="hero-kicker">AI SERVICE DESK</span>
          <h2>Tell us what went wrong.</h2>
          <p>One request can become knowledge assistance, an incident, a service request, an approved automation, or an explicit escalation.</p>
          <textarea
            value={request}
            onChange={(event) => setRequest(event.target.value)}
            onKeyDown={(event) => { if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') void submit() }}
            placeholder="Example: My VPN is not connecting..."
            disabled={loading}
          />
          <div className="composer-footer">
            <span>Ctrl/Cmd + Enter to submit</span>
            <button className="primary-button" onClick={() => void submit()} disabled={loading || !request.trim()}>
              {loading ? 'Analyzing…' : 'Analyze request →'}
            </button>
          </div>
        </div>
      </section>

      <div className="quick-prompts">
        <span>Demo scenarios</span>
        {examples.map((example) => (
          <button key={example} onClick={() => setRequest(example)} disabled={loading}>{example}</button>
        ))}
      </div>

      {error && <div className="alert error">{error}</div>}

      {workflow && (
        <>
          <section className="analysis-grid">
            <div className="card">
              <div className="section-heading">
                <div><span className="eyebrow">AI ANALYSIS</span><h3>Structured interpretation</h3></div>
                <Badge tone={confidenceTone}>{workflow.analysis.confidence} confidence</Badge>
              </div>
              <div className="analysis-fields">
                <InfoField label="Intent" value={workflow.analysis.intent.replaceAll('_', ' ')} />
                <InfoField label="Category" value={workflow.analysis.category} />
                <InfoField label="Subcategory" value={workflow.analysis.subcategory} />
                <InfoField label="Priority" value={workflow.analysis.priority} />
                <InfoField label="Impact" value={workflow.analysis.impact} />
                <InfoField label="Urgency" value={workflow.analysis.urgency} />
                <InfoField label="Assignment" value={workflow.analysis.assignment_group} />
                <InfoField label="Automation candidate" value={workflow.analysis.automation_candidate ? 'Yes' : 'No'} />
                <InfoField label="Software" value={workflow.analysis.software_name} />
              </div>
              <div className="summary-box"><span>SUMMARY</span><strong>{workflow.analysis.summary}</strong></div>
            </div>

            <div className="card action-card">
              <div>
                <span className="eyebrow">ROUTING DECISION</span>
                <h3>{workflow.decision.route.replaceAll('_', ' ')}</h3>
                <p>{actionDescription}</p>
              </div>
              <div className="decision-list">
                <DecisionRow label="Confirmation" value={workflow.decision.requires_confirmation ? 'Required' : 'Not required'} tone={workflow.decision.requires_confirmation ? 'amber' : 'green'} />
                <DecisionRow label="Human escalation" value={workflow.decision.requires_human_escalation ? 'Available' : 'Not required'} tone={workflow.decision.requires_human_escalation ? 'amber' : 'green'} />
                <DecisionRow label="Reason" value={workflow.decision.reason.replaceAll('_', ' ')} tone="blue" />
              </div>
              <div className="action-area">
                {workflow.analysis.intent === 'automatable_issue' && workflow.analysis.automation_candidate && (
                  <button className="primary-button full-width" onClick={() => void runApprovedFix()} disabled={loading}>
                    {loading ? 'Executing controlled workflow…' : 'Run approved fix'}
                  </button>
                )}
                {(workflow.analysis.intent === 'unknown' || workflow.decision.requires_human_escalation) && (
                  <button className="secondary-button full-width" onClick={() => void escalate()} disabled={loading}>
                    {loading ? 'Creating escalation…' : 'Create IT support ticket'}
                  </button>
                )}
              </div>
            </div>
          </section>

          {workflow.analysis.intent === 'knowledge_question' && knowledge && <KnowledgeCard data={knowledge} />}

          {(workflowMessage || responseTicket) && (
  <section className="card result-card">
    <div className="result-icon">i</div>
    <div>
      <span className="eyebrow">WORKFLOW RESPONSE</span>
      <h3>ITSM response</h3>

      <p>
        {workflowMessage ||
          'Your IT support incident was created successfully.'}
      </p>

      {responseTicket && (
        <div className="inline-result">
          <Badge tone="green">Ticket reference</Badge>
          <strong>{responseTicket}</strong>
        </div>
      )}
    </div>
  </section>
)}
          {selfHealing && <SelfHealingCard data={selfHealing} />}
          {workflowProvisioning && <ProvisioningCard data={workflowProvisioning} />}
        </>
      )}
    </div>
  )
}

function InfoField({ label, value }: { label: string; value: string | null | undefined }) {
  return <div className="info-field"><span>{label}</span><strong>{value || '—'}</strong></div>
}

function DecisionRow({ label, value, tone }: { label: string; value: string; tone: 'blue' | 'green' | 'amber' }) {
  return <div className="decision-row"><span>{label}</span><Badge tone={tone}>{value}</Badge></div>
}

function KnowledgeCard({ data }: { data: KnowledgeAnswer }) {
  return (
    <section className="card knowledge-card">
      <div className="section-heading">
        <div><span className="eyebrow">GROUNDED KNOWLEDGE</span><h3>{data.grounded ? 'Approved knowledge found' : 'No grounded answer'}</h3></div>
        <Badge tone={data.grounded ? 'green' : 'red'}>{data.confidence} confidence</Badge>
      </div>
      <p className="answer">{data.answer}</p>
      <div className="source-list">
        <span className="eyebrow">SOURCES</span>
        {!data.sources.length && <div className="empty">No approved knowledge sources were returned.</div>}
        {data.sources.map((source) => (
          <div className="source" key={`${source.document_id}-${source.chunk_id}`}>
            <div><strong>{source.title}</strong><small>{source.document_id} · {source.retrieval_method} · chunk {source.chunk_index}</small></div>
            <span>{source.score.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </section>
  )
}

function SelfHealingCard({ data }: { data: SelfHealingResponse }) {
  const successful = data.status === 'completed' || data.status === 'success' || data.automation_status === 'completed'
  const tone = successful ? 'green' : data.status.includes('escalat') ? 'amber' : 'red'
  return (
    <section className="card result-card">
      <div className={`result-icon ${tone}`}>⚙</div>
      <div className="result-grow">
        <div className="section-heading compact">
          <div><span className="eyebrow">CONTROLLED AUTOMATION</span><h3>{formatStatus(data.status)}</h3></div>
          <Badge tone={tone}>{formatStatus(data.automation_status ?? data.status)}</Badge>
        </div>
        <p>{data.message}</p>
        <div className="result-meta">
          {data.action && <span>Action: {data.action}</span>}
          {data.tool && <span>Tool: {data.tool}</span>}
          {data.external_ticket_number && <span>ITSM: {data.external_ticket_number}</span>}
        </div>
        {data.validation_checks.length > 0 && <div className="check-list">{data.validation_checks.map((check) => <span key={check}>✓ {check}</span>)}</div>}
      </div>
    </section>
  )
}

function ProvisioningCard({ data }: { data: SoftwareProvisioningResponse }) {
  const tone = data.status === 'completed' || data.status === 'resolved' ? 'green' : data.status.includes('fail') ? 'red' : 'blue'
  return (
    <section className="card result-card">
      <div className={`result-icon ${tone}`}>▣</div>
      <div className="result-grow">
        <div className="section-heading compact">
          <div><span className="eyebrow">SOFTWARE PROVISIONING</span><h3>{data.software_name}</h3></div>
          <Badge tone={tone}>{formatStatus(data.status)}</Badge>
        </div>
        <p>{data.message}</p>
        <div className="result-meta">
          <span>Request: {data.provisioning_request_id}</span>
          {data.external_request_number && <span>ITSM: {data.external_request_number}</span>}
        </div>
      </div>
    </section>
  )
}

function formatStatus(value: string) { return value.replaceAll('_', ' ') }

function getTicketReference(value: unknown): string {
  if (!value || typeof value !== 'object') return ''
  const object = value as Record<string, unknown>
  if (typeof object.external_ticket_number === 'string') return object.external_ticket_number
  if (typeof object.ticket_id === 'string') return object.ticket_id
  return ''
}

function getMessage(value: unknown): string {
  if (!value || typeof value !== 'object') return ''
  const object = value as Record<string, unknown>
  return typeof object.message === 'string' ? object.message : ''
}

function getProvisioningResponse(value: unknown): SoftwareProvisioningResponse | null {
  if (!value || typeof value !== 'object') return null
  const object = value as Record<string, unknown>
  if (
    typeof object.provisioning_request_id !== 'string' ||
    typeof object.software_name !== 'string' ||
    typeof object.status !== 'string' ||
    typeof object.message !== 'string'
  ) {
    return null
  }
  return value as SoftwareProvisioningResponse
}
