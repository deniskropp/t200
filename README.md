# Orion Collective Orchestration System (OCS)

## Overview
The **Orion Collective Orchestration System (OCS)** is a fully adaptive, self-evolving orchestration system designed to transform high-level intent into high-fidelity execution. It leverages specialized agents (Director, Lyra, Aurora, etc.) to decompose goals, design workflows, and execute tasks.

## Project Structure
The codebase is organized as a modern Python package under `src/ocs`:
```
src/ocs/
├── api/       # FastAPI backend services
├── cli/       # Command-line interface (Typer)
└── shared/    # Core domain models, prompts, and interfaces
```

## Getting Started

### Prerequisites
- Python 3.12+
- `pip` or other package manager (`uv`, `pdm`)

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```

### Usage

#### CLI
Interaction with the OCS is primarily done via the CLI.
```bash
python -m ocs.cli.main --help
```
**Available Commands:**
- `init`: Initialize the environment.
- `list-agents`: View available agent roles.
- `run-agent`: Start a specific agent loop.

#### API
Start the backend server:
```bash
fastapi dev src/ocs/api/main.py
```
Or using `uvicorn` directly:
```bash
uvicorn ocs.api.main:app --reload
```
API Documentation will be available at `http://localhost:8000/docs`.

## Documentation
- [Conceptual Design](docs/design/ocs_conceptual.kl)
- [Phase 3 Specs](docs/design/phase3_design_spec.kl)
- [Blueprint](docs/blueprint/orchestration_blueprint.md)
