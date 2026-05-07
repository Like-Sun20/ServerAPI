from __future__ import annotations

import random
import threading
from datetime import UTC, datetime

from faker import Faker

from app.schemas.user import User, UserCreate, UserListResponse, UserUpdate

_fake = Faker("zh_CN")
_lock = threading.Lock()
_users: dict[int, User] = {}
_next_id = 1

_ROLES = ("admin", "editor", "viewer")
_STATUSES = ("active", "inactive")


def _seed_if_empty() -> None:
    global _next_id
    if _users:
        return
    now = datetime.now(UTC)
    for i in range(1, 11):
        user = User(
            id=i,
            username=_fake.unique.user_name(),
            email=_fake.unique.email(),
            role=random.choice(_ROLES),
            status=random.choice(_STATUSES),
            created_at=now,
        )
        _users[i] = user
    _next_id = max(_users.keys(), default=0) + 1


def get_all_users() -> list[User]:
    """返回全部用户（按 id 排序）。"""
    _seed_if_empty()
    with _lock:
        return sorted(_users.values(), key=lambda u: u.id)


def get_user_by_id(user_id: int) -> User | None:
    _seed_if_empty()
    with _lock:
        return _users.get(user_id)


def create_user(user_data: UserCreate) -> User:
    global _next_id
    _seed_if_empty()
    now = datetime.now(UTC)
    with _lock:
        uid = _next_id
        _next_id += 1
        user = User(
            id=uid,
            username=user_data.username,
            email=user_data.email,
            role=user_data.role,
            status=user_data.status,
            created_at=now,
        )
        _users[uid] = user
        return user


def update_user(user_id: int, user_data: UserUpdate) -> User | None:
    _seed_if_empty()
    with _lock:
        existing = _users.get(user_id)
        if existing is None:
            return None
        data = existing.model_dump()
        if user_data.username is not None:
            data["username"] = user_data.username
        if user_data.email is not None:
            data["email"] = user_data.email
        if user_data.role is not None:
            data["role"] = user_data.role
        if user_data.status is not None:
            data["status"] = user_data.status
        updated = User(**data)
        _users[user_id] = updated
        return updated


def delete_user(user_id: int) -> bool:
    _seed_if_empty()
    with _lock:
        if user_id not in _users:
            return False
        del _users[user_id]
        return True


def list_users(page: int, page_size: int) -> UserListResponse:
    """分页列表（供 Live 兼容接口使用）。"""
    _seed_if_empty()
    with _lock:
        all_items = sorted(_users.values(), key=lambda u: u.id)
    total = len(all_items)
    start = (page - 1) * page_size
    end = start + page_size
    slice_items = all_items[start:end]
    return UserListResponse(
        items=slice_items,
        total=total,
        page=page,
        page_size=page_size,
    )
