import { api } from './client'
import type {
  DashboardSummary,
  IntentWorkflowResponse,
  KnowledgeAnswer,
  KnowledgeSearchResponse,
  SelfHealingResponse,
  SoftwareCatalogItem,
  SoftwareProvisioningResponse,
  Ticket,
} from '../types/api'

export function analyzeRequest(input: {
  employee_request: string
  user_id: string
  consent_granted?: boolean
  consent_source?: 'explicit_user_request' | 'user_confirmation' | 'not_required'
  create_escalation_ticket?: boolean
}) {
  return api<IntentWorkflowResponse>('/api/v1/intent', {
    method: 'POST',
    body: JSON.stringify({
      consent_granted: false,
      consent_source: 'not_required',
      create_escalation_ticket: false,
      ...input,
    }),
  })
}

export function askKnowledge(query: string) {
  return api<KnowledgeAnswer>('/api/v1/knowledge/ask', {
    method: 'POST',
    body: JSON.stringify({ query, limit: 5 }),
  })
}

export function searchKnowledge(input: {
  query: string
  limit?: number
  mode?: 'dense' | 'keyword' | 'hybrid'
  category?: string
  subcategory?: string
}) {
  return api<KnowledgeSearchResponse>('/api/v1/knowledge/search', {
    method: 'POST',
    body: JSON.stringify({
      query: input.query,
      limit: input.limit ?? 10,
      mode: input.mode ?? 'hybrid',
      category: input.category ?? null,
      subcategory: input.subcategory ?? null,
    }),
  })
}

export function executeSelfHealing(input: {
  employee_request: string
  user_id: string
}) {
  return api<SelfHealingResponse>('/api/v1/self-healing', {
    method: 'POST',
    body: JSON.stringify({
      ...input,
      consent_granted: true,
      consent_source: 'explicit_user_request',
    }),
  })
}

export function createEscalation(input: {
  employee_request: string
  user_id: string
}) {
  return analyzeRequest({
    ...input,
    create_escalation_ticket: true,
  })
}

export function listTickets(userId: string) {
  return api<Ticket[]>(
    `/api/v1/tickets?user_id=${encodeURIComponent(userId)}`,
  )
}

export function getTicket(ticketId: string) {
  return api<Ticket>(`/api/v1/tickets/${encodeURIComponent(ticketId)}`)
}

export function listSoftwareCatalog() {
  return api<SoftwareCatalogItem[]>(
    '/api/v1/software-provisioning/catalog',
  )
}

export function requestSoftware(input: {
  user_id: string
  software_name: string
  employee_request: string
}) {
  return api<SoftwareProvisioningResponse>(
    '/api/v1/software-provisioning',
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  )
}

export function getProvisioningStatus(id: string) {
  return api<SoftwareProvisioningResponse>(
    `/api/v1/software-provisioning/${encodeURIComponent(id)}`,
  )
}

export function getDashboardSummary() {
  return api<DashboardSummary>('/api/v1/dashboard/summary')
}
