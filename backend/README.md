# ITSM AI Platform - Backend



Python/FastAPI backend for the ITSM AI Platform prototype.



The backend provides AI intent analysis, deterministic workflow routing, RAG-based knowledge retrieval, controlled self-healing, software provisioning workflows, ticket management, ITSM integration, audit logging, persistence, and dashboard aggregation.



\---



\## Architecture



```text

React Frontend

&#x20;     |

&#x20;     | REST API

&#x20;     v

&#x20;  FastAPI

&#x20;     |

&#x20;     v

Application Services

&#x20;     |

&#x20;     +-------------------+

&#x20;     |                   |

&#x20;     v                   v

&#x20;Intent / Routing       RAG

&#x20;     |                   |

&#x20;     |                   +--> Embeddings

&#x20;     |                   +--> Qdrant

&#x20;     |                   +--> Hybrid Retrieval

&#x20;     |                   +--> Grounded LLM

&#x20;     |

&#x20;     +--> Ticket Workflow

&#x20;     |

&#x20;     +--> Self-Healing

&#x20;     |

&#x20;     +--> Software Provisioning

&#x20;     |

&#x20;     +--> Dashboard

&#x20;     |

&#x20;     v

Infrastructure

&#x20;     |

&#x20;     +--> MongoDB

&#x20;     +--> Mock ITSM

&#x20;     +--> Mock Automation

&#x20;     +--> Mock Provisioning

```



\---



\## Technology



\- Python 3.12+

\- FastAPI

\- Pydantic

\- Pydantic Settings

\- PyMongo

\- Hugging Face Transformers

\- PyTorch

\- Sentence Transformers

\- Qdrant

\- YAML / Markdown knowledge documents

\- Pytest



\---



\## AI Models



\### Language Model



```text

Qwen/Qwen3-1.7B

```



Used for grounded knowledge response generation.



\### Embedding Model



```text

Alibaba-NLP/gte-modernbert-base

```



Used to generate embeddings for knowledge retrieval.



\---



\## RAG Pipeline



The backend implements:



```text

Knowledge Documents

&#x20;      |

&#x20;      v

Markdown Parsing

&#x20;      |

&#x20;      v

Semantic Chunking

&#x20;      |

&#x20;      v

Embedding Generation

&#x20;      |

&#x20;      v

Qdrant

&#x20;      |

&#x20;      +--> Dense Retrieval

&#x20;      |

&#x20;      +--> BM25 Sparse Retrieval

&#x20;      |

&#x20;      v

Hybrid Retrieval

&#x20;      |

&#x20;      v

Reciprocal Rank Fusion

&#x20;      |

&#x20;      v

Grounding Gate

&#x20;      |

&#x20;      v

Bounded Context

&#x20;      |

&#x20;      v

Qwen LLM

&#x20;      |

&#x20;      v

Grounded Answer + Sources

```



The knowledge base currently contains eight documents.



\---



\## Intent Routing



The intent workflow supports:



\- Knowledge Question

\- Incident

\- Service Request

\- Automatable Issue

\- Unknown



Confidence determines how the request proceeds:



| Confidence | Behaviour |

|---|---|

| High | Route to the appropriate workflow |

| Medium | Require confirmation |

| Low | Escalate to human support |

| Unknown | Escalate rather than guess |



The deterministic router does not directly execute workflows or call external systems.



\---



\## Main Workflows



\### Incident



```text

Intent

&#x20; |

&#x20; v

Incident Classification

&#x20; |

&#x20; v

Ticket Service

&#x20; |

&#x20; v

Mock ITSM Client

&#x20; |

&#x20; v

Incident

```



\### Self-Healing



```text

Identify

&#x20; |

Diagnose

&#x20; |

Knowledge Search

&#x20; |

Automation Decision

&#x20; |

Safety / Authorization

&#x20; |

Execute

&#x20; |

Validate

&#x20; |

Audit

&#x20; |

ITSM Update

```



\### Software Provisioning



```text

Employee Request

&#x20;     |

&#x20;     v

Intent Analysis

&#x20;     |

&#x20;     v

Software Catalogue

&#x20;     |

&#x20;     v

Service Request

&#x20;     |

&#x20;     v

Mock Provisioning

&#x20;     |

&#x20;     v

Provisioning Status

```



\---



\## ITSM Integration



The backend uses an ITSM client abstraction.



The current implementation uses a stateful mock ServiceNow-compatible client.



Supported operations include:



\- Create Incident

\- Create Service Request

\- Get Ticket

\- Update Ticket



No live ServiceNow instance is required for the prototype.



\---



\## API



The API is versioned under:



```text

/api/v1

```



Important endpoints include:



```text

POST /api/v1/intent



POST /api/v1/knowledge/search



POST /api/v1/knowledge/ask



POST /api/v1/self-healing



GET/POST /api/v1/software-provisioning/...



GET/POST /api/v1/tickets/...



GET /api/v1/dashboard/summary

```



The FastAPI route definitions are the source of truth for request and response schemas.



\---



\## Configuration



Configuration is managed through Pydantic Settings.



Supported variables:



```env

APP\_NAME=ITSM AI Platform

ENVIRONMENT=development

DEBUG=true

MONGODB\_URI=mongodb://localhost:27017

MONGODB\_DATABASE=itsm

```



A configuration template is provided at:



```text

.env.example

```



Create the local configuration with:



```powershell

Copy-Item .env.example .env

```



Do not place real credentials or secrets in `.env.example`.



The local `.env` file is ignored by Git.



\---



\## Installation



Requirements:



\- Python 3.12+

\- MongoDB-compatible database

\- Qdrant

\- Sufficient local resources for the Hugging Face models



Create an environment:



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



Install dependencies:



```powershell

pip install -e .

```



\---



\## Running



Start the FastAPI application:



```powershell

uvicorn app.main:app --reload --port 8000

```



Backend:



```text

http://localhost:8000

```



Swagger/OpenAPI documentation:



```text

http://localhost:8000/docs

```



Health endpoint:



```text

http://localhost:8000/health

```



\---



\## Knowledge Base



Knowledge documents are stored under:



```text

knowledge/

```



Current topics include:



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



The knowledge ingestion and retrieval components prepare these documents for Qdrant-based retrieval.



\---



\## Testing



Run the complete backend test suite:



```powershell

pytest -q

```



Final validation:



```text

205 passed

```



The test suite covers API behaviour, intent analysis, routing, workflow orchestration, tickets, ITSM, RAG, self-healing, software provisioning, repositories, and audit behaviour.



\---



\## Project Structure



```text

backend/

|

+-- app/

|   +-- api/

|   +-- application/

|   +-- config/

|   +-- domain/

|   +-- infrastructure/

|

+-- evaluation/

|

+-- knowledge/

|

+-- tests/

|

+-- .env.example

+-- .gitignore

+-- .python-version

+-- pyproject.toml

+-- README.md

+-- uv.lock

```



\### Application layers



```text

api

&#x20;|

&#x20;v

application

&#x20;|

&#x20;v

domain

&#x20;|

&#x20;v

infrastructure

```



The architecture keeps workflow orchestration separate from infrastructure implementations.



\---



\## Safety



The backend intentionally separates AI analysis from workflow execution.



Important controls include:



\- Confidence-based routing

\- Medium-confidence confirmation

\- Low-confidence escalation

\- Unknown-intent escalation

\- Knowledge grounding

\- Source attribution

\- Authorization checks

\- Consent checks

\- Approved automation policies

\- Validation after automation

\- Audit logging



Unknown requests are not automatically sent through RAG or automation.



\---



\## Prototype Limitations



The backend is intentionally a prototype.



Current limitations include:



\- Mock ServiceNow integration

\- Mock password-reset automation

\- Mock software provisioning

\- No actual software installation

\- Local Hugging Face inference

\- Prototype authentication

\- Prototype dashboard semantics

\- No production distributed worker architecture

\- No enterprise SSO/RBAC

\- No production-grade observability or high availability



\---



\## Relationship to the Root Project



For complete project architecture, frontend usage, demo scenarios, limitations, and end-to-end workflows, see:



```text

../README.md

```



The root README is the primary project documentation.

