from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from src.database import Base

class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, unique=True, index=True, nullable=False)
    last_name = Column(String, unique=True, index=True, nullable=False)
    active = Column(Boolean, default=True)

    releases = relationship("Release", back_populates="participant")


class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, index=True, nullable=False)
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)

    participant = relationship("Participant", back_populates="releases")
