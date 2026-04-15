from __future__ import annotations

from datetime import datetime  # noqa: TC003

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationSurfaceModel(Base):
    __tablename__ = "application_surfaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    surface_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    surface_type: Mapped[str] = mapped_column(String(32), nullable=False)
    route_prefix: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    checks: Mapped[list[ReadinessCheckModel]] = relationship(
        back_populates="surface",
        cascade="all, delete-orphan",
    )


class ReadinessCheckModel(Base):
    __tablename__ = "readiness_checks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    surface_id: Mapped[int] = mapped_column(
        ForeignKey("application_surfaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[str] = mapped_column(String(255), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    surface: Mapped[ApplicationSurfaceModel] = relationship(back_populates="checks")
