from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)

class WorkflowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

class GenerateRequest(BaseModel):
    description: str = Field(min_length=1)

class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    input: Any = None

class ExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    status: str
    input: str
    output: str | None = None
    error: str | None = None
    retry_count: int = 0
    step_results: list[Any] = Field(default_factory=list)
    created_at: datetime
    finished_at: datetime | None = None
