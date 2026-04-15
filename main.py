import os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import CustodyLog, Evidence
from security import hash_block, sha256_hex


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="SecureChain - Digital Evidence Chain of Custody")

if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
else:
    templates = Jinja2Templates(directory=str(BASE_DIR))


@app.on_event("startup")
def on_startup() -> None:
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    evidences: List[Evidence] = db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "evidences": evidences,
        },
    )


@app.post("/upload")
async def upload_evidence(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    save_path = UPLOAD_DIR / file.filename
    content = await file.read()

    with open(save_path, "wb") as f:
        f.write(content)

    file_hash = sha256_hex(content)
    evidence = Evidence(filename=file.filename, file_hash=file_hash)
    db.add(evidence)
    db.flush()  # assign ID

    timestamp = datetime.utcnow()
    current_hash = hash_block(
        action="UPLOAD",
        file_hash=file_hash,
        timestamp=timestamp,
        previous_hash="GENESIS",
    )

    log = CustodyLog(
        evidence_id=evidence.id,
        action="UPLOAD",
        timestamp=timestamp,
        previous_hash="GENESIS",
        current_hash=current_hash,
        details="Initial upload of evidence file.",
    )
    db.add(log)
    db.commit()
    db.refresh(evidence)

    if request.headers.get("accept", "").lower().startswith("text/html"):
        evidences: List[Evidence] = db.execute(select(Evidence).order_by(Evidence.created_at.desc())).scalars().all()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "evidences": evidences, "message": f"Uploaded evidence ID {evidence.id}."},
        )

    return {"evidence_id": evidence.id, "file_hash": evidence.file_hash}


@app.post("/access/{evidence_id}")
def log_access(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    last_log = (
        db.execute(
            select(CustodyLog)
            .where(CustodyLog.evidence_id == evidence_id)
            .order_by(CustodyLog.timestamp.desc(), CustodyLog.id.desc())
        )
        .scalars()
        .first()
    )

    previous_hash = last_log.current_hash if last_log else "GENESIS"
    timestamp = datetime.utcnow()
    current_hash = hash_block(
        action="ACCESS",
        file_hash=evidence.file_hash,
        timestamp=timestamp,
        previous_hash=previous_hash,
    )

    log = CustodyLog(
        evidence_id=evidence_id,
        action="ACCESS",
        timestamp=timestamp,
        previous_hash=previous_hash,
        current_hash=current_hash,
        details="Evidence accessed.",
    )
    db.add(log)
    db.commit()

    return {"status": "Access logged", "evidence_id": evidence_id, "log_id": log.id}


@app.get("/logs/{evidence_id}")
def get_logs(evidence_id: int, db: Session = Depends(get_db)):
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    logs = (
        db.execute(
            select(CustodyLog)
            .where(CustodyLog.evidence_id == evidence_id)
            .order_by(CustodyLog.timestamp.asc(), CustodyLog.id.asc())
        )
        .scalars()
        .all()
    )

    return {
        "evidence": {
            "id": evidence.id,
            "filename": evidence.filename,
            "file_hash": evidence.file_hash,
            "created_at": evidence.created_at,
        },
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "timestamp": log.timestamp,
                "previous_hash": log.previous_hash,
                "current_hash": log.current_hash,
                "details": log.details,
            }
            for log in logs
        ],
    }


@app.get("/verify/{evidence_id}")
def verify_chain(evidence_id: int, db: Session = Depends(get_db)):
    evidence = db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    logs: List[CustodyLog] = (
        db.execute(
            select(CustodyLog)
            .where(CustodyLog.evidence_id == evidence_id)
            .order_by(CustodyLog.timestamp.asc(), CustodyLog.id.asc())
        )
        .scalars()
        .all()
    )

    if not logs:
        return {"status": "No logs", "detail": "No custody records found for this evidence."}

    prev_current_hash = None
    for idx, log in enumerate(logs):
        expected_prev = prev_current_hash or "GENESIS"
        if log.previous_hash != expected_prev:
            return {
                "status": "Tampering Detected",
                "detail": f"Log ID {log.id} has invalid previous_hash.",
                "at_log_id": log.id,
            }

        recalculated_current = hash_block(
            action=log.action,
            file_hash=evidence.file_hash,
            timestamp=log.timestamp,
            previous_hash=log.previous_hash,
        )
        if log.current_hash != recalculated_current:
            return {
                "status": "Tampering Detected",
                "detail": f"Log ID {log.id} has invalid current_hash.",
                "at_log_id": log.id,
            }

        prev_current_hash = log.current_hash

    return {"status": "Integrity Verified", "logs_checked": len(logs)}


# Optional: simple static mount if you later add CSS/JS
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

