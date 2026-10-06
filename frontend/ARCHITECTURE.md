# Phase 11/12 Frontend Architecture

React only calls FastAPI. It never accesses MongoDB, Qdrant, ServiceNow, or automation tools directly.

Employee flow:
`POST /api/v1/intent`

Knowledge:
`POST /api/v1/knowledge/ask`

Knowledge inspection:
`POST /api/v1/knowledge/search`

Controlled self-healing:
`POST /api/v1/self-healing` only after explicit employee action.

Software:
`POST /api/v1/software-provisioning`

Escalation:
`POST /api/v1/intent` with `create_escalation_ticket=true`.

Dashboard:
`GET /api/v1/dashboard/summary`.

The dashboard values are backend-derived, not hard-coded in React.
