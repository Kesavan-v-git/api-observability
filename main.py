
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from datetime import datetime
import os

from database import create_db_and_tables, get_session
from models import Project, LogEntry
from github_client import (
    fetch_file_from_github,
    get_default_branch_sha,
    create_branch,
    update_file_on_branch,
    create_pull_request,
)
from llm_client import analyze_error
from stack_trace_parser import extract_file_and_line
from patch_applier import apply_change_to_file


def _parse_timestamp(value):
    if not value:
        return datetime.utcnow()

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        return datetime.utcnow()


fastapi_app = FastAPI()


import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from database import engine  # or wherever your SQLAlchemy/SQLModel engine lives

@fastapi_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    with Session(engine) as session:
        log = LogEntry(
            project_id=YOUR_PROJECT_ID,       # see note below
            endpoint=str(request.url.path),
            method=request.method,
            status_code=500,
            stack_trace=traceback.format_exc(),
            timestamp=datetime.utcnow(),
        )
        session.add(log)
        session.commit()
        session.refresh(log)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "log_id": log.id},
    )

@fastapi_app.on_event("startup")
def on_startup():
    create_db_and_tables()

def get_or_create_default_project(session: Session) -> Project:
    project = session.exec(select(Project)).first()

    if project:
        return project

    project = Project(
        application_url="http://127.0.0.1:8002",
        github_owner="Kesavan-v-gt",
        github_repo="",
        github_token="GITHUB_TOKEN",
        llm_provider="gemini",
        llm_api_key=os.getenv("GEMINI_API_KEY"),
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


# ============================================================
# SINGLE REST ENDPOINT FOR STRUCTURED API LOG INGESTION
# ============================================================

@fastapi_app.post("/api/logs")
def receive_log(
    payload: dict,
    session: Session = Depends(get_session)
):
    api_key = payload.get("api_key")
    project_id = payload.get("project_id")

    # First try project_id
    project = (
        session.get(Project, project_id)
        if project_id
        else None
    )

    # If project_id was not found, try api_key
    if not project and api_key:
        statement = select(Project).where(
            Project.api_key == api_key
        )
        project = session.exec(statement).first()

    # Reject unknown project
    if not project:
        raise HTTPException(
            status_code=401,
            detail="Invalid api_key or project_id"
        )

    # Create structured log entry
    log = LogEntry(
        project_id=project.id,
        endpoint=payload.get("endpoint", ""),
        method=payload.get("method", ""),
        status_code=payload.get("status_code", 500),
        stack_trace=payload.get("stack_trace", ""),
        timestamp=_parse_timestamp(
            payload.get("timestamp")
        ),
    )

    # Save to SQLite database
    session.add(log)
    session.commit()
    session.refresh(log)

    print(
        f"LOG INGESTED: {log.id} | "
        f"{log.method} {log.endpoint} | "
        f"HTTP {log.status_code}"
    )

    return {
        "log_id": log.id,
        "status": "received"
    }


# ============================================================
# INVESTIGATE A STORED LOG
# ============================================================

@fastapi_app.get("/api/investigate/{log_id}")
def investigate(
    log_id: str,
    session: Session = Depends(get_session)
):
    log = session.get(LogEntry, log_id)

    if not log:
        raise HTTPException(
            status_code=404,
            detail="Log not found"
        )

    project = session.get(Project, log.project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    file_name, line_number = extract_file_and_line(
        log.stack_trace
    )

    if not file_name:
        raise HTTPException(
            status_code=422,
            detail="Could not parse stack trace"
        )

    source_code = fetch_file_from_github(
        project.github_owner,
        project.github_repo,
        file_name,
        project.github_token
    )

    diagnosis = analyze_error(
        stack_trace=log.stack_trace,
        endpoint=log.endpoint,
        status_code=log.status_code,
        file_path=file_name,
        source_code=source_code,
        api_key=project.llm_api_key,
    )

    return diagnosis


# ============================================================
# CREATE PULL REQUEST
# ============================================================

@fastapi_app.post("/api/create-pr")
def create_pr(
    payload: dict,
    session: Session = Depends(get_session)
):
    log_id = payload["log_id"]
    changes = payload["changes"]

    log = session.get(LogEntry, log_id)

    if not log:
        raise HTTPException(
            status_code=404,
            detail="Log not found"
        )

    project = session.get(Project, log.project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    base_branch, base_sha = get_default_branch_sha(
        project.github_owner,
        project.github_repo,
        project.github_token
    )

    new_branch = f"tracefix/{log.id}"

    create_branch(
        project.github_owner,
        project.github_repo,
        new_branch,
        base_sha,
        project.github_token
    )

    for change in changes:
        original = fetch_file_from_github(
            project.github_owner,
            project.github_repo,
            change["file"],
            project.github_token
        )

        patched = apply_change_to_file(
            original,
            change["start_line"],
            change["end_line"],
            change["replacement_code"]
        )

        update_file_on_branch(
            project.github_owner,
            project.github_repo,
            change["file"],
            patched,
            new_branch,
            f"TraceFix: fix for {log.id}",
            project.github_token,
        )

    pr = create_pull_request(
        project.github_owner,
        project.github_repo,
        new_branch,
        base_branch,
        title=f"TraceFix: automated fix for {log.id}",
        body=f"Automated fix generated by TraceFix for log `{log.id}`.",
        token=project.github_token,
    )

    return {
        "pr_url": pr.get("html_url"),
        "branch": new_branch
    }


# ============================================================
# CORS
# ============================================================



class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float


class Order(BaseModel):
    items: list[OrderItem]

@fastapi_app.post("/api/order/total")
def calculate_total(order: Order):
    total = 0

    for item in order.items:
        total += item.price * item.quantity

    average = total / len(order.items) if order.items else 0

    return {
        "total": total,
        "average": average
    }


fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)