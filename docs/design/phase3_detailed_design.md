# OCS Phase 3: Detailed Design Document

## 1. Workflow Orchestration & State Machine

This section addresses the implementation details for the core workflow logic (nodes N1-N6) as defined in the conceptual model.

### 1.1 State Representation
**Question:** How should we strictly define the state transitions between nodes to ensure type safety and valid progression?

**Design Decision:**
We will use a **Finite State Machine (FSM)** implemented with python `enum.Enum` for state definitions and `pydantic` for state models.
*   **States**: Explicit Enums (`State.INITIALIZATION`, `State.TASK_DECOMPOSITION`, etc.).
*   **Transitions**: A strict transition table (dictionary or mapping) that defines valid `from_state` -> `to_state` pairs.
*   **Validation**: A `WorkflowEngine` class will enforce these transitions. Attempting an invalid transition raises a `TransitionError`.

### 1.2 Trigger Mechanisms
**Question:** What specific events or data conditions must be met to trigger the `E2` edge ("TASs & Prompts Ready") automatically?

**Design Decision:**
Transitions will be **Event-Driven** but guarded by **Condition Checks** (Guards).
*   **Trigger**: Completion of an Agent's task (e.g., `Lyra` finishes prompt generation).
*   **Guard**: `E2` triggers ONLY if:
    1.  `Goal Definition` exists and is valid.
    2.  `Initial Prompts` are generated (non-empty).
    3.  `required_inputs` for the next state are present in the context.

### 1.3 Parallel Execution (Node N4)
**Question:** How does the engine handle multiple agents executing simultaneously within `N4`, and how are their results synchronized?

**Design Decision:**
We will use **`asyncio.gather`** for parallel agent execution within a single workflow step.
*   **Execution**: The `Director` spawns async tasks for each active agent in the current phase.
*   **Synchronization**: The engine awaits `gather(*tasks)`. All results must return successfully (or handle errors) before the state transition logic evaluates the composite result.
*   **Aggregation**: A `ResultAggregator` service collects individual agent outputs into the shared `KnowledgeGraph` or Context before moving to `N5`.

### 1.4 Loop Prevention (Edge E4)
**Question:** How do we programmatically limit the "Refine & Re-execute" loop to prevent infinite regression?

**Design Decision:**
*   **Max Counters**: The `WorkflowContext` will maintain a `retry_count` dictionary keyed by Phase/Node.
*   **Thresholds**: A global config (e.g., `MAX_REFINEMENT_LOOPS = 3`).
*   **Diminishing Returns**: (<i>Advanced</i>) Compute semantic distance between iterations; if change < epsilon, force exit or manual intervention. For MVP, strict counter is sufficient.
*   **Fallback**: If max loops reached, transition to a `MANUAL_REVIEW` or `FAILURE` state.

### 1.5 Failure Recovery
**Question:** What is the fallback strategy if a critical transition fails?

**Design Decision:**
*   **Transaction-like States**: Each transition is atomic. If `on_enter` logic fails, the state remains at the <i>previous</i> safe state.
*   **Error Handling**: Exceptions during execution (e.g., API timeout) trigger a `retry` (with backoff).
*   **Critical Failures**: If retries are exhausted, the system enters a `SUSPENDED` state, logging the error and waiting for User/Director intervention. It does <i>not</i> auto-rollback major completed phases unless explicitly commanded.

---

## 2. Agent-Service & Interface Communication

This section details the communication architecture between the backend, CLI, and Agent services.

### 2.1 Payload Schema
**Question:** What is the strict Pydantic model for the "Task" object passed from the Task Assignment Interface to a specific Agent?

**Design Decision:**
*   **Model**: `AgentTask` (Pydantic V2).
*   **Fields**:
    *   `id`: UUIDv4
    *   `type`: Enum (`TaskType.GENERATION`, `TaskType.REVIEW`, etc.)
    *   `payload`: Dict/Any (Generic schema validated by `type`)
    *   `context_refs`: List[str] (URIs to necessary context files)
    *   `constraints`: `TaskConstraints` (timeout, max_tokens)
    *   `assigned_to`: `AgentID`
    *   `status`: `TaskStatus`

### 2.2 Inter-Process Communication
**Question:** Should we use a message queue (e.g., internal memory queue vs. Redis) or direct HTTP calls for the "Inter-Agent Bus"?

**Design Decision:**
*   **Initial MVP**: **Internal Memory Queue (Python `asyncio.Queue`)** within the single Monolith-process.
    *   Rationale: Lower complexity, easier debugging for the initial phase.
*   **Future Proofing**: Design the `MessageBus` interface such that the underlying implementation can be swapped for Redis/RabbitMQ later without changing agent logic.
*   **Protocol**: Agents subscribe to their `AgentID` topic. Director publishes tasks to specific topics.

### 2.3 Artifact Handoff
**Question:** How do agents structurally return their "Generated Artifacts" to the Director?

**Design Decision:**
*   **Structure**: `ArtifactReference` object.
*   **Method**: The Agent saves the content to the file system (standardized path: `artifacts/{session_id}/{agent_id}/{filename}`).
*   **Return Value**: The task result returns the **Absolute Path** and a **Summary/Metadata** object, not the raw content blob (unless very small).

### 2.4 Heartbeat Monitoring
**Question:** How does the system detect if an assigned agent has stalled or crashed?

**Design Decision:**
*   **Mechanism**: Active Heartbeat.
*   **Implementation**: Agents (running as background tasks) must periodically update a `last_seen` timestamp in the `AgentRegistry`.
*   **Watchdog**: A `WatchdogService` runs every N seconds. If `now() - agent.last_seen > THRESHOLD`, the agent is marked as `STALLED`, and the Director is notified to restart/reassign.

### 2.5 Permission Scoping
**Question:** How do we enforce that `GPTASe` can access the "Task Assignment" view but *not* the "Output Validation" controls?

**Design Decision:**
*   **RBAC**: Role-Based Access Control implemented via FastAPI Dependencies.
*   **Scopes**: Define scopes like `task:read`, `task:write`, `validation:approve`.
*   **Enforcement**: Agents are issued API Keys (internal tokens) with specific scopes. `GPTASe` token has `task:read`, while `Director` token has `*:*`.

---

## 3. UI/UX Architecture & Real-time Integration

This section defines the frontend architecture, focusing on dynamic interaction and visual consistency.

### 3.1 Frontend Tech Stack
**Question:** Should the UI be a server-rendered Jinja2/HTMX solution or a decoupled React/Vite SPA?

**Design Decision:**
*   **Choice**: **React/Vite SPA**.
*   **Rationale**: The requirement for "Dynamic Design", complex state management (e.g., Knowledge Graph visualization, rearranging tasks), and "Glassmorphism" interactivity strongly favors a component-based SPA over server-side rendering.
*   **Implementation**: TypeScript + React, communicating with the FastAPI backend via REST + WebSockets.

### 3.2 Real-time Updates
**Question:** How will the `Log_Stream` and `KPI_Panel` receive live updates?

**Design Decision:**
*   **Choice**: **WebSockets**.
*   **Rationale**: We require high-frequency updates for the log stream. More importantly, interaction is likely bidirectional (e.g., User pausing an Agent from the panel), which WebSockets handle natively better than SSE.
*   **Library**: `FastAPI` (backend) + native `WebSocket` API (frontend) with a lightweight wrapper for reconnection logic.

### 3.3 Component Reusability
**Question:** How can we architect the "List_TAS" component to be shared between Input and Tracking phases?

**Design Decision:**
*   **Pattern**: **Presentational vs. Container Components**.
*   **Component**: `TaskListView` (Presentational).
    *   Props: `tasks: Task[]`, `mode: 'edit' | 'readonly'`, `onAction: (id, action) => void`.
*   **Usage**:
    *   *Input Phase*: Wraps `TaskListView` with `TaskEditorContainer` (handles add/remove/edit).
    *   *Tracking Phase*: Wraps `TaskListView` with `TaskTrackerContainer` (handles live status updates, maps status to badges).

### 3.4 Visual Consistency
**Question:** How do we architect the CSS to enforce the "Slate/Sky" color palette and "Glassmorphism" tokens globally?

**Design Decision:**
*   **Strategy**: **CSS Variables (Design Tokens)**.
*   **Implementation**: A global `theme.css` defining the palette.
    ```css
    :root {
      --color-slate-900: #0f172a;
      --color-sky-500: #0ea5e9;
      --glass-bg: rgba(15, 23, 42, 0.7);
      --glass-border: 1px solid rgba(255, 255, 255, 0.1);
      --backdrop-blur: blur(12px);
    }
    ```
*   **Standardization**: All components must use these variables instead of hardcoded hex values.

### 3.5 Large Data Visualization
**Question:** What strategy should be used to render the `Tree_View` efficiently if the Knowledge Graph becomes deeply nested?

**Design Decision:**
*   **Strategy**: **Lazy-Loading with Virtualization**.
*   **Recursion**: Use a recursive component `GraphNode`.
*   **Lazy Load**: Children of a node are only fetched/rendered when the user explicitly "expands" the node (unless predetermined).
*   **Virtual Scroller**: If a single level has thousands of nodes, use `react-window` to render only the visible subset.

---

## 4. Data Persistence, Versioning, & KickLang Sync

This section addresses how data is stored, versioned, and synchronized with the Knowledge Graph.

### 4.1 Persistence Layer
**Question:** What is the optimal database structure for storing the hierarchical relationship of Goals -> TAS -> Artifacts?

**Design Decision:**
*   **Database**: **SQLite** (Dev) / **PostgreSQL** (Prod).
*   **ORM**: **SQLAlchemy (Async)** (v2.0+).
*   **Schema Strategy**: Relational.
    *   `Goal` (1) -> (Many) `Task`
    *   `Task` (1) -> (Many) `Artifact`
    *   Adjacency List model for hierarchical Tasks (subtasks).

### 4.2 Versioning Strategy
**Question:** How do we store multiple iterations of an artifact during the "Refinement Loop"?

**Design Decision:**
*   **Strategy**: **Append-Only History Tables**.
*   **Implementation**:
    *   `Artifact` Table: Stores metadata and pointer to `current_version_id`.
    *   `ArtifactVersion` Table: Stores `content`, `timestamp`, `agent_id`, `version_number`.
    *   New iterations insert a row into `ArtifactVersion` and update `Artifact.current_version_id`.

### 4.3 KickLang Serialization
**Question:** How do we implement the `N6` integration to automatically serialize finished tasks into valid `.kl` files?

**Design Decision:**
*   **Component**: `KickLangSerializer` Service.
*   **Trigger**: On state transition to `N6` or periodically.
*   **Logic**: Maps the DB entities (`Goal`, `Task`) to the KickLang YAML-like structure.
*   **Output**: Writes/Updates `ocs_conceptual.kl` (or project-specific file) ensuring it remains a valid executable spec.

### 4.4 Graph Sync
**Question:** How strictly must the runtime database mirror the "Knowledge Graph"?

**Design Decision:**
*   **Source of Truth**: **Relational Database**.
*   **Graph**: The "Knowledge Graph" is a **derived in-memory view** (using `networkx`) initialized from the DB at startup.
*   **Sync**: Changes are written to DB first. The Graph Manager observes DB events (or Service calls) to update the in-memory graph to keep them consistent.

### 4.5 Audit Trails
**Question:** How do we log every "Decision Control" action (Approve/Reject) for future meta-analysis?

**Design Decision:**
*   **Mechanism**: **Audit Log Table**.
*   **Schema**: `ActionLog(id, timestamp, actor_id, entity_type, entity_id, action_type, metadata_json)`.
*   **Capture**: A generic `AuditService.log()` call injected into the `approve_task` / `reject_task` service methods.

---

## 5. Refinement Loops & Quality Control Logic

This section defines how the system handles iterative refinement and validation of agent outputs.

### 5.1 Purification Logic
**Question:** How does the `[Purify]` button programmatically invoke the `puTASe` agent, and what context does it need?

**Design Decision:**
*   **Invocation**: API Call `POST /agents/puTASe/run`.
*   **Context**: The `Task` payload includes:
    *   `Goal Definition` (The "True North").
    *   `Input List` (The raw TAS list from GPTASe).
*   **Prompting**: A specialized refinement prompt: "Given this Goal and this Raw List, purify the list by merging duplicates and removing irrelevance."

### 5.2 Automated Validation
**Question:** Which "SMART Criteria" can be validated via regex/logic code vs. requiring LLM/Human evaluation?

**Design Decision:**
*   **Hybrid Validator**:
    *   **Logic (Fast)**: Regex for formatting (e.g., "Must start with a verb"), Length checks, JSON schema compliance.
    *   **LLM (Smart)**: "Is this Specific to the goal?", "Is this Measurable?".
*   **Pipeline**: Check Logic first. If pass, call Validation Agent. If pass, mark `status=VALIDATED_PENDING_APPROVAL`.

### 5.3 Feedback Injection
**Question:** When `[Reject]` is clicked, how is the feedback structured and injected back into the Agent's prompt context?

**Design Decision:**
*   **Structure**: `RejectionFeedback` object.
*   **Injection**: The Workflow Engine creates a new `Task` (retry) that appends a `History` block to the prompt:
    ```
    PREVIOUS ATTEMPT: {previous_content}
    CRITIQUE: {user_feedback}
    INSTRUCTION: Improve the previous attempt based on the critique.
    ```

### 5.4 Mocking for Test
**Question:** How do we simulate "Bad Artifacts" to verify that the "Output Validation Panel" correctly enables the `[Reject]` flow?

**Design Decision:**
*   **Mechanism**: **Fault Injection Middleware / Mock Agents**.
*   **Implementation**: Create a `SaboteurAgent` (or config flag `FORCE_FAILURE=True` on normal agents).
*   **Behavior**: The agent deliberately returns valid JSON but nonsense content or fails specific SMART criteria to trigger the validation UI warnings.

### 5.5 Confidence Scoring
**Question:** Should the system auto-approve artifacts if the Agent's internal confidence score exceeds a certain threshold?

**Design Decision:**
*   **Strategy**: **Conditional Auto-Approval**.
*   **Config**: `AUTO_APPROVE_THRESHOLD` (e.g., 0.95).
*   **Logic**:
    *   IF `agent.confidence >= THRESHOLD` AND `task.risk_level == 'LOW'`: Auto-Approve.
    *   ELSE: Require Human Review.
*   **Risk Level**: Defined in the Goal/Task setup (default: LOW for drafts, HIGH for final implementations).

