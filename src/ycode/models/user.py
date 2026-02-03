from __future__ import annotations

from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .token import RefreshToken


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)

    about: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )    
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    refresh_tokens: Mapped[List[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    
    oauth_accounts: Mapped[List[OAuthUser]] = relationship(                
        "OAuthUser",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    is_profile_complete: Mapped[bool] = mapped_column(default=False, nullable=False)

class OAuthUser(Base):
    __tablename__ = "oauth_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    access_token: Mapped[str] = mapped_column(String(512), nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),    
        nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="oauth_accounts")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )