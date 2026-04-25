from pydantic import BaseModel, Field
from typing import Optional
import datetime

class ParticipantBase(BaseModel):
    first_name: str
    last_name: str
    active: bool = True

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    active: Optional[bool] = None

class Participant(ParticipantBase):
    id: int
    
    model_config = {"from_attributes": True}

class ParticipantWithStats(Participant):
    release_count: int = 0

class ReleaseBase(BaseModel):
    version: str = Field(pattern=r'^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$', description="Semantic version like 1.2.3 or v1.2.3")
    date: Optional[datetime.datetime] = None
    participant_id: int

class ReleaseCreate(ReleaseBase):
    pass

class Release(ReleaseBase):
    id: int
    date: datetime.datetime
    participant: Participant

    model_config = {"from_attributes": True}

class NextParticipantInfo(BaseModel):
    participant: Participant
    release_count: int
    last_release_date: Optional[datetime.datetime]
