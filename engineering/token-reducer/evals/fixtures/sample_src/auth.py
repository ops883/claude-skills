"""Password hashing, login, and session token handling."""
import hashlib
import secrets


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    return hash_password(password, salt) == expected_hash


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


class AuthService:
    """Handles login, logout, and session token validation."""

    def __init__(self, user_store):
        self.user_store = user_store
        self.sessions = {}

    def login(self, username, password):
        user = self.user_store.get(username)
        if user is None:
            return None
        if not verify_password(password, user["salt"], user["password_hash"]):
            return None
        token = create_session_token()
        self.sessions[token] = username
        return token

    def logout(self, token):
        self.sessions.pop(token, None)

    def current_user(self, token):
        return self.sessions.get(token)
