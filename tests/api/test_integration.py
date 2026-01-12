from fastapi.testclient import TestClient
from src.api.main import app
from src.core.workflow.state import WorkflowState

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_and_query_goal():
    # 1. Create Goal
    response = client.post("/api/v1/workflow/goals", json={
        "title": "API Test Goal",
        "description": "Testing via TestClient"
    })
    assert response.status_code == 201
    goal_id = response.json()["id"]
    assert goal_id is not None
    
    # 2. Transition (Should fail guard if descriptions are checked, but guard only checks existence)
    # The guard checks if goal.title and goal.description exist, which they do.
    response = client.post(f"/api/v1/workflow/goals/{goal_id}/advance", json={
        "target_state": WorkflowState.TASK_DECOMPOSITION.value
    })
    
    assert response.status_code == 200
    assert response.json()["new_state"] == WorkflowState.TASK_DECOMPOSITION.value
