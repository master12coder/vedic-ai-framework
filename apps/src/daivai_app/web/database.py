"""SQLite database layer — SQLModel tables and session management.

Single-file database with users, clients, and daily cache.
Zero config — creates SQLite file on first use.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sqlmodel import Field, Session, SQLModel, create_engine, select


class User(SQLModel, table=True):  # type: ignore[call-arg]
    """Google OAuth user."""

    id: int | None = Field(default=None, primary_key=True)
    google_id: str = Field(unique=True, index=True)
    email: str = Field(index=True)
    name: str
    picture_url: str | None = None
    role: str = Field(default="family")  # owner | pandit | family
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(default_factory=datetime.now)


class Client(SQLModel, table=True):  # type: ignore[call-arg]
    """A person whose chart has been computed."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    name: str
    name_hi: str | None = None
    dob: str  # DD/MM/YYYY
    tob: str  # HH:MM
    place: str
    lat: float
    lon: float
    gender: str
    chart_json: str  # Full ChartData serialized
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DailyCache(SQLModel, table=True):  # type: ignore[call-arg]
    """Cached daily guidance to avoid recomputation."""

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(index=True)
    date: str  # YYYY-MM-DD
    guidance_json: str


_engine = None


def get_engine() -> Any:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///data/daivai.db")
        db_path = db_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(db_url, echo=False)
        SQLModel.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    """Create a new database session."""
    return Session(get_engine())


def reset_engine() -> None:
    """Reset engine for testing."""
    global _engine
    _engine = None


# ── User CRUD ────────────────────────────────────────────────────────────


def get_or_create_user(
    google_id: str, email: str, name: str, picture_url: str | None = None
) -> User:
    """Find existing user by Google ID or create a new one."""
    with get_session() as session:
        stmt = select(User).where(User.google_id == google_id)
        user = session.exec(stmt).first()
        if user:
            user.last_login = datetime.now()
            user.name = name
            if picture_url:
                user.picture_url = picture_url
            session.add(user)
            session.commit()
            session.refresh(user)
            return cast(User, user)

        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture_url=picture_url,
        )
        # First user becomes owner
        existing = session.exec(select(User)).first()
        if existing is None:
            user.role = "owner"
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def get_user_by_id(user_id: int) -> User | None:
    """Fetch a user by primary key."""
    with get_session() as session:
        return cast(User | None, session.get(User, user_id))


# ── Client CRUD ──────────────────────────────────────────────────────────


def create_client(
    user_id: int,
    name: str,
    dob: str,
    tob: str,
    place: str,
    lat: float,
    lon: float,
    gender: str,
    chart_json: str,
) -> Client:
    """Create a new client record with computed chart data."""
    with get_session() as session:
        client = Client(
            user_id=user_id,
            name=name,
            dob=dob,
            tob=tob,
            place=place,
            lat=lat,
            lon=lon,
            gender=gender,
            chart_json=chart_json,
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        return client


def get_client(client_id: int) -> Client | None:
    """Fetch a client by ID."""
    with get_session() as session:
        return cast(Client | None, session.get(Client, client_id))


def get_clients_for_user(user_id: int) -> list[Client]:
    """Get all clients belonging to a user."""
    with get_session() as session:
        stmt = select(Client).where(Client.user_id == user_id).order_by(Client.updated_at.desc())  # type: ignore[attr-defined]
        return list(session.exec(stmt).all())


def delete_client(client_id: int, user_id: int) -> bool:
    """Delete a client (only if owned by user)."""
    with get_session() as session:
        client = session.get(Client, client_id)
        if client and client.user_id == user_id:
            session.delete(client)
            session.commit()
            return True
        return False
