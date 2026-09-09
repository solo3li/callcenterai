# AI Call Center Platform - Reference Document

This document serves as the primary architectural and developmental reference for the AI Call Center Platform. It maps the project requirements to the physical folder structure and outlines the technology stack.

## 1. System Architecture & Tech Stack

The system is designed as a scalable, multi-tenant microservices architecture:
- **Core / Backend:** Django, PostgreSQL
- **Realtime AI Voice:** Pipecat, Gemini Live
- **Telephony & WebRTC:** LiveKit Server, SIP Trunks
- **Realtime Communication:** Centrifugo
- **Knowledge Base (RAG):** R2R, Apache Tika, PostgreSQL (pgvector)
- **Workflow Automation:** n8n, n8n PostgreSQL
- **Infrastructure:** Docker, Kubernetes, Helm, Traefik, Object Storage

## 2. Microservices Directory Mapping

The workspace is structured into independent services:

- **`/project_service_main/` (Phase 1, 2, 5, 11, 12, 13, 14)**
  The core Django backend. Manages organizations (multi-tenancy), users, authentication, human agent dashboards, billing, analytics, and centralized database state.
- **`/ai_service/` (Phase 4)**
  The realtime AI voice processor. Runs Pipecat AI workers integrated with Gemini Live for low-latency, speech-to-speech conversational agents.
- **`/rag_service/` (Phase 8)**
  The document processing and retrieval engine. Uses R2R and Apache Tika for parsing documents, generating embeddings, vector search, and serving context to the AI agents.
- **`/workflow_service/` (Phase 10)**
  The automation engine. Uses n8n to handle event-driven workflows, webhook triggers, external CRM integrations, and automated actions based on call states.

## 3. Development Roadmap (16 Phases)

* **Phase 1 — Core Foundation:** Django Core, PostgreSQL, Multi-tenancy, Auth, Groups.
* **Phase 2 — AI Agents:** Data models for AI Agent personas, configuration, and behaviors.
* **Phase 3 — Voice / Telephony:** LiveKit Server, SIP trunks, Inbound/Outbound routing.
* **Phase 4 — Realtime AI:** Pipecat, Gemini Live integration, function/tool calling.
* **Phase 5 — Human Support:** Human Agent App, routing, AI to Human transfers.
* **Phase 6 — Realtime Communication:** Centrifugo integration for agent presence and events.
* **Phase 7 — Recording & Transcription:** LiveKit Egress, Audio storage, and speaker identification.
* **Phase 8 — Knowledge / RAG:** R2R deployment, vector embeddings, and RAG pipelines.
* **Phase 9 — Actions / Integrations:** API frameworks for AI tools (REST, gRPC, WebSocket).
* **Phase 10 — Workflow Automation:** n8n deployment for external business logic and triggers.
* **Phase 11 — Call Management:** Call timelines, metadata, outcomes, and state machines.
* **Phase 12 — Analytics:** System-wide metrics for AI, Human agents, and Organizations.
* **Phase 13 — Billing:** Usage tracking (AI minutes, SIP), subscriptions, and limits.
* **Phase 14 — Admin & Security:** System dashboards, RBAC, and rate limiting.
* **Phase 15 — Observability:** Centralized logs, metrics, and alerting.
* **Phase 16 — Production / Scale:** Kubernetes deployment, high availability, and disaster recovery.

## 4. Core Capabilities

- **Hybrid Operations:** Complete synergy between AI initial handling and seamless warm-transfers to human agents.
- **Tool Calling:** AI can perform strict API calls (Actions) during live conversations (e.g., checking order status).
- **Tenant Isolation:** Robust data and security isolation ensuring B2B SaaS readiness.
