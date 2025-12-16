"""
Tests for the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    from app import activities
    original_state = {k: {"participants": v["participants"].copy()} for k, v in activities.items()}
    
    yield
    
    # Restore original state
    for activity_name, data in original_state.items():
        activities[activity_name]["participants"] = data["participants"]


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activities_have_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student(self, client, reset_activities):
        """Test signing up a new student"""
        from app import activities
        
        initial_count = len(activities["Chess Club"]["participants"])
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert len(activities["Chess Club"]["participants"]) == initial_count + 1
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test signing up a student who is already registered"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_fills_activity(self, client, reset_activities):
        """Test that activities can reach max capacity"""
        from app import activities
        
        # Debate Team has max 10 participants, currently has 1
        activity = activities["Debate Team"]
        original_count = len(activity["participants"])
        
        # Sign up new students until reaching max
        for i in range(activity["max_participants"] - original_count):
            email = f"student{i}@mergington.edu"
            response = client.post(
                "/activities/Debate%20Team/signup?email=" + email
            )
            assert response.status_code == 200
        
        # Try to sign up one more (should still succeed as we don't check capacity)
        response = client.post(
            "/activities/Debate%20Team/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_student(self, client, reset_activities):
        """Test unregistering a student from an activity"""
        from app import activities
        
        initial_count = len(activities["Chess Club"]["participants"])
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_student(self, client):
        """Test unregistering a student who is not registered"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
