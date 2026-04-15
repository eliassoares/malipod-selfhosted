from __future__ import annotations

from pydantic import BaseModel

from app.schemas.health import ReadinessCheck  # noqa: TC001


class HomePageContext(BaseModel):
    app_name: str
    environment: str
    status: str
    checks: list[ReadinessCheck]
