"""
Load testing scenarios for AutoBiz Engine API using Locust.
Simulates realistic API usage patterns with CEO users creating and managing businesses.
"""

import random
from uuid import uuid4

from locust import HttpUser, between, task


class CEOUser(HttpUser):
    """Simulates a CEO user interacting with the AutoBiz Engine API."""

    wait_time = between(1, 3)

    def on_start(self):
        """Register a unique CEO user for this locust instance."""
        self.ceo_id = str(uuid4())
        self.business_ids = []
        # Auth is handled via bearer token using the CEO ID
        self.client.headers.update({"Authorization": f"Bearer {self.ceo_id}"})

    @task(3)
    def create_business(self):
        """Create a new business — highest frequency task."""
        idea = self._generate_idea()
        with self.client.post(
            "/api/v1/businesses/create",
            json={"idea": idea, "ceo_id": self.ceo_id},
            name="POST /businesses/create",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.business_ids.append(data["id"])
                response.success()
            elif response.status_code == 401:
                response.success()  # Auth failure is expected in some cases
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def list_businesses(self):
        """List all businesses for the current CEO."""
        with self.client.get(
            "/api/v1/businesses/",
            name="GET /businesses/",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(2)
    def get_random_business(self):
        """Fetch details of a random business owned by this CEO."""
        if not self.business_ids:
            return
        business_id = random.choice(self.business_ids)
        with self.client.get(
            f"/api/v1/businesses/{business_id}",
            name="GET /businesses/{id}",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def get_business_timeline(self):
        """Get build timeline for a random business."""
        if not self.business_ids:
            return
        business_id = random.choice(self.business_ids)
        with self.client.get(
            f"/api/v1/businesses/{business_id}/timeline",
            name="GET /businesses/{id}/timeline",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def list_approvals(self):
        """List pending approval requests."""
        with self.client.get(
            "/api/v1/approvals/pending",
            name="GET /approvals/pending",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def get_metrics(self):
        """Get metrics for a random business."""
        if not self.business_ids:
            return
        business_id = random.choice(self.business_ids)
        with self.client.get(
            f"/api/v1/metrics/{business_id}/realtime",
            name="GET /metrics/{id}/realtime",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)
    def launch_business(self):
        """Attempt to launch a building business."""
        if not self.business_ids:
            return
        business_id = random.choice(self.business_ids)
        with self.client.post(
            f"/api/v1/businesses/{business_id}/launch",
            name="POST /businesses/{id}/launch",
            catch_response=True,
        ) as response:
            # 200 (success), 400 (not building), 404 (not found) are all expected
            if response.status_code in (200, 400, 404):
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    def _generate_idea(self) -> str:
        """Generate a random business idea string."""
        adjectives = ["AI-powered", "Smart", "Automated", "Cloud-based", "Next-gen", "Intelligent"]
        domains = [
            "SaaS platform",
            "Marketplace",
            "Analytics tool",
            "Payment system",
            "CRM suite",
            "DevOps tool",
        ]
        suffixes = [
            "for enterprises",
            "for SMBs",
            "for developers",
            "for healthcare",
            "for fintech",
        ]
        return f"{random.choice(adjectives)} {random.choice(domains)} {random.choice(suffixes)}"


class UnauthenticatedUser(HttpUser):
    """Simulates unauthenticated requests to test auth rejection."""

    wait_time = between(2, 5)

    @task
    def attempt_create_without_auth(self):
        """Attempt to create a business without authentication."""
        # Create a fresh client without auth headers
        with self.client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business", "ceo_id": str(uuid4())},
            name="POST /businesses/create (unauthenticated)",
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401, got {response.status_code}")
