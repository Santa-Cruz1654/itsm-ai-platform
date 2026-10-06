\# ITSM AI Platform - Frontend



React + TypeScript frontend for the ITSM AI Platform prototype.



The frontend provides the employee self-service experience, knowledge-base interface, AI workflow results, and ITSM operations dashboard.



\---



\## Technology



\- React

\- TypeScript

\- Vite

\- CSS



\---



\## Application Areas



The frontend provides three primary areas.



\### Employee Portal



Employees can submit natural-language IT requests.



Example requests:



```text

My VPN is not connecting.

```



```text

My password has expired.

```



```text

How do I troubleshoot Outlook synchronization?

```



```text

I need Visual Studio Code installed on my laptop.

```



The portal sends the request to the FastAPI backend for AI intent analysis and workflow routing.



\### Knowledge Base



Provides knowledge search and grounded answers.



Knowledge responses can display the supporting sources returned by the backend.



\### ITSM Operations



Provides the operational dashboard showing ticket and workflow information returned by the backend.



\---



\## Frontend Architecture



```text

Employee

&#x20;   |

&#x20;   v

React Application

&#x20;   |

&#x20;   +--> Employee Portal

&#x20;   |

&#x20;   +--> Knowledge Base

&#x20;   |

&#x20;   +--> ITSM Operations

&#x20;   |

&#x20;   v

API Client

&#x20;   |

&#x20;   v

FastAPI Backend

```



The frontend does not implement the AI reasoning itself. AI classification, routing, RAG, automation, ticketing, and provisioning are handled by the backend.



\---



\## API Integration



The frontend communicates with the backend through REST APIs.



The API client is located under:



```text

src/api/

```



The primary API base configuration is:



```text

VITE\_API\_BASE\_URL

```



If `VITE\_API\_BASE\_URL` is not provided, the frontend uses relative `/api` requests.



During local development, Vite proxies `/api` requests to:



```text

http://127.0.0.1:8000

```



\---



\## Configuration



An example frontend environment file is provided:



```text

.env.example

```



Do not put secrets, API keys, passwords, database credentials, or service tokens into `VITE\_\*` variables.



Vite exposes client-side environment variables to the browser, so sensitive credentials must remain on the backend.



\---



\## Installation



Requirements:



\- Node.js

\- npm



Install dependencies:



```powershell

npm install

```



\---



\## Development



Start the development server:



```powershell

npm run dev

```



The frontend is available at:



```text

http://localhost:5173

```



The development server proxies API requests to the FastAPI backend.



Run the backend separately from:



```text

backend/

```



\---



\## Production Build



Validate the production build with:



```powershell

npm run build

```



The build output is generated under:



```text

dist/

```



The `dist/` directory is a generated build artifact and is not part of the source repository.



\---



\## Demo Scenarios



The employee portal supports the main project demonstration scenarios:



1\. VPN incident

2\. Password self-healing

3\. Outlook knowledge question

4\. Software provisioning

5\. Unknown / unsupported request



\### VPN



```text

My VPN is not connecting.

```



Expected flow:



```text

Employee Request

&#x20;   |

&#x20;   v

AI Intent

&#x20;   |

&#x20;   v

Incident

&#x20;   |

&#x20;   v

ITSM Ticket

```



\### Password



```text

My password has expired.

```



Expected flow:



```text

Intent

&#x20;   |

&#x20;   v

Self-Healing Workflow

&#x20;   |

&#x20;   v

Approved Automation

&#x20;   |

&#x20;   v

Validation + Audit

```



\### Outlook



```text

How do I troubleshoot Outlook synchronization?

```



Expected flow:



```text

Intent

&#x20;   |

&#x20;   v

Knowledge Retrieval

&#x20;   |

&#x20;   v

Grounded Answer

&#x20;   |

&#x20;   v

Sources

```



\### Software Provisioning



```text

I need Visual Studio Code installed on my laptop.

```



Expected flow:



```text

Intent

&#x20;   |

&#x20;   v

Software Catalogue

&#x20;   |

&#x20;   v

Service Request

&#x20;   |

&#x20;   v

Mock Provisioning

```



\### Unknown Request



```text

How do I configure the company SAP production database replication?

```



Expected flow:



```text

Unknown / Unsupported Intent

&#x20;   |

&#x20;   v

Safety Gate

&#x20;   |

&#x20;   v

Human Escalation

```



\---



\## Project Structure



```text

frontend/

|

+-- src/

|   +-- api/

|   +-- components/

|   +-- pages/

|   +-- types/

|

+-- .env.example

+-- ARCHITECTURE.md

+-- index.html

+-- package.json

+-- package-lock.json

+-- README.md

+-- tsconfig.app.json

+-- tsconfig.json

+-- tsconfig.node.json

+-- vite.config.ts

```



\---



\## Backend Dependency



The frontend requires the FastAPI backend to be running for the complete application workflow.



Backend API:



```text

http://localhost:8000

```



API documentation:



```text

http://localhost:8000/docs

```



Frontend:



```text

http://localhost:5173

```



\---



\## Prototype Scope



The frontend is part of an enterprise-style ITSM prototype.



It demonstrates:



\- Employee self-service

\- AI-assisted request handling

\- Knowledge retrieval

\- Grounded responses

\- ITSM workflow visualization

\- Self-healing workflow interaction

\- Software provisioning workflow

\- Human escalation



Production authentication, enterprise SSO, RBAC, and other production security infrastructure are outside the prototype scope.



\---



\## Related Documentation



For complete project architecture, backend implementation, RAG design, safety controls, API overview, testing, limitations, and end-to-end workflows, see:



```text

../README.md

```



The root README is the primary project documentation.

