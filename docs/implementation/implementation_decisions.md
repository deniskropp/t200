# OCS Phase 3 Implementation Planning

## Structural Recommendation
The redundant directory structure `src/ocs` has been dissolved.
- `src/ocs/shared` → `src/shared`
- `src/ocs/cli` → `src/cli`
- `src/ocs/api` → `src/api`
Imports have been updated to reference top-level packages.

---

## Implementation Decisions (/impl)

### 1. Project Structure & Core Standards
1. **Dissolving `src/ocs`**: **DONE**. `src/ocs` is removed.
2. **Shared Library**: `src/shared` is strictly for pure utilities/DTOs.
3. **Configuration**: Consolidate in `src/shared/config.py` using `pydantic-settings`.
4. **Error Handling**: Unified `AppError` in `src/shared/errors.py`.
5. **Logging**: Enforce `structlog`.

### 2. Agent Architecture (Core)
1. **Base Agent**: Enforce `process_message(msg)` interface.
2. **Inter-Agent Bus**: `InMemoryMessageBus` for MVP, interface-ready for Redis.
3. **State Persistence**: Persist on logical checkpoints.
4. **LLM Service**: Provider-agnostic interface in `src/core/llm`.
5. **Concurrency**: `asyncio.Task` within the main process.

### 3. Workflow & Orchestration
1. **State Machine**: Flexible, code-driven transitions.
2. **Workflow Guards**: Asynchronous.
3. **Task Decomposition**: Independent DB rows for sub-tasks.
4. **Context Passing**: Via message bus payload.
5. **Failure Recovery**: Auto-retry with backoff.

### 4. API Layer (FastAPI)
1. **DTOs vs ORM**: Decoupled.
2. **Streaming**: WebSockets.
3. **Authentication**: Placeholder/No-auth for now.
4. **Versioning**: Strict `/api/v1`.
5. **Validation**: Custom `422` handler.

### 5. User Interface (Frontend)
1. **Component System**: TailwindCSS + Component Library (e.g. shadcn/ui).
2. **State Management**: React Context + Hooks.
3. **Mocking**: "Mock API" mode supported.
4. **Log Viewer**: Searchable/Filterable.
5. **Task Interaction**: Dedicated "Inbox" view.
