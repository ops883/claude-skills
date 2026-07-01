"""Plain dataclasses for User and Order records (eval distractor file)."""
from dataclasses import dataclass, field


@dataclass
class User:
    username: str
    email: str
    salt: str = ""
    password_hash: str = ""


@dataclass
class Order:
    order_id: str
    user_username: str
    items: list = field(default_factory=list)
    total_cents: int = 0
