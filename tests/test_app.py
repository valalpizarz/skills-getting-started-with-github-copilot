"""
FastAPI Tests for High School Management System API

Tests follow the AAA (Arrange-Act-Assert) pattern for clear, readable test structure:
- Arrange: Set up test data and fixtures
- Act: Execute the endpoint being tested
- Assert: Verify the response and state changes
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_redirect_root_to_static_index(self, client: TestClient):
        """
        Arrange: Prepare test client
        Act: Make GET request to root endpoint
        Assert: Verify redirect response to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code in [307, 308]  # Temporary or permanent redirect
        assert "/static/index.html" in response.headers.get("location", "")

    def test_root_redirect_follows_to_static_files(self, client: TestClient):
        """
        Arrange: Prepare test client
        Act: Make GET request to root endpoint with redirect following
        Assert: Verify final response indicates redirect occurred
        """
        # Act
        response = client.get("/", follow_redirects=True)

        # Assert
        assert response.status_code == 200


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client: TestClient):
        """
        Arrange: Prepare test client
        Act: Request all activities
        Assert: Verify 9 activities are returned
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Math Team" in data

    def test_get_activities_has_required_fields(self, client: TestClient):
        """
        Arrange: Prepare test client
        Act: Request all activities
        Assert: Verify each activity has required fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity in data.items():
            assert isinstance(activity, dict)
            assert required_fields.issubset(activity.keys()), \
                f"Activity {activity_name} missing required fields"
            assert isinstance(activity["participants"], list)
            assert isinstance(activity["max_participants"], int)

    def test_get_activities_returns_preloaded_data(self, client: TestClient):
        """
        Arrange: Prepare test client
        Act: Request all activities
        Assert: Verify pre-loaded participant data is correct
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        # Chess Club should have 2 pre-loaded participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        # Programming Class should have 2 pre-loaded participants
        assert len(data["Programming Class"]["participants"]) == 2


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success_adds_participant(self, client: TestClient):
        """
        Arrange: Prepare test client and new email
        Act: Sign up a new student for an activity
        Assert: Verify success response and participant is added
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        # Verify participant was added
        activities_response = client.get("/activities")
        updated_activity = activities_response.json()[activity_name]
        assert email in updated_activity["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client: TestClient):
        """
        Arrange: Prepare test client and non-existent activity name
        Act: Attempt to sign up for activity that doesn't exist
        Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "NonexistentClub"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self, client: TestClient):
        """
        Arrange: Prepare test client and activity with pre-loaded participant
        Act: Attempt to sign up same student twice
        Assert: Verify 400 error on second signup attempt
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_multiple_students_different_activities(self, client: TestClient):
        """
        Arrange: Prepare test client and two different activities
        Act: Sign up same student for two different activities
        Assert: Verify both signups succeed
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"

        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": email}
        )
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": email}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity1]["participants"]
        assert email in activities_data[activity2]["participants"]

    def test_signup_increases_participant_count(self, client: TestClient):
        """
        Arrange: Get initial participant count for an activity
        Act: Sign up a new student
        Assert: Verify participant count increased by 1
        """
        # Arrange
        activity_name = "Art Club"
        email = "newartist@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1


class TestDeleteParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_delete_participant_success(self, client: TestClient):
        """
        Arrange: Prepare test client with pre-loaded participant
        Act: Delete participant from activity
        Assert: Verify success response and participant is removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Pre-loaded participant

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        # Verify participant was removed
        activities_response = client.get("/activities")
        updated_activity = activities_response.json()[activity_name]
        assert email not in updated_activity["participants"]

    def test_delete_nonexistent_activity_returns_404(self, client: TestClient):
        """
        Arrange: Prepare test client and non-existent activity name
        Act: Attempt to delete from activity that doesn't exist
        Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "FakeActivity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "Activity not found" in response.json()["detail"]

    def test_delete_participant_not_enrolled_returns_404(self, client: TestClient):
        """
        Arrange: Prepare test client with student not enrolled in activity
        Act: Attempt to delete student who is not a participant
        Assert: Verify 404 error response
        """
        # Arrange
        activity_name = "Soccer Club"
        email = "notstudent@mergington.edu"  # Not enrolled

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "Participant not found" in response.json()["detail"]

    def test_delete_decreases_participant_count(self, client: TestClient):
        """
        Arrange: Get initial participant count for an activity
        Act: Delete a participant
        Assert: Verify participant count decreased by 1
        """
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"  # Pre-loaded participant
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in final_response.json()[activity_name]["participants"]

    def test_delete_then_signup_same_activity(self, client: TestClient):
        """
        Arrange: Prepare test client with pre-loaded participant
        Act: Delete participant then sign them up again
        Assert: Verify both operations succeed
        """
        # Arrange
        activity_name = "Drama Club"
        email = "isabella@mergington.edu"

        # Act - Delete first
        delete_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert delete_response.status_code == 200
        assert signup_response.status_code == 200
        final_response = client.get("/activities")
        assert email in final_response.json()[activity_name]["participants"]
