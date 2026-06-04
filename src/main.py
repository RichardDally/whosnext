import os
import logging
import datetime
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from src import models, schemas, database
from src.database import engine
from src.__version__ import __version__


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.info(f"Starting Who's Next version {__version__}")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Who's Next?", version=__version__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def read_index():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/api/participants", response_model=List[schemas.ParticipantWithStats])
def read_participants(db: Session = Depends(database.get_db)):
    participants = db.query(models.Participant).all()
    result = []
    for p in participants:
        count = db.query(models.Release).filter(models.Release.participant_id == p.id).count()
        p_dict = schemas.Participant.model_validate(p).model_dump()
        p_dict["release_count"] = count
        result.append(p_dict)
    return result

@app.post("/api/participants", response_model=schemas.Participant)
def create_participant(participant: schemas.ParticipantCreate, db: Session = Depends(database.get_db)):
    # Check uniqueness
    existing_first = db.query(models.Participant).filter(models.Participant.first_name == participant.first_name).first()
    if existing_first:
        raise HTTPException(status_code=400, detail="First name must be unique")
    existing_last = db.query(models.Participant).filter(models.Participant.last_name == participant.last_name).first()
    if existing_last:
        raise HTTPException(status_code=400, detail="Last name must be unique")
    
    db_participant = models.Participant(**participant.model_dump())
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant

@app.put("/api/participants/{participant_id}", response_model=schemas.Participant)
def update_participant(participant_id: int, participant: schemas.ParticipantUpdate, db: Session = Depends(database.get_db)):
    db_participant = db.query(models.Participant).filter(models.Participant.id == participant_id).first()
    if not db_participant:
        raise HTTPException(status_code=404, detail="Participant not found")
        
    if participant.first_name is not None:
        existing_first = db.query(models.Participant).filter(models.Participant.first_name == participant.first_name, models.Participant.id != participant_id).first()
        if existing_first:
            raise HTTPException(status_code=400, detail="First name must be unique")
        db_participant.first_name = participant.first_name
        
    if participant.last_name is not None:
        existing_last = db.query(models.Participant).filter(models.Participant.last_name == participant.last_name, models.Participant.id != participant_id).first()
        if existing_last:
            raise HTTPException(status_code=400, detail="Last name must be unique")
        db_participant.last_name = participant.last_name
        
    if participant.active is not None:
        db_participant.active = participant.active
        
    db.commit()
    db.refresh(db_participant)
    return db_participant

@app.get("/api/releases", response_model=List[schemas.Release])
def read_releases(db: Session = Depends(database.get_db)):
    return db.query(models.Release).order_by(models.Release.date.desc()).all()

@app.post("/api/releases", response_model=schemas.Release)
def create_release(release: schemas.ReleaseCreate, db: Session = Depends(database.get_db)):
    existing_release = db.query(models.Release).filter(models.Release.version == release.version).first()
    if existing_release:
        raise HTTPException(status_code=400, detail="Version already exists")
        
    dumped = release.model_dump()
    if not dumped.get("date"):
        dumped["date"] = datetime.datetime.now(datetime.timezone.utc)
    db_release = models.Release(**dumped)
    db.add(db_release)
    db.commit()
    db.refresh(db_release)
    return db_release

@app.delete("/api/releases/{release_id}")
def delete_release(release_id: int, db: Session = Depends(database.get_db)):
    db_release = db.query(models.Release).filter(models.Release.id == release_id).first()
    if not db_release:
        raise HTTPException(status_code=404, detail="Release not found")
    db.delete(db_release)
    db.commit()
    return {"detail": "Release deleted"}

@app.get("/api/next", response_model=schemas.NextParticipantInfo)
def get_next(db: Session = Depends(database.get_db)):
    active_participants = db.query(models.Participant).filter(models.Participant.active).all()
    if not active_participants:
        raise HTTPException(status_code=404, detail="No participants available")
    
    participant_stats = []
    for p in active_participants:
        releases = db.query(models.Release).filter(models.Release.participant_id == p.id).all()
        release_count = len(releases)
        last_release_date = max([r.date for r in releases]) if releases else None
        participant_stats.append({
            "participant": p,
            "release_count": release_count,
            "last_release_date": last_release_date
        })
    
    def sort_key(stat):
        # We want None to be treated as older than any date.
        lrd = stat["last_release_date"] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        if lrd.tzinfo is None:
            lrd = lrd.replace(tzinfo=datetime.timezone.utc)
        return (stat["release_count"], lrd, stat["participant"].first_name.lower())
    
    participant_stats.sort(key=sort_key)
    
    next_stat = participant_stats[0]
    return schemas.NextParticipantInfo(
        participant=next_stat["participant"],
        release_count=next_stat["release_count"],
        last_release_date=next_stat["last_release_date"]
    )
