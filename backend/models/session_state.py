from sqlalchemy import DateTime, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base
from datetime import datetime, timezone

class SessionState(Base):
    __tablename__ = "session_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hcp_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    interaction_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    follow_up_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    compliance_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

