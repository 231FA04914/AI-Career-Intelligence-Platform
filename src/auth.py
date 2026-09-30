"""
User Authentication, Access Control & Security Layer (Milestone 4 - Task 7)
Provides secure password hashing (PBKDF2-HMAC-SHA256), session tokens,
user registration, authentication, and multi-tenant access validation.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import uuid
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Default secret for signing session tokens (override via environment in production)
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "career-intel-auth-secret-key-2026-production")
PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt.
    
    Args:
        password: Raw password string.
        salt: Optional hexadecimal salt string. If None, a new salt is generated.
        
    Returns:
        Tuple of (hex_password_hash, hex_salt)
    """
    if not salt:
        salt = secrets.token_hex(16)
    
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        PBKDF2_ITERATIONS
    )
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify a plaintext password against stored hash and salt in constant time.
    """
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, password_hash)


def generate_session_token(user_id: str, username: str, role: str = "user", expires_in_hours: int = 24) -> str:
    """
    Generate a cryptographically signed session token.
    Token structure: payload_hex.signature_hex
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + (expires_in_hours * 3600),
        "nonce": secrets.token_hex(8)
    }
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_hex = payload_json.encode('utf-8').hex()
    signature = hmac.new(AUTH_SECRET_KEY.encode('utf-8'), payload_hex.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload_hex}.{signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate and decode a signed session token.
    
    Returns:
        User payload dictionary if valid and unexpired, None otherwise.
    """
    if not token or "." not in token:
        return None
    try:
        payload_hex, signature = token.split(".", 1)
        expected_signature = hmac.new(
            AUTH_SECRET_KEY.encode('utf-8'),
            payload_hex.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            logger.warning("Session token signature verification failed.")
            return None

        payload_json = bytes.fromhex(payload_hex).decode('utf-8')
        payload = json.loads(payload_json)

        # Check expiration
        if payload.get("exp", 0) < time.time():
            logger.info(f"Session token expired for user {payload.get('username')}.")
            return None

        return payload
    except Exception as e:
        logger.warning(f"Error parsing session token: {e}")
        return None


class AuthManager:
    """
    Manages user registration, login authentication, session management,
    and multi-tenant access control.
    """

    def __init__(self, db_manager=None):
        from src.database import DatabaseManager
        self.db = db_manager or DatabaseManager()
        self._ensure_default_demo_user()

    def _ensure_default_demo_user(self):
        """Seed a standard demo user if no users exist in database."""
        try:
            demo_user = self.db.get_user_by_username("demo_user")
            if not demo_user:
                self.register_user(
                    username="demo_user",
                    email="demo@meetingintel.ai",
                    password="DemoUser2026!",
                    role="admin"
                )
                logger.info("Created default demo user: demo_user / DemoUser2026!")
        except Exception as e:
            logger.warning(f"Failed to ensure demo user: {e}")

    def register_user(self, username: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        """
        Register a new user account with hashed credentials.
        """
        username = username.strip().lower()
        email = email.strip().lower()

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email address format.")

        # Check if username or email already exists
        existing_user = self.db.get_user_by_username(username)
        if existing_user:
            raise ValueError(f"Username '{username}' is already taken.")

        existing_email = self.db.get_user_by_email(email)
        if existing_email:
            raise ValueError(f"Email '{email}' is already registered.")

        password_hash, salt = hash_password(password)
        user_id = self.db.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            role=role
        )

        return {
            "id": user_id,
            "username": username,
            "email": email,
            "role": role,
            "token": generate_session_token(user_id, username, role)
        }

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials and return user object with signed session token.
        """
        identifier = username_or_email.strip().lower()
        user = self.db.get_user_by_username(identifier)
        if not user:
            user = self.db.get_user_by_email(identifier)

        if not user:
            logger.warning(f"Authentication failed: user '{identifier}' not found.")
            return None

        if not verify_password(password, user["password_hash"], user["salt"]):
            logger.warning(f"Authentication failed: invalid password for user '{identifier}'.")
            return None

        token = generate_session_token(user["id"], user["username"], user.get("role", "user"))
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "token": token
        }

    def validate_access(self, user_id: Optional[str], meeting_user_id: Optional[str]) -> bool:
        """
        Verify if a given user has permission to access a specific meeting.
        - If meeting_user_id is None (public/legacy), any authenticated user or demo user can access.
        - If meeting_user_id is specified, only that matching user (or admin) can access.
        """
        if meeting_user_id is None:
            return True
        if user_id is None:
            return False
        if user_id == meeting_user_id:
            return True
        
        # Check if user is admin
        user = self.db.get_user_by_id(user_id)
        if user and user.get("role") == "admin":
            return True

        return False

    def list_registered_users(self) -> List[Dict[str, Any]]:
        """Return list of registered user profiles (id, username, email, role, created_at)."""
        return self.db.list_users()

