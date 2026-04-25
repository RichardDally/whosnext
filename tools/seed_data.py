import sys
from pathlib import Path
import random
import datetime

# Ensure the root of the project is in PYTHONPATH so 'src' can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database import SessionLocal, engine
from src import models

def seed():
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Define bots
        bots = [
            ("Pepper", "bot-1"),
            ("Roomba", "bot-2"),
            ("Zed", "bot-3"),
            ("Alfred", "bot-4")
        ]
        
        # Create bots if they don't exist
        participant_ids = []
        for first, last in bots:
            p = db.query(models.Participant).filter_by(first_name=first).first()
            if not p:
                p = models.Participant(first_name=first, last_name=last, active=True)
                db.add(p)
                db.commit()
                db.refresh(p)
                print(f"Created participant: {first} {last}")
            else:
                print(f"Participant already exists: {first} {last}")
            participant_ids.append(p.id)
            
        # Define Quarters for 2026
        quarters = [
            (datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 3, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)),
            (datetime.datetime(2026, 4, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 6, 30, 23, 59, 59, tzinfo=datetime.timezone.utc)),
            (datetime.datetime(2026, 7, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 9, 30, 23, 59, 59, tzinfo=datetime.timezone.utc)),
            (datetime.datetime(2026, 10, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2026, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)),
        ]
        
        # Find highest version number to avoid uniqueness constraint errors if run multiple times
        last_release = db.query(models.Release).order_by(models.Release.id.desc()).first()
        global_version_counter = 1
        if last_release and last_release.version.startswith("v2026."):
            try:
                global_version_counter = int(last_release.version.split('.')[-1]) + 1
            except ValueError:
                pass
        
        total_seeded = 0
        
        # Generate releases
        for q_idx, (q_start, q_end) in enumerate(quarters, start=1):
            for pid in participant_ids:
                num_releases = random.randint(5, 50)
                for _ in range(num_releases):
                    # Random date within the quarter
                    delta = q_end - q_start
                    random_seconds = random.randint(0, int(delta.total_seconds()))
                    release_date = q_start + datetime.timedelta(seconds=random_seconds)
                    
                    version_str = f"v2026.{q_idx}.{global_version_counter}"
                    global_version_counter += 1
                    
                    # Double check uniqueness (just in case)
                    existing = db.query(models.Release).filter_by(version=version_str).first()
                    if not existing:
                        r = models.Release(version=version_str, date=release_date, participant_id=pid)
                        db.add(r)
                        total_seeded += 1
        
        db.commit()
        print(f"Seeded {total_seeded} random releases for 2026.")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
