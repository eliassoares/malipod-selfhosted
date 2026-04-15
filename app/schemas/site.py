from pydantic import BaseModel

from app.schemas.health import ReadinessCheck


class HomePageContext(BaseModel):
    app_name: str
    environment: str
    status: str
    checks: list[ReadinessCheck]
