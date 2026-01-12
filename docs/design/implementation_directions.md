# OCS Phase 3 Implementation Directions

This document outlines the critical implementation directions for Phase 3 of the Orion Collective Orchestration System (OCS). It is organized into five key categories, each with five targeted questions to guide the design and coding process.

## 1. Workflow Orchestration & State Machine
*Focus: Implementing the core logic defined in the Workflow Diagram (Nodes N1-N6).*

1.  **State Representation**: How should we strictly define the state transitions between nodes (e.g., `N2 -> N3`) to ensure type safety and valid progression (Finite State Machine vs. Directed Acyclic Graph)?
2.  **Trigger Mechanisms**: What specific events or data conditions must be met to trigger the `E2` edge ("TASs & Prompts Ready") automatically?
3.  **Parallel Execution**: How does the engine handle multiple agents executing simultaneously within `N4`, and how are their results synchronized before moving to `N5`?
4.  **Loop Prevention**: How do we programmatically limit the "Refine & Re-execute" loop (`E4`) to prevent infinite regression (e.g., max retry counters, diminishing distinctness)?
5.  **Failure Recovery**: What is the fallback strategy if a critical transition (e.g., `E3` System Build) fails? Do we rollback to `N3` or `N2`?

## 2. Agent-Service & Interface Communication
*Focus: robust communication between the FastAPI backend, CLI, and Agent services.*

1.  **Payload Schema**: What is the strict Pydantic model for the "Task" object passed from the `Task Assignment Interface` to a specific Agent (e.g., `GPTASe`)?
2.  **Inter-Process Communication**: Since agents run as specialized loops, should we use a message queue (e.g., internal memory queue vs. Redis) or direct HTTP calls for the "Inter-Agent Bus"?
3.  **Artifact Handoff**: How do agents structurally return their "Generated Artifacts" to the Director? Is it a file path reference or a raw content blob?
4.  **Heartbeat Monitoring**: How does the system detect if an assigned agent has stalled or crashed during "Active" execution?
5.  **Permission Scoping**: How do we technically enforce that `GPTASe` can access the "Task Assignment" view but *not* the "Output Validation" decision controls?

## 3. UI/UX Architecture & Real-time Integration
*Focus: Building the frontend components (Dashboard, Panels) described in the Spec.*

1.  **Frontend Tech Stack**: Given the FastAPI backend, should the UI be a server-rendered Jinja2/HTMX solution (for simplicity) or a decoupled React/Vite SPA (for the requested "Dynamic Design")?
2.  **Real-time Updates**: How will the `Log_Stream` and `KPI_Panel` receive live updates? (Server-Sent Events (SSE) vs. WebSockets)?
3.  **Component Reusability**: How can we architect the "List_TAS" component to be shared between the *Input* phase (clean list) and the *Tracking* phase (status badges)?
4.  **Visual Consistency**: How do we architect the CSS/Tailwind configuration to enforce the "Slate/Sky" color palette and "Glassmorphism" tokens globally?
5.  **Large Data Visualization**: What strategy should be used to render the `Tree_View` efficiently if the Knowledge Graph becomes deeply nested?

## 4. Data Persistence, Versioning, & KickLang Sync
*Focus: Managing the state, artifacts, and knowledge graph integration.*

1.  **Persistence Layer**: What is the optimal database structure for storing the hierarchical relationship of Goals -> TAS -> Artifacts (SQLAlchemy w/ SQLite/Postgres)?
2.  **Versioning Strategy**: How do we store multiple iterations of an artifact during the "Refinement Loop" (e.g., `artifact_v1.md`, `artifact_v2.md`)?
3.  **KickLang Serialization**: How do we implement the `N6` integration to automatically serialize finished tasks into valid `.kl` files?
4.  **Graph Sync**: How strictly must the runtime database mirror the "Knowledge Graph"? Is the Graph the source of truth or a derived view?
5.  **Audit Trails**: How do we log every "Decision Control" action (Approve/Reject) for future meta-analysis?

## 5. Refinement Loops & Quality Control Logic
*Focus: Implementing the logic for the Output Validation Panel.*

1.  **Purification Logic**: How does the `[Purify]` button programmatically invoke the `puTASe` agent, and what context does it need (just the list, or the original goal)?
2.  **Automated Validation**: Which "SMART Criteria" can be validated via regex/logic code vs. requiring LLM/Human evaluation?
3.  **Feedback Injection**: When `[Reject]` is clicked, how is the feedback structured and injected back into the Agent's prompt context?
4.  **Mocking for Test**: How do we simulate "Bad Artifacts" to verify that the "Output Validation Panel" correctly enables the `[Reject]` flow?
5.  **Confidence Scoring**: Should the system auto-approve artifacts if the Agent's internal confidence score exceeds a certain threshold?
