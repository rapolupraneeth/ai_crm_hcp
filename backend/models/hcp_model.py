from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class HCP(Base):
    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    specialty: Mapped[str | None] = mapped_column(String(128), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")
