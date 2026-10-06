export type IntentType =
  | 'knowledge_question'
  | 'incident'
  | 'service_request'
  | 'automatable_issue'
  | 'unknown'

export type Confidence = 'low' | 'medium' | 'high'

export interface IntentAnalysis {
  intent: IntentType
  category: string | null
  subcategory: string | null
  priority: string | null
  impact: string | null
  urgency: string | null
  assignment_group: string | null
  summary: string
  confidence: Confidence
  automation_candidate: boolean
  software_name: string | null
}

export interface RoutingDecision {
  route: string
  reason: string
  requires_confirmation: boolean
  requires_human_escalation: boolean
}

export interface IntentWorkflowResponse {
  analysis: IntentAnalysis
  decision: RoutingDecision
  response: unknown
}

export interface Ticket {
  ticket_id: string
  user_id: string
  type: 'incident' | 'request'
  status: string
  title: string
  description: string
  category: string | null
  subcategory: string | null
  priority: string | null
  impact: string | null
  urgency: string | null
  assignment_group: string | null
  external_system: string | null
  external_ticket_id: string | null
  external_ticket_number: string | null
  external_sync_status: string
  external_sync_error: string | null
  created_at: string
  updated_at: string
  resolved_at: string | null
}

export interface KnowledgeSource {
  document_id: string
  chunk_id: string
  chunk_index: number
  title: string
  score: number
  retrieval_method: string
}

export interface KnowledgeAnswer {
  query: string
  answer: string
  grounded: boolean
  confidence: Confidence
  sources: KnowledgeSource[]
}

export interface KnowledgeSearchResult {
  chunk_id: string
  document_id: string
  content: string
  chunk_index: number
  heading_path: string[]
  title: string
  category: string
  subcategory: string
  version: string
  score: number
  dense_score?: number | null
  keyword_score?: number | null
  retrieval_method: string
}

export interface KnowledgeSearchResponse {
  query: string
  mode: string
  results: KnowledgeSearchResult[]
}

export interface SelfHealingResponse {
  status: string
  message: string
  action_id: string | null
  action: string | null
  tool: string | null
  diagnosis: string | null
  knowledge_sources: unknown[]
  automation_status: string | null
  validation_checks: string[]
  ticket_id: string | null
  external_ticket_id: string | null
  external_ticket_number: string | null
  audit_event_ids: string[]
}

export interface SoftwareCatalogItem {
  catalog_id: string
  name: string
  version: string
  category: string
  description: string
  aliases: string[]
  provisioning_supported: boolean
}

export interface SoftwareProvisioningResponse {
  provisioning_request_id: string
  software_name: string
  user_id: string
  status: string
  message: string
  created_at: string
  updated_at: string
  ticket_id: string | null
  external_request_id: string | null
  external_request_number: string | null
}

export interface DashboardSummary {
  total_tickets: number
  open_tickets: number
  ai_resolved_tickets: number
  escalated_tickets: number
  software_requests: number
  automation: {
    password_reset: number
    account_unlock: number
    software_provisioning: number
  }
  recent_tickets: Ticket[]
}
