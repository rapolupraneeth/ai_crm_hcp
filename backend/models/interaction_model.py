from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))  # 'materials' or 'samples'
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    interaction = relationship("Interaction", back_populates="uploaded_files")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id", ondelete="CASCADE"), index=True)
    interaction_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[str | None] = mapped_column(String(64), nullable=True)  # YYYY-MM-DD
    time: Mapped[str | None] = mapped_column(String(64), nullable=True)  # HH:MM:SS
    attendees: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list or comma-separated
    materials: Mapped[str | None] = mapped_column(Text, nullable=True)
    samples: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Store original user message
    follow_up_required: Mapped[bool] = mapped_column(default=False)
    interaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    hcp = relationship("HCP", back_populates="interactions")
    follow_ups = relationship("FollowUp", back_populates="interaction", cascade="all, delete-orphan")
    edit_history = relationship(
        "InteractionEditHistory",
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    uploaded_files = relationship("UploadedFile", back_populates="interaction", cascade="all, delete-orphan")
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id", ondelete="CASCADE"), index=True)
    interaction_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[str | None] = mapped_column(String(64), nullable=True)  # YYYY-MM-DD
    time: Mapped[str | None] = mapped_column(String(64), nullable=True)  # HH:MM:SS
    attendees: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list or comma-separated
    materials: Mapped[str | None] = mapped_column(Text, nullable=True)
    samples: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Store original user message
    follow_up_required: Mapped[bool] = mapped_column(default=False)
    interaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    hcp = relationship("HCP", back_populates="interactions")
    follow_ups = relationship("FollowUp", back_populates="interaction", cascade="all, delete-orphan")
    edit_history = relationship(
        "InteractionEditHistory",
        back_populates="interaction",
        cascade="all, delete-orphan",
    )


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interaction_id: Mapped[int] = mapped_column(
        ForeignKey("interactions.id", ondelete="CASCADE"), index=True
    )
    suggestion: Mapped[str] = mapped_column(Text)
    due_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    interaction = relationship("Interaction", back_populates="follow_ups")


class InteractionEditHistory(Base):
    __tablename__ = "interaction_edit_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interaction_id: Mapped[int] = mapped_column(
        ForeignKey("interactions.id", ondelete="CASCADE"), index=True
    )
    original_snapshot: Mapped[str] = mapped_column(Text)
    edited_snapshot: Mapped[str] = mapped_column(Text)
    edit_instruction: Mapped[str] = mapped_column(Text)
    edited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    interaction = relationship("Interaction", back_populates="edit_history")
