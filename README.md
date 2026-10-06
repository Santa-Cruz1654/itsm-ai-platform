# ITSM AI Platform

An enterprise-style AI-powered IT Service Management (ITSM) prototype that connects employee requests with intelligent intent classification, knowledge retrieval, controlled automation, software provisioning workflows, and ITSM ticket management.

The project demonstrates the following end-to-end journey:

**Employee Request -> AI Understanding -> Knowledge Retrieval -> Intelligent Decision -> Automation -> ITSM -> Resolution**

> **Prototype scope:** This project demonstrates enterprise workflow design, AI integration, RAG, controlled automation, API integration, and safety mechanisms. It is not intended to be production-ready ITSM infrastructure.

---

## 1. Capabilities

The prototype implements five major capabilities:

1. **Intelligent Ticket Intake**
2. **Auto Resolution / Self-Healing**
3. **Knowledge Management Automation**
4. **Self-Service Portal & Chatbot**
5. **Software Provisioning Automation**

### Core technologies

- React + TypeScript + Vite
- Python + FastAPI
- MongoDB-compatible persistence
- Hugging Face models
- Qdrant vector database
- Dense + BM25 hybrid retrieval
- Mock ServiceNow-compatible ITSM integration
- Mock password-reset automation
- Mock software-provisioning automation
- Audit logging
- Deterministic confidence and safety gates

---

# 2. Architecture

```text
                         +----------------+
                         |    Employee    |
                         +-------+--------+
                                 |
                                 v
                         +----------------+
                         | React Frontend |
                         | Self-Service UI|
                         +-------+--------+
                                 |
                              REST API
                                 |
                                 v
                         +----------------+
                         | FastAPI Backend|
                         +-------+--------+
                                 |
                 +---------------+---------------+
                 |               |               |
                 v               v               v
          +------------+   +-----------+   +-------------+
          | AI Intent  |   | Knowledge |   | Workflow    |
          | Analysis   |   | Retrieval |   | Orchestrator|
          +-----+------+   +-----+-----+   +------+------+
                |                |
                |         +------+------+
                |         |             |
                |         v             v
                |    Dense Search    BM25 Search
                |         |             |
                |         +------+------+
                |                |
                |                v
                |        +---------------+
                |        | RRF Hybrid    |
                |        | Retrieval     |
                |        +-------+-------+
                |                |
                |                v
                |          +-----------+
                |          |  Qdrant   |
                |          | Vector DB |
                |          +-----------+
                |
                v
        +----------------------+
        | Confidence & Safety  |
        | Gates / Deterministic|
        | Routing              |
        +----------+-----------+
                   |
       +-----------+-----------+----------------+
       |           |           |                |
       v           v           v                v
+----------+ +----------+ +-----------+ +---------------+
| Incident | | Self-    | | Software  | | Knowledge     |
| Workflow | | Healing  | | Provision | | Response      |
+----+-----+ +----+-----+ +-----+-----+ +---------------+
     |            |             |
     v            v             v
+----------+ +----------+ +---------------+
| Mock ITSM | | Mock     | | Mock Software |
| / Service | | Password | | Provisioning  |
| Now       | | Reset    | | Service       |
+-----------+ +----------+ +---------------+

                   |
                   v
          +-------------------+
          | MongoDB           |
          | Application Data  |
          +-------------------+

                   |
                   v
          +-------------------+
          | Audit Logging     |
          | & Traceability    |
          +-------------------+
```

---

# 3. Technology Stack

## Frontend

- React
- TypeScript
- Vite
- CSS

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- Pydantic Settings
- PyMongo

## AI / Machine Learning

- Hugging Face Transformers
- `Qwen/Qwen3-1.7B` for grounded response generation
- `Alibaba-NLP/gte-modernbert-base` for embeddings
- Sentence Transformers
- PyTorch

## Knowledge Retrieval

- Qdrant
- Dense vector retrieval
- BM25 sparse retrieval
- Hybrid retrieval
- Reciprocal Rank Fusion (RRF)
- Semantic chunking

## ITSM / Automation

- Mock ServiceNow-compatible ITSM client
- Mock password-reset tool
- Mock software-provisioning client

---

# 4. Repository Structure

```text
itsm/

 README.md

 backend/
    app/
       api/
       application/
       config/
       domain/
       infrastructure/

    evaluation/
       retrieval/

    knowledge/
       access/
       laptop/
       mfa/
       outlook/
       password/
       software/
       vpn/
       wifi/

    tests/
    .env.example
    .gitignore
    .python-version
    pyproject.toml
    README.md
    uv.lock

 frontend/
    src/
    .env.example
    ARCHITECTURE.md
    index.html
    package.json
    package-lock.json
    README.md
    tsconfig.app.json
    tsconfig.json
    tsconfig.node.json
    vite.config.ts
```

The local `.env` file is intentionally not listed because it is environment-specific configuration and should not be committed.

---

# 5. Intelligent Ticket Intake

Employees submit requests in natural language.

The backend processes the request through:

```text
Employee Request
       |
       v
AI Intent Analysis
       |
       v
Confidence Evaluation
       |
       v
Deterministic Intent Router
       |
       v
Appropriate Workflow
```

Supported intent categories include:

- Knowledge Question
- Incident
- Service Request
- Automatable Issue
- Unknown

### Confidence routing

| Confidence | Behaviour |
|---|---|
| High | Route to the appropriate workflow |
| Medium | Require confirmation |
| Low | Escalate to human support |
| Unknown | Escalate rather than guess |

Unknown requests do not automatically enter knowledge retrieval or automation workflows.

---

# 6. VPN Incident Workflow

Example:

```text
My VPN is not connecting.
```

The system can classify the request as an incident and enrich the ticket with ITSM information such as:

- Incident type
- Network / VPN category
- Priority
- Impact
- Urgency
- Assignment group
- Request summary
- Suggested resolution

Workflow:

```text
Employee
   |
   v
AI Intent Analysis
   |
   v
Incident
   |
   v
Ticket Service
   |
   v
ITSM / ServiceNow-compatible Client
   |
   v
Incident Created
```

The current implementation uses a mock ITSM client.

---

# 7. Auto Resolution / Self-Healing

Password expiry demonstrates controlled automation.

Example:

```text
My password has expired.
```

The workflow follows:

```text
Identify
   |
   v
Diagnose
   |
   v
Knowledge Search
   |
   v
Determine Automation
   |
   v
Safety / Authorization Check
   |
   v
Execute Approved Action
   |
   v
Validate
   |
   v
Audit
   |
   v
Update ITSM
```

The password-reset operation uses a mock automation tool.

Safety checks include:

- User authorization
- Consent
- Approved automation policy
- Knowledge-backed diagnosis
- Validation
- Audit logging

Automated actions are recorded through the audit mechanism.

If automation cannot safely complete the operation, the workflow can move toward incident creation or escalation.

---

# 8. Knowledge Management and RAG

The knowledge subsystem demonstrates a complete retrieval-augmented generation pipeline:

```text
Documents
    |
    v
Markdown Parsing
    |
    v
Semantic Chunking
    |
    v
Embedding Generation
    |
    v
Qdrant
    |
    v
Hybrid Retrieval
    |
    +----------------------+
    |                      |
    v                      v
Dense Retrieval       BM25 Sparse Retrieval
    |                      |
    +----------+-----------+
               |
               v
Reciprocal Rank Fusion
               |
               v
Grounding Gate
               |
               v
Bounded Context
               |
               v
LLM
               |
               v
Grounded Answer + Sources
```

The current knowledge base contains eight documents covering:

- Application access
- Laptop performance
- MFA/account lockout
- Outlook synchronization
- Password reset
- Software installation
- VPN troubleshooting
- Wi-Fi troubleshooting

RAG responses expose retrieved knowledge sources so users can see the documentation supporting the answer.

---

# 9. Grounding and Hallucination Safety

The language model is not treated as the source of truth for enterprise-specific knowledge.

The system first retrieves relevant documentation and applies a grounding decision before generating the response.

```text
User Question
      |
      v
Knowledge Retrieval
      |
      v
Sufficient Knowledge?
    /       \
  Yes        No
   |          |
   v          v
Grounded    Clarify /
LLM Answer  Escalate
   |
   v
Sources Returned
```

When sufficient knowledge is unavailable, the intended behaviour is to avoid fabricating an enterprise-specific answer and move toward clarification or escalation.

Confidence thresholds also prevent uncertain intent classifications from directly triggering sensitive workflows.

---

# 10. Self-Service Portal

The React frontend provides three primary areas.

## Employee Portal

Example requests:

```text
My password has expired.
```

```text
My VPN is not connecting.
```

```text
How do I troubleshoot Outlook synchronization?
```

```text
I need Visual Studio Code installed on my laptop.
```

The portal displays the AI interpretation and selected workflow.

## Knowledge Base

Provides knowledge search and grounded answers with supporting sources.

## ITSM Operations

Provides the operational dashboard and ticket/workflow information returned by the backend.

---

# 11. Software Provisioning

Example:

```text
I need Visual Studio Code installed on my laptop.
```

Workflow:

```text
Employee Request
      |
      v
AI Intent
      |
      v
Software Catalogue
      |
      v
ITSM Service Request
      |
      v
Mock Provisioning API
      |
      v
Provisioning Status
```

The approved prototype catalogue includes:

- Visual Studio Code
- Git
- Postman
- 7-Zip
- Notepad++

Actual software installation is intentionally not performed.

The provisioning integration demonstrates the enterprise workflow using a mock provisioning service.

---

# 12. ITSM / ServiceNow Integration

The project defines an ITSM client abstraction so application workflows are not tightly coupled to one vendor implementation.

The current prototype uses a stateful mock ServiceNow-compatible client.

Supported operations include:

- Create Incident
- Create Service Request
- Get Ticket
- Update Ticket

A live ServiceNow instance is **not required** for the prototype.

---

# 13. MongoDB

MongoDB is used as the application persistence layer.

Configuration is supplied through environment variables rather than hard-coded connection details.

The backend configuration currently supports:

```text
APP_NAME
ENVIRONMENT
DEBUG
MONGODB_URI
MONGODB_DATABASE
```

Example configuration is provided in:

```text
backend/.env.example
```

Default example values are:

```env
APP_NAME=ITSM AI Platform
ENVIRONMENT=development
DEBUG=true
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=itsm
```

The project can be configured for MongoDB Atlas or another MongoDB deployment by changing the environment configuration.

---

# 14. API Overview

The FastAPI backend exposes versioned APIs under:

```text
/api/v1
```

Important endpoints include:

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/intent` | Analyze and route an employee request |
| `POST /api/v1/knowledge/search` | Search the knowledge base |
| `POST /api/v1/knowledge/ask` | Generate a grounded knowledge answer |
| `POST /api/v1/self-healing` | Execute the self-healing workflow |
| `/api/v1/software-provisioning/...` | Software catalogue and provisioning operations |
| `/api/v1/tickets/...` | Ticket operations |
| `GET /api/v1/dashboard/summary` | ITSM dashboard aggregation |

The FastAPI implementation is the source of truth for the complete route and schema definitions.

---

# 15. Configuration

## Backend

Copy the example configuration:

```powershell
cd backend
Copy-Item .env.example .env
```

Adjust the values for the local environment.

Do not commit real credentials or secrets.

## Frontend

The frontend provides:

```text
frontend/.env.example
```

The frontend API configuration supports the Vite environment variable:

```text
VITE_API_BASE_URL
```

The development setup uses the Vite proxy to forward `/api` requests to the backend.

---

# 16. Running the Backend

Requirements:

- Python 3.12+
- MongoDB-compatible database
- Qdrant
- Sufficient local resources for the Hugging Face models

Create a Python environment:

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e .
```

Start FastAPI:

```powershell
uvicorn app.main:app --reload --port 8000
```

API:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

# 17. Running the Frontend

Install dependencies:

```powershell
cd frontend
npm install
```

Start the development server:

```powershell
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

The Vite development configuration proxies `/api` requests to the backend.

---

# 18. Knowledge Base

Knowledge documents are stored under:

```text
backend/knowledge/
```

The current knowledge base contains eight documents.

The ingestion pipeline processes the Markdown documents, creates chunks and embeddings, and stores the resulting vectors in Qdrant.

The vector store configuration is environment-dependent and should not contain hard-coded credentials.

---

# 19. Testing

The backend contains tests covering:

- API behaviour
- Intent analysis
- Intent routing
- Intent workflow orchestration
- Ticket services
- ITSM client behaviour
- Knowledge retrieval
- RAG answer generation
- Self-healing
- Software catalogue
- Software provisioning
- Repository behaviour
- Audit behaviour

Final backend validation:

```text
205 passed
```

The frontend production build was also successfully validated with:

```powershell
npm run build
```

---

# 20. Demo Scenarios

## Scenario 1 - VPN Incident

Input:

```text
My VPN is not connecting.
```

Demonstrates:

```text
Intent
   |
   v
Incident
   |
   v
Ticket
   |
   v
ITSM
```

## Scenario 2 - Password Self-Healing

Input:

```text
My password has expired.
```

Demonstrates:

```text
Identify
   |
   v
Diagnose
   |
   v
Knowledge Search
   |
   v
Automation Decision
   |
   v
Approved Action
   |
   v
Validation
   |
   v
Audit
```

## Scenario 3 - Outlook RAG

Input:

```text
How do I troubleshoot Outlook synchronization?
```

Demonstrates:

```text
Intent
   |
   v
RAG
   |
   v
Grounded Answer
   |
   v
Sources
```

## Scenario 4 - Software Provisioning

Input:

```text
I need Visual Studio Code installed on my laptop.
```

Demonstrates:

```text
Intent
   |
   v
Software Catalogue
   |
   v
Service Request
   |
   v
Mock Provisioning
   |
   v
Status
```

## Scenario 5 - Unknown Request

Input:

```text
How do I configure the company SAP production database replication?
```

Demonstrates:

```text
Unknown / Unsupported Intent
          |
          v
      Safety Gate
          |
          v
   Human Escalation
```

The system should not fabricate an enterprise-specific answer for an unsupported request.

---

# 21. Safety and Design Principles

The prototype intentionally separates AI reasoning from workflow execution.

Key principles:

- AI classification does not directly execute sensitive actions.
- Confidence levels influence routing.
- Medium-confidence requests require confirmation.
- Low-confidence requests are escalated.
- Unknown requests are treated as a safety condition.
- Automation requires explicit workflow checks.
- Automated actions are audited.
- Knowledge answers are grounded in retrieved documentation.
- Knowledge sources are returned with grounded answers.
- ITSM and provisioning integrations are mocked rather than performing uncontrolled external actions.

---

# 22. Limitations

This is an enterprise-style prototype rather than a production ITSM platform.

### Mock ITSM integration

The current implementation uses a mock ServiceNow-compatible client rather than a live ServiceNow instance.

### Mock automation

Password reset and software provisioning use mock implementations.

### No actual software installation

The provisioning workflow demonstrates the enterprise process but does not install software on an employee device.

### Local AI inference

The Hugging Face model runs locally and may have noticeable inference latency depending on the environment.

### Prototype dashboard semantics

Some dashboard metrics are derived from ticket state and metadata rather than a complete enterprise analytics platform.

### Provisioning status

The current frontend provisioning experience does not implement a complete long-running polling interface.

### Prototype authentication

The project does not implement enterprise-grade SSO, RBAC, or production identity management.

### Production hardening

High availability, distributed workers, production observability, enterprise secrets management, advanced authorization, rate limiting, and disaster recovery are outside the prototype scope.

---

# 23. Security

Do not commit:

- API keys
- Database credentials
- Service tokens
- Passwords
- Other secrets

Use environment variables for deployment-specific configuration.

The local:

```text
backend/.env
```

file is environment-specific and should remain uncommitted.

The committed example configuration is:

```text
backend/.env.example
frontend/.env.example
```

---

# 24. Project Scope

The project is optimized to demonstrate:

- Enterprise ITSM workflow design
- AI-assisted intent understanding
- RAG architecture
- Grounded LLM responses
- Safe automation
- ITSM integration patterns
- Software provisioning workflows
- Auditability
- Frontend/backend API integration

It is **not intended to replace a production ITSM platform**.

---

# 25. Final Validation

The implementation was validated with:

```text
Backend tests:   205 passed
Frontend build:  Successful
```

The final project was also cleaned of:

- Development virtual environments
- Node dependencies
- Frontend build output
- Git metadata
- Pytest caches
- Python bytecode caches
- Temporary exports
- Phase snapshots
- Backup/patch files
- Audit tooling

The resulting project contains the consolidated backend and frontend application source.

---

# 26. End-to-End Journey

```text
Employee Request
       |
       v
AI Understanding
       |
       v
Knowledge Retrieval
       |
       v
Intelligent Decision
       |
       +-------------------+
       |                   |
       v                   v
   Automation           ITSM Ticket
       |                   |
       +---------+---------+
                 |
                 v
        Resolution /
        Status Update
```

The project demonstrates how AI can be incorporated into an enterprise IT service workflow while maintaining deterministic routing, knowledge grounding, controlled automation, auditability, and human escalation.