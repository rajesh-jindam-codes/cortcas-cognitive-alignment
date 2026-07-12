import random
import uuid
from locust import HttpUser, task, between

class CortcasLoadTestUser(HttpUser):
    # Simulated think time between tasks: 1 to 5 seconds
    wait_time = between(1.0, 5.0)
    
    def on_start(self):
        """Perform user login and capture authorization headers."""
        self.auth_headers = {}
        self.student_ids = []
        
        # Register a temporary load-test user
        self.user_email = f"load_user_{uuid.uuid4().hex[:6]}@loadtest.com"
        self.client.post("/api/v1/auth/register", json={
            "email": self.user_email,
            "password": "loadpassword123",
            "role": "admin"  # allows writes to test full functionality
        })
        
        # Log in
        login_res = self.client.post("/api/v1/auth/login", data={
            "username": self.user_email,
            "password": "loadpassword123"
        })
        
        if login_res.status_code == 200:
            token = login_res.json()["access_token"]
            self.auth_headers = {"Authorization": f"Bearer {token}"}
            
        # Get some student IDs to use in predictions
        students_res = self.client.get("/api/v1/students/?limit=20", headers=self.auth_headers)
        if students_res.status_code == 200:
            self.student_ids = [s["id"] for s in students_res.json()]

    @task(5)
    def view_dashboard(self):
        """Fetch dashboard aggregated summary and risk metrics."""
        self.client.get("/api/v1/dashboard/summary", headers=self.auth_headers)
        self.client.get("/api/v1/dashboard/risk-students", headers=self.auth_headers)
        self.client.get("/api/v1/dashboard/alerts", headers=self.auth_headers)

    @task(3)
    def list_students(self):
        """Simulate browsing students directory."""
        self.client.get("/api/v1/students/?limit=50", headers=self.auth_headers)

    @task(2)
    def view_prediction_history(self):
        """Fetch a random student's prediction records."""
        if self.student_ids:
            student_id = random.choice(self.student_ids)
            self.client.get(f"/api/v1/predictions/history/{student_id}", headers=self.auth_headers)

    @task(1)
    def trigger_prediction(self):
        """Trigger an on-demand prediction (writes to DB, invalidates cache)."""
        if self.student_ids:
            student_id = random.choice(self.student_ids)
            self.client.post(f"/api/v1/predictions/predict/{student_id}", headers=self.auth_headers)
