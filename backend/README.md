# ITSM AI Platform — Backend

A Python/FastAPI backend for an AI-powered IT Service Management (ITSM) platform prototype. The backend orchestrates intelligent request classification, knowledge retrieval, ticket management, controlled self-healing workflows, software provisioning, audit logging, and dashboard aggregation.

The platform is designed around a separation of concerns: AI components analyze requests, application services coordinate workflows, and infrastructure adapters handle persistence and external-system interactions.

> **Project status:** Working prototype. The backend test suite passes **206 tests**. ServiceNow integration, automation, and provisioning currently use mock implementations rather than live enterprise systems.

---

## Table of Contents

- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [AI Models](#ai-models)
- [Retrieval-Augmented Generation](#retrieval-augmented-generation-rag)
- [Intent Classification and Routing](#intent-classification-and-routing)
- [Core Workflows](#core-workflows)
- [ITSM Integration](#itsm-integration)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Installation](#installation)
- [Running the Backend](#running-the-backend)
- [Knowledge Base](#knowledge-base)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Safety and Control Mechanisms](#safety-and-control-mechanisms)
- [Prototype Limitations](#prototype-limitations)
- [Relationship to the Root Project](#relationship-to-the-root-project)

---

## Architecture

The backend follows a layered architecture that separates API handling, application workflows, domain logic, and infrastructure integrations.

```text
                    React Frontend
                          |
                          | REST API
                          v
                   FastAPI Application
                          |
                          v
                    API Layer
                          |
                          v
                 Application Services
                          |
             +------------+------------+
             |            |            |
             v            v            v
       Intent/Routing     RAG      Ticket Workflows
             |            |            |
             |            +--> Embeddings
             |            +--> Qdrant
             |            +--> Hybrid Retrieval
             |            +--> Grounded LLM
             |
             +--> Self-Healing
             |
             +--> Software Provisioning
             |
             +--> Dashboard Aggregation
                          |
                          v
                    Infrastructure
                          |
             +------------+------------+
             |            |            |
             v            v            v
          MongoDB      Mock ITSM    Mock Automation
                                      |
                                      v
                               Mock Provisioning
```

### Architectural layers

| Layer | Responsibility |
|---|---|
| API | Exposes versioned HTTP endpoints and handles request/response validation. |
| Application | Coordinates intent analysis, ticket operations, knowledge retrieval, automation, and provisioning workflows. |
| Domain | Contains core business concepts and domain-level rules. |
| Infrastructure | Implements persistence, retrieval integrations, ITSM adapters, and automation adapters. |

The architecture keeps workflow orchestration separate from infrastructure implementations, making individual components easier to test and replace.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python 3.12+ |
| Backend framework | FastAPI |
| Data validation and settings | Pydantic, Pydantic Settings |
| Database integration | PyMongo, MongoDB-compatible database |
| Language model ecosystem | Hugging Face Transformers, PyTorch |
| Embeddings | Sentence Transformers |
| Vector database | Qdrant |
| Knowledge documents | Markdown, YAML |
| Testing | Pytest |

---

## AI Models

### Language Model

```text
Qwen/Qwen3-1.7B
```

Used for grounded knowledge-response generation in the RAG pipeline.

### Embedding Model

```text
Alibaba-NLP/gte-modernbert-base
```

Used to generate vector embeddings for semantic knowledge retrieval.

> Model availability, hardware requirements, model-loading configuration, and runtime behaviour depend on the local environment and application configuration.

---

## Retrieval-Augmented Generation (RAG)

The knowledge retrieval pipeline combines semantic search with lexical retrieval to find relevant information before generating a response.

### Pipeline

```text
                 Knowledge Documents
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
                +--------+--------+
                |                 |
                v                 v
          Dense Retrieval    BM25 Sparse Retrieval
                |                 |
                +--------+--------+
                         |
                         v
                  Hybrid Retrieval
                         |
                         v
             Reciprocal Rank Fusion (RRF)
                         |
                         v
                    Grounding Gate
                         |
                         v
                   Bounded Context
                         |
                         v
                      Qwen LLM
                         |
                         v
              Grounded Answer + Sources
```

### Key components

- **Document parsing:** Reads supported knowledge documents.
- **Semantic chunking:** Splits content into retrieval-oriented segments.
- **Embedding generation:** Converts knowledge chunks into vectors.
- **Dense retrieval:** Finds semantically similar content using vector representations.
- **BM25 sparse retrieval:** Finds relevant content through lexical matching.
- **Hybrid retrieval:** Combines dense and sparse retrieval results.
- **Reciprocal Rank Fusion (RRF):** Combines ranked results from different retrieval methods.
- **Grounding gate:** Applies the application's grounding rules before generation.
- **Bounded context:** Limits the retrieved information supplied to the language model.
- **Source attribution:** Returns supporting sources with the generated answer.

The knowledge base currently contains eight documents covering common IT support topics.

---

## Intent Classification and Routing

The intent workflow categorizes incoming requests and determines which application workflow should handle them.

### Supported intent categories

| Intent | Purpose |
|---|---|
| Knowledge Question | Requests for IT information or troubleshooting guidance. |
| Incident | Reports of existing IT problems. |
| Service Request | Requests for IT services or resources. |
| Automatable Issue | Problems that may qualify for an approved automated workflow. |
| Unknown | Requests that cannot be confidently categorized. |

### Confidence-based routing

| Confidence level | Intended behaviour |
|---|---|
| High | Route the request to the appropriate workflow. |
| Medium | Request confirmation where required. |
| Low | Escalate to human support. |
| Unknown | Escalate rather than guess. |

The deterministic router is responsible for routing decisions. It does not independently execute workflows or directly invoke external systems.

---

## Core Workflows

### 1. Incident Management

The incident workflow coordinates request classification, ticket creation, and ITSM interaction.

```text
Employee Request
       |
       v
Intent Classification
       |
       v
Incident Workflow
       |
       v
Ticket Service
       |
       v
Mock ITSM Client
       |
       v
Incident Record
```

The prototype supports ticket creation and ticket-related operations through its ITSM abstraction.

### 2. Self-Healing Automation

The self-healing workflow evaluates whether an issue can be handled through an approved automation path.

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
Safety and Authorization Checks
   |
   v
Execute Approved Action
   |
   v
Validate Outcome
   |
   v
Audit Result
   |
   v
Update ITSM Ticket
```

The workflow separates issue analysis from action execution. Automation decisions are subject to application policies, authorization checks, and validation.

The current implementation uses mock automation rather than executing real enterprise remediation operations.

### 3. Software Provisioning

The provisioning workflow handles employee requests for software.

```text
Employee Request
       |
       v
Intent Analysis
       |
       v
Software Catalogue
       |
       v
Service Request
       |
       v
Mock Provisioning Adapter
       |
       v
Provisioning Status
```

The prototype models the provisioning workflow and its status transitions. It does not perform actual software installation on employee devices.

### 4. Ticket Management

Ticket-related application services coordinate ticket operations and ITSM interactions.

The backend also aggregates ticket information for the dashboard, including ticket counts and workflow-related status information.

### 5. Dashboard Aggregation

The dashboard service combines application data to provide a summary of ITSM activity to the frontend.

The dashboard is intended for the prototype's operational overview. Its metrics should not be interpreted as production-grade service-level indicators without further validation.

---

## ITSM Integration

The backend uses an ITSM client abstraction to separate ticket workflows from the underlying ITSM implementation.

The current prototype uses a stateful mock ServiceNow-compatible client.

### Supported operations

- Create incident
- Create service request
- Retrieve ticket
- Update ticket

No live ServiceNow instance is required for the prototype.

### Integration boundary

The mock client provides a way to demonstrate and test ITSM workflows without connecting to an enterprise ServiceNow environment.

A production integration would require an appropriately configured ServiceNow instance, authentication, permissions, error handling, and integration testing.

---

## API Reference

The backend exposes versioned API routes under:

```text
/api/v1
```

### Important endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/intent` | Analyze an incoming request and determine its intent. |
| POST | `/api/v1/knowledge/search` | Search the knowledge base. |
| POST | `/api/v1/knowledge/ask` | Submit a knowledge question. |
| POST | `/api/v1/self-healing` | Invoke the self-healing workflow. |
| GET/POST | `/api/v1/software-provisioning/...` | Access software provisioning operations. |
| GET/POST | `/api/v1/tickets/...` | Access ticket-related operations. |
| GET | `/api/v1/dashboard/summary` | Retrieve dashboard summary information. |

The ellipses indicate endpoint families rather than literal route paths. Consult the FastAPI route definitions for the exact methods, paths, request schemas, and response schemas.

### Interactive API documentation

When the backend is running locally, FastAPI's Swagger UI is available at:

```text
http://localhost:8000/docs
```

The generated OpenAPI specification can be viewed at:

```text
http://localhost:8000/openapi.json
```

The application's route definitions are the source of truth for the API contract.

---

## Configuration

Application configuration is managed through Pydantic Settings.

The following variables illustrate the expected configuration format. Confirm the actual variable names and defaults in the application's settings implementation.

```env
APP_NAME="ITSM AI Platform"
ENVIRONMENT=development
DEBUG=true
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=itsm
```

A configuration template is expected at:

```text
.env.example
```

### Windows PowerShell

From the backend directory, create a local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure the values required by your environment.

**Security guidelines:**

- Never commit `.env` files containing credentials.
- Do not place API keys, passwords, or other secrets in `.env.example`.
- Keep local environment files excluded through `.gitignore`.
- Use appropriate secret-management mechanisms for production deployments.

---

## Installation

### Prerequisites

- Python 3.12 or a compatible version supported by the project.
- `uv` or another supported Python environment and package-management workflow.
- MongoDB-compatible database if database-backed functionality is enabled.
- Qdrant if vector retrieval functionality is enabled.
- Sufficient memory and processing resources for the configured Hugging Face models.

### 1. Navigate to the backend

```powershell
cd D:\itsm\backend
```

### 2. Create a virtual environment

If you are using standard Python tooling:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Alternatively, if the project is configured for `uv`, use its environment-management commands.

### 3. Install dependencies

Using pip:

```powershell
pip install -e .
```

Use the dependency and lockfile configuration committed with the project when reproducing the intended environment.

---

## Running the Backend

Start the FastAPI application from the backend directory:

```powershell
uvicorn app.main:app --reload --port 8000
```

### Local URLs

| Resource | Address |
|---|---|
| Backend | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| OpenAPI specification | `http://localhost:8000/openapi.json` |
| Health endpoint | `http://localhost:8000/health` |

The health endpoint is available at `/health` in the documented application configuration. If the route is changed, use the route definition as the source of truth.

---

## Knowledge Base

Knowledge documents are stored under:

```text
knowledge/
```

The current knowledge topics include:

```text
access
laptop
mfa
outlook
password
software
vpn
wifi
```

The ingestion and retrieval components prepare the knowledge documents for Qdrant-based search.

The knowledge base supports the prototype's IT support and troubleshooting scenarios.

---

## Testing

The backend uses Pytest for automated testing.

### Run the test suite

From the backend directory:

```powershell
uv run pytest -q
```

Alternatively, if the environment is already configured:

```powershell
pytest -q
```

### Latest recorded validation

```text
206 passed, 1 warning
```

The latest recorded run completed in approximately 15 seconds.

The warning concerns a Starlette deprecation notice involving `httpx` and the test client. It did not cause any test failures.

### Test coverage areas

The test suite exercises multiple parts of the backend, including:

- API behaviour
- Intent analysis and routing
- Workflow orchestration
- Ticket management
- ITSM interactions
- Knowledge retrieval and RAG
- Self-healing workflows
- Software provisioning
- Repository implementations
- Audit behaviour

The recorded test result demonstrates that the current automated test suite passes. It does not, by itself, establish production readiness or validate live enterprise integrations.

---

## Project Structure

The main backend layout is:

```text
backend/
├── app/
│   ├── api/
│   ├── application/
│   │   └── ports/
│   ├── config/
│   ├── domain/
│   └── infrastructure/
│       ├── database/
│       └── repositories/
├── evaluation/
├── knowledge/
├── tests/
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
└── uv.lock
```

This is a representative layout. Refer to the actual repository for the complete set of files and directories.

### Application dependency direction

```text
API
 |
 v
Application
 |
 v
Domain

Infrastructure provides implementations
for application-facing interfaces.
```

The separation allows application workflows to be tested without requiring every infrastructure integration to be live.

---

## Safety and Control Mechanisms

The backend separates AI-assisted analysis from workflow execution.

The implemented design includes controls such as:

- Confidence-based routing
- Confirmation for medium-confidence decisions where required
- Escalation for low-confidence requests
- Unknown-intent escalation
- Knowledge grounding
- Source attribution
- Authorization checks
- Consent checks
- Approved automation policies
- Post-automation validation
- Audit logging

Unknown requests are not automatically sent through RAG or automation.

These mechanisms support safer workflow handling in the prototype. They should not be interpreted as a substitute for a full enterprise security review, production authorization model, or operational risk assessment.

---

## Prototype Limitations

The project demonstrates an AI-assisted ITSM architecture but is not a complete production deployment.

Current limitations include:

- Mock ServiceNow integration rather than a live enterprise connection
- Mock password-reset automation
- Mock software provisioning
- No actual software installation on employee devices
- Local Hugging Face model inference
- Prototype authentication
- Prototype dashboard semantics
- No production distributed-worker architecture
- No enterprise SSO/RBAC implementation
- No production-grade observability or high availability

Additional work would be required to deploy the platform in a real enterprise environment, including security hardening, identity integration, monitoring, deployment automation, and integration testing.

---

## Relationship to the Root Project

This README documents the backend component.

For the complete platform architecture, frontend usage, demonstration scenarios, end-to-end workflows, and overall project limitations, see the root README:

```text
../README.md
```

The root README is the primary documentation for the complete ITSM AI Platform.