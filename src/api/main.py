from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import workflow, agents, logs
from src.api.deps import _bus, _engine
from src.api.routers.agents import AgentRegistryService
from src.core.agents.director import DirectorAgent

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- LIFESPAN STARTUP ---")
    # Startup
    registry = AgentRegistryService(_bus)
    await registry.start_listening()
    
    # Initialize Core Agents
    director = DirectorAgent(bus=_bus, engine=_engine)
    await director.start()
    
    from src.api.deps import _llm
    
    from src.core.agents.lyra import LyraAgent
    lyra = LyraAgent(bus=_bus, llm=_llm)
    await lyra.start()
    
    from src.core.agents.gptase import GPTASeAgent
    gptase = GPTASeAgent(bus=_bus, llm=_llm)
    await gptase.start()
    
    yield
    print("--- LIFESPAN SHUTDOWN ---")
    # Shutdown
    await gptase.stop()
    await lyra.stop()
    await director.stop()
    # await _bus.shutdown() # If implemented

app = FastAPI(
    title="Orion Collective System (OCS)",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["workflow"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["logs"])

from src.api.routers import stream
app.include_router(stream.router, prefix="/api/v1/stream", tags=["stream"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "system": "OCS"}
