from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ApiRootResponse(BaseModel):
    name: str
    status: Literal["starting", "ready", "degraded"]
    docs: str


class HealthStatus(BaseModel):
    status: Literal["alive"]


class ReadinessCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class ReadinessStatus(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: list[ReadinessCheck]
