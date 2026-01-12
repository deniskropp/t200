from fastapi import FastAPI
from ocs.shared.constants import SYSTEM_NAME, SYSTEM_VERSION, SYSTEM_MODE
from ocs.shared.models import Task, TaskState

app = FastAPI(title=SYSTEM_NAME, version=SYSTEM_VERSION)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "system": SYSTEM_NAME,
        "version": SYSTEM_VERSION,
        "mode": SYSTEM_MODE,
        "status": "online"
    }

@app.post("/tasks/")
async def create_task(task: Task):
    """Create a new task."""
    # Logic to add task to queue/db
    task.state = TaskState.PENDING
    return {"message": "Task received", "task": task}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status."""
    return {"task_id": task_id, "status": "Not found (Mock)"}
