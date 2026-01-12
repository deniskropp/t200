import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app, lifespan
from src.core.workflow.state import WorkflowState  
    
@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_create_and_query_goal():
    async with lifespan(app): # Ensure lifespan runs (tables created via conftest or lifespan)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Create Goal
            response = await ac.post("/api/v1/workflow/goals", json={
                "title": "API Test Goal",
                "description": "Testing via TestClient"
            })
            assert response.status_code == 201
            goal_id = response.json()["id"]
            assert goal_id is not None
            
            # 2. Transition
            response = await ac.post(f"/api/v1/workflow/goals/{goal_id}/advance", json={
                "target_state": WorkflowState.TASK_DECOMPOSITION.value
            })
            
            assert response.status_code == 200
            assert response.json()["new_state"] == WorkflowState.TASK_DECOMPOSITION.value
