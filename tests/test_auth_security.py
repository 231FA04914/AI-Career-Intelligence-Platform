"""
User Access & Security Validation Tests (Milestone 4 - Task 7)
Validates:
- User registration & input validation
- Password hashing & cryptographic salt verification
- Signed session tokens & tamper protection
- Multi-tenant data isolation (User A vs User B access control)
- Unauthorized access prevention
"""

import pytest
import tempfile
from pathlib import Path

from src.database import DatabaseManager
from src.auth import (
    hash_password,
    verify_password,
    generate_session_token,
    verify_session_token,
    AuthManager
)


@pytest.fixture
def temp_db():
    """Create an isolated temporary database for auth testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = DatabaseManager(db_path=db_path)
    yield db
    if Path(db_path).exists():
        try:
            Path(db_path).unlink()
        except Exception:
            pass


@pytest.fixture
def auth_mgr(temp_db):
    """Create AuthManager instance connected to temp_db."""
    return AuthManager(db_manager=temp_db)


def test_password_hashing_and_verification():
    """Test PBKDF2 password hashing and constant-time verification."""
    password = "SecurePassword2026!"
    pw_hash, salt = hash_password(password)

    assert pw_hash is not None and len(pw_hash) == 64
    assert salt is not None and len(salt) == 32

    # Verification with correct password
    assert verify_password(password, pw_hash, salt) is True

    # Verification with incorrect password
    assert verify_password("WrongPassword!", pw_hash, salt) is False


def test_session_token_lifecycle_and_tamper_detection():
    """Test session token generation, validation, and anti-tamper signature."""
    user_id = "usr_test123"
    username = "alice"
    token = generate_session_token(user_id, username, role="user")

    assert token is not None and "." in token

    # Valid token verification
    payload = verify_session_token(token)
    assert payload is not None
    assert payload["user_id"] == user_id
    assert payload["username"] == username
    assert payload["role"] == "user"

    # Tampered token verification must fail
    tampered_token = token[:-4] + "abcd"
    assert verify_session_token(tampered_token) is None

    # Invalid string verification
    assert verify_session_token("invalid_token_string") is None


def test_user_registration_and_validation(auth_mgr):
    """Test user registration constraints and duplicate rejection."""
    # Successful registration
    user = auth_mgr.register_user("charlie", "charlie@example.com", "SecretPass123!", role="user")
    assert user["username"] == "charlie"
    assert user["email"] == "charlie@example.com"
    assert user["token"] is not None

    # Duplicate username rejection
    with pytest.raises(ValueError, match="already taken"):
        auth_mgr.register_user("charlie", "other@example.com", "SecretPass123!")

    # Duplicate email rejection
    with pytest.raises(ValueError, match="already registered"):
        auth_mgr.register_user("other_user", "charlie@example.com", "SecretPass123!")

    # Short password rejection
    with pytest.raises(ValueError, match="at least 6 characters"):
        auth_mgr.register_user("newuser", "new@example.com", "123")


def test_user_authentication(auth_mgr):
    """Test user login via username and email."""
    auth_mgr.register_user("diana", "diana@domain.com", "DianaPass2026!")

    # Login by username
    u1 = auth_mgr.authenticate_user("diana", "DianaPass2026!")
    assert u1 is not None
    assert u1["username"] == "diana"

    # Login by email
    u2 = auth_mgr.authenticate_user("diana@domain.com", "DianaPass2026!")
    assert u2 is not None
    assert u2["username"] == "diana"

    # Login with wrong password
    assert auth_mgr.authenticate_user("diana", "WrongPass") is None

    # Login with non-existent user
    assert auth_mgr.authenticate_user("nonexistent", "Pass") is None


def test_multi_tenant_meeting_isolation(temp_db, auth_mgr):
    """Verify that User A cannot access User B's private meetings (Task 7 Requirement)."""
    # Create User A and User B
    user_a = auth_mgr.register_user("user_a", "usera@example.com", "PasswordA123!")
    user_b = auth_mgr.register_user("user_b", "userb@example.com", "PasswordB123!")

    # User A creates a meeting
    meeting_a_id = temp_db.save_meeting_intelligence(
        title="User A Secret Strategy",
        transcript_text="Confidential roadmap for User A.",
        summary_text="Strategy discussion.",
        decisions=["Launch product in Q4"],
        action_items=[{"action": "Finalize budget", "owner": "Alice", "priority": "High"}],
        participants=[{"name": "Alice", "role": "Lead"}],
        user_id=user_a["id"]
    )

    # User B creates a meeting
    meeting_b_id = temp_db.save_meeting_intelligence(
        title="User B Marketing Plan",
        transcript_text="Marketing campaigns for User B.",
        summary_text="Marketing discussion.",
        decisions=["Run ad campaigns"],
        action_items=[{"action": "Design banners", "owner": "Bob", "priority": "Medium"}],
        participants=[{"name": "Bob", "role": "Designer"}],
        user_id=user_b["id"]
    )

    # 1. User A retrieves meetings list -> should only see User A's meetings (and shared/legacy)
    user_a_meetings = temp_db.get_all_meetings(user_id=user_a["id"])
    user_a_meeting_ids = [m["id"] for m in user_a_meetings]
    assert meeting_a_id in user_a_meeting_ids
    assert meeting_b_id not in user_a_meeting_ids

    # 2. User B retrieves meetings list -> should only see User B's meetings
    user_b_meetings = temp_db.get_all_meetings(user_id=user_b["id"])
    user_b_meeting_ids = [m["id"] for m in user_b_meetings]
    assert meeting_b_id in user_b_meeting_ids
    assert meeting_a_id not in user_b_meeting_ids

    # 3. Direct access check: User B attempting to fetch User A's private meeting
    assert temp_db.get_meeting(meeting_a_id, user_id=user_b["id"]) is None
    # User A fetching own meeting
    assert temp_db.get_meeting(meeting_a_id, user_id=user_a["id"]) is not None

    # 4. Deletion check: User B attempting to delete User A's meeting must be rejected
    assert temp_db.delete_meeting(meeting_a_id, user_id=user_b["id"]) is False
    # Ensure meeting A is still in the database
    assert temp_db.get_meeting(meeting_a_id, user_id=user_a["id"]) is not None

    # 5. User A deleting own meeting succeeds
    assert temp_db.delete_meeting(meeting_a_id, user_id=user_a["id"]) is True


def test_unauthenticated_session_and_login_flow(auth_mgr):
    """Verify that unauthenticated state defaults to None and valid credentials log in."""
    from unittest.mock import MagicMock
    import streamlit as st

    # Simulate empty session state
    st.session_state.clear()
    assert st.session_state.get("auth_user") is None

    # Test authentication with valid demo credentials
    user = auth_mgr.authenticate_user("demo_user", "DemoUser2026!")
    assert user is not None
    st.session_state["auth_user"] = user
    assert st.session_state.get("auth_user")["username"] == "demo_user"

    # Test logout
    st.session_state["auth_user"] = None
    assert st.session_state.get("auth_user") is None

