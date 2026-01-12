
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.api.main import app, lifespan
from src.core.db.session import AsyncSessionLocal
from src.core.db.models import Goal
from src.core.workflow.state import WorkflowState
from uuid import UUID

@pytest.mark.asyncio
async def test_end_to_end_flow(caplog):
    import logging
    caplog.set_level(logging.INFO)
    
    # Explicitly trigger lifespan to start Agents
    async with lifespan(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            
            # 1. Create Goal
            payload = {
                "title": "Integration Test Goal",
                "description": "Testing Director auto-advance"
            }
            response = await ac.post("/api/v1/workflow/goals", json=payload)
            assert response.status_code == 201
            data = response.json()
            goal_id = data["id"]
            
            print(f"Goal created: {goal_id}")
            
            # 2. Verify Initial State in DB
            async with AsyncSessionLocal() as session:
                goal = await session.get(Goal, UUID(goal_id))
                assert goal is not None
                assert goal.status == WorkflowState.INITIALIZATION.value
                
            print("Initial state verified. Waiting for Director...")
            
            # 3. Wait for Director & Lyra (Director sleeps 2s, Lyra sleeps 1s)
            await asyncio.sleep(5.0)
            
            # 4. Verify Advanced State
            async with AsyncSessionLocal() as session:
                goal = await session.get(Goal, UUID(goal_id))
                print(f"Current Status: {goal.status}")
                assert goal.status == WorkflowState.TASK_DECOMPOSITION.value
                
                # 5. Verify Tasks Generated (eager load or explicit query)
                # Re-fetch or separate query to avoid lazy load issues in async
                # Check relationship or count manually
                # NOTE: tasks relationship is lazy=select, might need joinedload or await .tasks
                pass
            
            # Separate query for tasks
            from sqlalchemy import select
            from src.core.db.models import Task
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Task).where(Task.goal_id == UUID(goal_id)))
                tasks = result.scalars().all()
                print(f"Tasks found: {len(tasks)}")
                assert len(tasks) == 3
