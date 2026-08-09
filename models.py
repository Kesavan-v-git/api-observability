from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

class Project(SQLModel, table=True):
    id: str = Field(default_factory=lambda: generate_id("proj"), primary_key=True)
    api_key: str = Field(default_factory=lambda: generate_id("key"))
    application_url: str
    github_owner: str
    github_repo: str
    github_token: str
    llm_provider: str
    llm_api_key: str
    status: str = "connected"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LogEntry(SQLModel, table=True):
    id: str = Field(default_factory=lambda: generate_id("log"), primary_key=True)
    project_id: str
    endpoint: str
    method: str
    status_code: int
    stack_trace: str
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)