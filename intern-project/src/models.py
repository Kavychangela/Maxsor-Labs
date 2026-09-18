from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tickets = relationship(
        "Ticket",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="tickets",
    )

    decision = relationship(
        "Decision",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False,
        unique=True,
    )
    action = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    sources = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    ticket = relationship(
        "Ticket",
        back_populates="decision",
    )