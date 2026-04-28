from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"
    SKIP = "skip"


class CheckResult(BaseModel):
    id: str
    title: str
    status: Status
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)


class DiagnosticReport(BaseModel):
    tool: str = "matter-network-doctor"
    version: str
    generated_at: str
    sections: dict[str, list[CheckResult]]

