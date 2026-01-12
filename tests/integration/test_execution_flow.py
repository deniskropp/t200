
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.api.main import app, lifespan
from src.core.db.session import AsyncSessionLocal
from src.core.db.models import Task
from uuid import UUID
from sqlalchemy import select

@pytest.mark.asyncio
async def test_execution_flow():
    # Full flow: Goal -> Lyra -> Tasks -> Director -> GPTASe -> Success
    
    async with lifespan(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            
            # 1. Create Goal
            payload = {"title": "Execution Test", "description": "Testing GPTASe"}
            response = await ac.post("/api/v1/workflow/goals", json=payload)
            goal_id = response.json()["id"]
            
            # 2. Wait for Workflow (Director (2s initial) + Lyra (1s) + Director(Assign) + GPTASe (2-4s))
            # Safe wait: 10s
            print("Waiting for workflow execution...")
            for i in range(10):
                await asyncio.sleep(1)
                # print(f"Tick {i}")

            # 3. Verify Tasks Completed
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Task).where(Task.goal_id == UUID(goal_id)))
                tasks = result.scalars().all()
                
                assert len(tasks) == 3
                
                # We expect COMPLETED now that Director handles the result loop
                completed_count = sum(1 for t in tasks if t.status == "COMPLETED")
                print(f"Completed Tasks: {completed_count}")
                assert completed_count == 3
                
                # Check assigned
                assigned_count = sum(1 for t in tasks if t.assigned_to == "GPTASe")
                assert assigned_count == 3
