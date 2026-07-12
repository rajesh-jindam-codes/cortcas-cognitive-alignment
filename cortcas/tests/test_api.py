import pytest
import uuid
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

async def test_auth_workflow_and_rbac(client: AsyncClient):
    # 1. Register viewer & admin
    viewer_email = f"test_viewer_{uuid.uuid4().hex[:6]}@example.com"
    res = await client.post("/api/v1/auth/register", json={
        "email": viewer_email,
        "password": "viewerpassword123",
        "role": "viewer"
    })
    assert res.status_code == 201
    
    admin_email = f"test_admin_{uuid.uuid4().hex[:6]}@example.com"
    res = await client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": "adminpassword123",
        "role": "admin"
    })
    assert res.status_code == 201

    # 2. Login to get tokens
    # AsyncClient post with form-data can use 'data' parameter
    login_res_viewer = await client.post("/api/v1/auth/login", data={
        "username": viewer_email,
        "password": "viewerpassword123"
    })
    assert login_res_viewer.status_code == 200
    tokens_viewer = login_res_viewer.json()
    viewer_headers = {"Authorization": f"Bearer {tokens_viewer['access_token']}"}

    login_res_admin = await client.post("/api/v1/auth/login", data={
        "username": admin_email,
        "password": "adminpassword123"
    })
    assert login_res_admin.status_code == 200
    tokens_admin = login_res_admin.json()
    admin_headers = {"Authorization": f"Bearer {tokens_admin['access_token']}"}

    # 3. Test RBAC on Student creation (Post is Admin only)
    new_student = {
        "email": f"stud_{uuid.uuid4().hex[:6]}@cortcas.edu",
        "name": "Alex Mercer",
        "age": 21,
        "gender": "Male",
        "department": "Biology",
        "year_of_study": 3,
        "enrollment_date": "2026-01-10"
    }

    # Viewer should be forbidden (403)
    res = await client.post("/api/v1/students/", json=new_student, headers=viewer_headers)
    assert res.status_code == 403

    # Admin should succeed (201)
    res = await client.post("/api/v1/students/", json=new_student, headers=admin_headers)
    assert res.status_code == 201
    created_student = res.json()
    assert created_student["name"] == "Alex Mercer"

    # 4. Read access should be permitted for both (200)
    res = await client.get("/api/v1/students/", headers=viewer_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = await client.get(f"/api/v1/students/{created_student['id']}", headers=viewer_headers)
    assert res.status_code == 200

    # 5. Admin can delete, viewer cannot
    res = await client.delete(f"/api/v1/students/{created_student['id']}", headers=viewer_headers)
    assert res.status_code == 403

    res = await client.delete(f"/api/v1/students/{created_student['id']}", headers=admin_headers)
    assert res.status_code == 200

async def test_inference_endpoints(client: AsyncClient):
    # 1. Register and login admin
    admin_email = f"test_admin_{uuid.uuid4().hex[:6]}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": "adminpassword123",
        "role": "admin"
    })
    login_res = await client.post("/api/v1/auth/login", data={
        "username": admin_email,
        "password": "adminpassword123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 2. Register student and add a session
    student_email = f"student_{uuid.uuid4().hex[:6]}@cortcas.edu"
    res = await client.post("/api/v1/students/", json={
        "email": student_email,
        "name": "Diana Prince",
        "age": 22,
        "gender": "Female",
        "department": "Data Science",
        "year_of_study": 4,
        "enrollment_date": "2026-02-15"
    }, headers=headers)
    assert res.status_code == 201
    student_id = res.json()["id"]

    res = await client.post("/api/v1/sessions/", json={
        "student_id": student_id,
        "start_time": "2026-07-12T09:00:00",
        "end_time": "2026-07-12T09:45:00",
        "duration_minutes": 45,
        "engagement_score": 0.92,
        "focus_score": 0.88,
        "inactivity_duration": 30,
        "revision_count": 5,
        "wrong_answers": 1,
        "response_time": 12.5
    }, headers=headers)
    assert res.status_code == 201

    # 3. Trigger predict endpoint
    res = await client.post(f"/api/v1/predictions/predict/{student_id}", headers=headers)
    assert res.status_code == 201
    predictions = res.json()
    assert "risk_prediction" in predictions
    assert "cluster_prediction" in predictions
    assert "anomaly_prediction" in predictions
    
    # 4. Check prediction history
    res = await client.get(f"/api/v1/predictions/history/{student_id}", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 3

async def test_dashboard_endpoints(client: AsyncClient):
    # Register and login viewer
    viewer_email = f"test_viewer_{uuid.uuid4().hex[:6]}@example.com"
    await client.post("/api/v1/auth/register", json={
        "email": viewer_email,
        "password": "viewerpassword123",
        "role": "viewer"
    })
    login_res = await client.post("/api/v1/auth/login", data={
        "username": viewer_email,
        "password": "viewerpassword123"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Query dashboard summary (should execute and cache successfully)
    res = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_students" in data
    assert "avg_engagement" in data
    assert "total_anomaly_alerts" in data
    
    # Query risk students list
    res = await client.get("/api/v1/dashboard/risk-students", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Query latest alerts list
    res = await client.get("/api/v1/dashboard/alerts", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
