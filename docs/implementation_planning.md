# OCS Phase 3 Implementation Planning

## Structural Recommendation
The existence of both `src/...` and `src/ocs/...` is redundant and a result of transitional restructuring.

**Action Item**: Dissolve `src/ocs` completely.
- Move `src/ocs/shared` → `src/shared`
- Move `src/ocs/cli` → `src/cli`
- Move `src/ocs/api` → merge into `src/api`
- Update all imports to reference the top-level packages (`src.shared`, `src.core`, etc.).

---

## Implementation Questions (/impl)

### 1. Project Structure & Core Standards
1. **Dissolving `src/ocs`**: Do you confirm the immediate removal of `src/ocs` and redistribution of its contents to `src/api`, `src/cli`, and `src/shared`?
2. **Shared Library**: Should `src/shared` be strictly for pure utilities/DTOs (no business logic) to prevent circular imports?
3. **Configuration**: Shall we consolidate all config loading (Env, TOML) into `src/shared/config.py` using Pydantic Settings?
4. **Error Handling**: Do you want a unified `AppError` base class in `src/shared/errors.py` that maps automatically to HTTP 4xx/5xx in the API?
5. **Logging**: Should we enforce `structlog` or standard `logging` with JSON capability for all services?

### 2. Agent Architecture (Core)
1. **Base Agent**: Should the `BaseAgent` class (in `src/core/agents`) enforce a strict `process_message(msg)` interface, or allow flexible method dispatching?
2. **Inter-Agent Bus**: To ensure `src/core/bus` is the single source of truth—should we stick to the current in-memory implementation for now or interface-ready it for Redis/RabbitMQ?
3. **State Persistence**: Should agents persist their state (memory/context) on every message handled, or only at specific checkpoints?
4. **LLM Service**: In `src/core/llm`, should we implement a provider-agnostic interface (supporting OpenAI/Anthropic/Google) now, or stick to a single provider for MVP?
5. **Concurrency**: Should agents run as independent `asyncio.Task`s within the main process, or do you foresee separate processes/containers soon?

### 3. Workflow & Orchestration
1. **State Machine**: Should we implement a rigid definition (e.g., transitions defined in a declarative dict/yaml) or code-driven flexible transitions?
2. **Workflow Guards**: Do you want "Guard" functions to run *synchronously* blocking the transition, or *asynchronously* (potentially long-running checks)?
3. **Task Decomposition**: When `Lyra` decomposes a task, should the sub-tasks be created as independent rows in the DB immediately?
4. **Context Passing**: How should global workflow context (e.g. "User verified X") be passed to individual agents? Via the message bus payload or a shared context store?
5. **Failure Recovery**: If a step fails, should the workflow auto-pause for human intervention, or attempt auto-retry with backoff?

### 4. API Layer (FastAPI)
1. **DTOs vs ORM**: Shall we strictly decouple API models (Pydantic) from DB models (SQLAlchemy), requiring mapper functions for every endpoint?
2. **Streaming**: For real-time feedback (Agent → UI), should we prioritize Server-Sent Events (SSE) or WebSockets?
3. **Authentication**: Do we need a placeholder Auth dependency in `src/api/deps.py` now (e.g. JWT stub), or effectively "no-auth" for this phase?
4. **Versioning**: Should we enforce `/api/v1/...` prefix strictness now?
5. **Validation**: Should we implement a custom validation handler to return formatted "422 Unprocessable Entity" errors matching the frontend's form expectations?

### 5. User Interface (Frontend)
1. **Component System**: Are we sticking to a specific styling solution (e.g. TailwindCSS, or a library like shadcn/ui)?
2. **State Management**: For the `TaskBoard` and live logs, should we use a simple React Context or a store like Zustand/Jotai?
3. **Mocking**: Should the UI be built against a "Mock API" mode first (ignoring the real backend)?
4. **Log Viewer**: Do you need a searchable/filterable log viewer component, or just a tailing stream?
5. **Task Interaction**: Should the "Human in the Loop" approvals be a modal on the board or a dedicated "Inbox" view?
