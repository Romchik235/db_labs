from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# --- DB setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- FastAPI app
app = FastAPI(
    docs_url="/docs",
    redoc_url=None,
    swagger_ui_parameters={"persistAuthorization": True},
    swagger_ui_css_url="/static/custom.css"
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- DB model
class WorkflowEventDB(Base):
    __tablename__ = "workflow_events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, nullable=False)
    quiz_id = Column(Integer, nullable=False)
Base.metadata.create_all(bind=engine)

# --- Pydantic models
class WorkflowEventCreate(BaseModel):
    name: str
    status: str
    user_id: int
    quiz_id: int

class WorkflowEvent(BaseModel):
    id: int
    name: str
    status: str
    timestamp: datetime.datetime
    user_id: int
    quiz_id: int
    class Config:
        from_attributes = True

# --- CRUD endpoints
@app.post("/workflowevent/", response_model=WorkflowEvent)
def create_workflow_event(event: WorkflowEventCreate):
    db = SessionLocal()
    db_event = WorkflowEventDB(
        name=event.name, status=event.status,
        user_id=event.user_id, quiz_id=event.quiz_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    db.close()
    return db_event

@app.get("/workflowevent/", response_model=List[WorkflowEvent])
def get_all_workflow_events():
    db = SessionLocal()
    events = db.query(WorkflowEventDB).all()
    db.close()
    return events

@app.get("/workflowevent/{event_id}", response_model=WorkflowEvent)
def get_workflow_event(event_id: int):
    db = SessionLocal()
    event = db.query(WorkflowEventDB).filter(WorkflowEventDB.id == event_id).first()
    db.close()
    if not event:
        raise HTTPException(status_code=404, detail="Not found")
    return event

@app.put("/workflowevent/{event_id}", response_model=WorkflowEvent)
def update_workflow_event(event_id: int, event: WorkflowEventCreate):
    db = SessionLocal()
    db_event = db.query(WorkflowEventDB).filter(WorkflowEventDB.id == event_id).first()
    if not db_event:
        db.close()
        raise HTTPException(status_code=404, detail="Not found")
    db_event.name = event.name
    db_event.status = event.status
    db_event.user_id = event.user_id
    db_event.quiz_id = event.quiz_id
    db.commit()
    db.refresh(db_event)
    db.close()
    return db_event

@app.delete("/workflowevent/{event_id}")
def delete_workflow_event(event_id: int):
    db = SessionLocal()
    db_event = db.query(WorkflowEventDB).filter(WorkflowEventDB.id == event_id).first()
    if not db_event:
        db.close()
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_event)
    db.commit()
    db.close()
    return {"ok": True}

@app.post("/workflowevent/seed/")
def seed_workflow_events():
    db = SessionLocal()
    db.query(WorkflowEventDB).delete()
    events = [
        WorkflowEventDB(name="Event A", status="new", user_id=1, quiz_id=1),
        WorkflowEventDB(name="Event B", status="in progress", user_id=2, quiz_id=1),
        WorkflowEventDB(name="Event C", status="done", user_id=1, quiz_id=2)
    ]
    db.add_all(events)
    db.commit()
    db.close()
    return {"ok": True, "count": len(events)}

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
