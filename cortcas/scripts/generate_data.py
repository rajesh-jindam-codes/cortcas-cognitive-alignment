import asyncio
import uuid
import random
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from faker import Faker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal, engine
from app.models.db_models import Student, Session, BehavioralEvent, User
from app.auth.security import get_password_hash

fake = Faker()

# Configuration
NUM_STUDENTS = 300
DEPARTMENTS = ["Computer Science", "Data Science", "Mathematics", "Physics", "Chemistry", "Biology"]
GENDERS = ["Male", "Female", "Non-binary", "Prefer not to say"]
EVENT_TYPES = [
    "question_answered",
    "inactivity",
    "tab_switch",
    "revision",
    "hint_requested",
    "session_pause",
    "rapid_guessing",
    "early_exit"
]

def generate_student_profiles(num_students: int) -> List[Dict[str, Any]]:
    profiles = []
    # Distribution: 20% highly engaged, 50% average, 20% at risk, 7% irregular, 3% extreme outliers
    categories = ["highly_engaged", "average", "at_risk", "irregular", "outlier"]
    weights = [0.20, 0.50, 0.20, 0.07, 0.03]
    
    assigned_categories = np.random.choice(categories, size=num_students, p=weights)
    
    start_date = datetime.now() - timedelta(days=180)
    
    for i in range(num_students):
        student_id = uuid.uuid4()
        profile_cat = assigned_categories[i]
        
        name = fake.name()
        email = f"student_{i}_{student_id.hex[:6]}@cortcas.edu"
        age = random.randint(18, 25)
        gender = random.choice(GENDERS)
        dept = random.choice(DEPARTMENTS)
        year = random.randint(1, 4)
        enrollment_date = (start_date + timedelta(days=random.randint(0, 30))).date()
        
        profiles.append({
            "id": student_id,
            "name": name,
            "email": email,
            "age": age,
            "gender": gender,
            "department": dept,
            "year_of_study": year,
            "enrollment_date": enrollment_date,
            "category": profile_cat,
            "created_at": datetime.now() - timedelta(days=180)
        })
    return profiles

def generate_sessions_for_student(student: Dict[str, Any]) -> List[Dict[str, Any]]:
    category = student["category"]
    student_id = student["id"]
    enrollment_datetime = datetime.combine(student["enrollment_date"], datetime.min.time())
    
    # Decide session counts based on profile
    if category == "highly_engaged":
        num_sessions = random.randint(35, 50)
    elif category == "average":
        num_sessions = random.randint(20, 35)
    elif category == "at_risk":
        num_sessions = random.randint(10, 22)
    elif category == "irregular":
        num_sessions = random.randint(5, 15)
    else:  # outlier
        num_sessions = random.randint(3, 8)
        
    sessions = []
    current_time = enrollment_datetime + timedelta(days=1)
    end_bound = datetime.now()
    
    # Distribute sessions across the 6-month period
    total_days = (end_bound - current_time).days
    if total_days <= 0:
        total_days = 1
    
    session_intervals = sorted(random.sample(range(total_days), min(num_sessions, total_days)))
    
    for day_offset in session_intervals:
        session_id = uuid.uuid4()
        session_date = current_time + timedelta(days=day_offset)
        
        # Add a random hour
        session_start = session_date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59), second=0)
        
        # Profile specific distributions
        if category == "highly_engaged":
            duration_minutes = random.randint(20, 45)
            engagement_score = float(np.clip(np.random.normal(0.9, 0.05), 0.75, 1.0))
            focus_score = float(np.clip(np.random.normal(0.9, 0.05), 0.75, 1.0))
            inactivity_duration = random.randint(0, 120)  # seconds
            revision_count = random.randint(6, 15)
            wrong_answers = random.randint(0, 3)
            response_time = float(np.clip(np.random.normal(15.0, 3.0), 5.0, 30.0))
            
        elif category == "average":
            duration_minutes = random.randint(20, 60)
            engagement_score = float(np.clip(np.random.normal(0.65, 0.08), 0.45, 0.85))
            focus_score = float(np.clip(np.random.normal(0.68, 0.07), 0.45, 0.85))
            inactivity_duration = random.randint(120, 360)  # seconds
            revision_count = random.randint(2, 7)
            wrong_answers = random.randint(2, 7)
            response_time = float(np.clip(np.random.normal(30.0, 8.0), 10.0, 60.0))
            
        elif category == "at_risk":
            duration_minutes = random.randint(15, 75)
            engagement_score = float(np.clip(np.random.normal(0.3, 0.1), 0.05, 0.55))
            focus_score = float(np.clip(np.random.normal(0.28, 0.09), 0.05, 0.55))
            inactivity_duration = random.randint(480, 1800)  # seconds (8 to 30 mins)
            revision_count = random.randint(0, 2)
            wrong_answers = random.randint(6, 16)
            response_time = float(np.clip(np.random.normal(65.0, 20.0), 20.0, 180.0))
            
        elif category == "irregular":
            duration_minutes = random.randint(5, 90)
            engagement_score = float(np.clip(np.random.normal(0.5, 0.25), 0.05, 0.95))
            focus_score = float(np.clip(np.random.normal(0.52, 0.23), 0.05, 0.95))
            inactivity_duration = random.randint(30, 1200)  # seconds
            revision_count = random.randint(0, 12)
            wrong_answers = random.randint(0, 20)
            response_time = float(np.clip(np.random.normal(45.0, 35.0), 2.0, 240.0))
            
        else:  # outlier (abnormal patterns)
            # 50% chance of super short script session, 50% chance of idle session
            if random.choice([True, False]):
                # Script/bot behavior: extremely low response time, high wrong answers, very short duration
                duration_minutes = random.randint(1, 3)
                engagement_score = float(np.clip(np.random.normal(0.08, 0.04), 0.01, 0.2))
                focus_score = float(np.clip(np.random.normal(0.08, 0.04), 0.01, 0.2))
                inactivity_duration = 0
                revision_count = 0
                wrong_answers = random.randint(25, 60)
                response_time = float(np.clip(np.random.normal(0.6, 0.2), 0.1, 1.5))
            else:
                # Extreme idle behavior
                duration_minutes = random.randint(120, 240)
                engagement_score = float(np.clip(np.random.normal(0.05, 0.03), 0.01, 0.15))
                focus_score = float(np.clip(np.random.normal(0.05, 0.03), 0.01, 0.15))
                inactivity_duration = duration_minutes * 60 - random.randint(60, 300)  # almost entirely idle
                revision_count = random.randint(0, 1)
                wrong_answers = random.randint(0, 2)
                response_time = float(random.randint(300, 1200))
                
        session_end = session_start + timedelta(minutes=duration_minutes)
        
        sessions.append({
            "id": session_id,
            "student_id": student_id,
            "start_time": session_start,
            "end_time": session_end,
            "duration_minutes": duration_minutes,
            "engagement_score": engagement_score,
            "focus_score": focus_score,
            "inactivity_duration": inactivity_duration,
            "revision_count": revision_count,
            "wrong_answers": wrong_answers,
            "response_time": response_time,
            "created_at": session_start,
            "category": category  # keep for generating events
        })
    return sessions

def generate_events_for_session(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    session_id = session["id"]
    category = session["category"]
    start_time = session["start_time"]
    duration_min = session["duration_minutes"]
    
    events = []
    
    # Highly engaged students have more question_answered and revision events
    # At risk have inactivity and tab switches
    # Outliers have rapid guessing or deep inactivity
    
    num_events = 0
    if category == "highly_engaged":
        num_events = random.randint(15, 30)
    elif category == "average":
        num_events = random.randint(10, 20)
    elif category == "at_risk":
        num_events = random.randint(5, 12)
    elif category == "irregular":
        num_events = random.randint(3, 25)
    else:  # outlier
        num_events = random.randint(10, 65)  # e.g., rapid clicks
        
    for _ in range(num_events):
        event_time = start_time + timedelta(seconds=random.randint(0, duration_min * 60))
        
        # Decide event type based on profile
        if category == "highly_engaged":
            event_type = random.choice(["question_answered"] * 10 + ["revision"] * 5 + ["hint_requested"] * 2 + ["tab_switch"] * 1)
        elif category == "average":
            event_type = random.choice(["question_answered"] * 8 + ["tab_switch"] * 3 + ["inactivity"] * 2 + ["revision"] * 2 + ["hint_requested"] * 1)
        elif category == "at_risk":
            event_type = random.choice(["inactivity"] * 6 + ["tab_switch"] * 4 + ["session_pause"] * 2 + ["question_answered"] * 2)
        elif category == "irregular":
            event_type = random.choice(EVENT_TYPES)
        else: # outlier
            # script vs idle
            if session["duration_minutes"] < 5:
                event_type = random.choice(["rapid_guessing"] * 12 + ["question_answered"] * 5 + ["early_exit"] * 3)
            else:
                event_type = random.choice(["inactivity"] * 15 + ["session_pause"] * 3 + ["tab_switch"] * 2)
                
        # Generate some mock metadata
        meta = {}
        if event_type == "question_answered":
            meta = {
                "question_id": f"q_{random.randint(1, 100)}",
                "is_correct": random.choice([True, False]) if category != "highly_engaged" else random.choice([True] * 9 + [False]),
                "score_weight": round(random.uniform(1.0, 5.0), 1)
            }
        elif event_type == "inactivity":
            meta = {"idle_seconds": random.randint(30, 600) if category != "outlier" else random.randint(600, 7200)}
        elif event_type == "tab_switch":
            meta = {"target_url": random.choice(["youtube.com", "reddit.com", "discord.gg", "wikipedia.org", "google.com"])}
        elif event_type == "revision":
            meta = {"attempt_number": random.randint(2, 4), "previous_score": round(random.uniform(0, 0.8), 2)}
        elif event_type == "hint_requested":
            meta = {"hint_level": random.randint(1, 3), "time_spent_before_hint": random.randint(10, 120)}
        elif event_type == "rapid_guessing":
            meta = {"interval_ms": random.randint(200, 1500), "options_clicked": ["A", "B", "C"]}
        elif event_type == "early_exit":
            meta = {"percent_completed": round(random.uniform(0.05, 0.4), 2), "reason": "timeout"}
            
        events.append({
            "id": uuid.uuid4(),
            "session_id": session_id,
            "event_type": event_type,
            "timestamp": event_time,
            "metadata": meta
        })
        
    return events

async def main():
    print("Initializing Synthetic Data Generation...")
    
    # 1. Generate Platform Users (Admin & Viewers for Auth tests)
    users_data = [
        User(
            id=uuid.uuid4(),
            email="admin@cortcas.edu",
            # We'll use plain SHA256/bcrypt later. For now, a placeholder hash
            # that we'll match in the auth system.
            hashed_password=get_password_hash("admin123") if 'get_password_hash' in globals() else "$2b$12$EixZaYVK1fsAH1VMn.wK/.tF1Zty.4pM2fT9WbA2S9sQY8m9wS31m", # default bcrypt for "admin123"
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        User(
            id=uuid.uuid4(),
            email="viewer@cortcas.edu",
            hashed_password=get_password_hash("viewer123") if 'get_password_hash' in globals() else "$2b$12$EixZaYVK1fsAH1VMn.wK/.tF1Zty.4pM2fT9WbA2S9sQY8m9wS31m", # default bcrypt for "viewer123"
            role="viewer",
            is_active=True,
            created_at=datetime.utcnow()
        )
    ]

    print(f"Generating {NUM_STUDENTS} students...")
    student_profiles = generate_student_profiles(NUM_STUDENTS)
    
    db_students = []
    sessions_to_insert = []
    events_to_insert = []
    
    for p in student_profiles:
        student = Student(
            id=p["id"],
            email=p["email"],
            name=p["name"],
            age=p["age"],
            gender=p["gender"],
            department=p["department"],
            year_of_study=p["year_of_study"],
            enrollment_date=p["enrollment_date"],
            created_at=p["created_at"]
        )
        db_students.append(student)
        
        # Generate sessions
        student_sessions = generate_sessions_for_student(p)
        for s in student_sessions:
            sess = Session(
                id=s["id"],
                student_id=s["student_id"],
                start_time=s["start_time"],
                end_time=s["end_time"],
                duration_minutes=s["duration_minutes"],
                engagement_score=s["engagement_score"],
                focus_score=s["focus_score"],
                inactivity_duration=s["inactivity_duration"],
                revision_count=s["revision_count"],
                wrong_answers=s["wrong_answers"],
                response_time=s["response_time"],
                created_at=s["created_at"]
            )
            sessions_to_insert.append(sess)
            
            # Generate behavioral events
            session_events = generate_events_for_session(s)
            for e in session_events:
                evt = BehavioralEvent(
                    id=e["id"],
                    session_id=e["session_id"],
                    event_type=e["event_type"],
                    timestamp=e["timestamp"],
                    event_metadata=e["metadata"]
                )
                events_to_insert.append(evt)
                
    print(f"Generated:")
    print(f" - {len(db_students)} Student records")
    print(f" - {len(sessions_to_insert)} Session records")
    print(f" - {len(events_to_insert)} BehavioralEvent records")
    
    # Bulk insertion using AsyncSession
    async with AsyncSessionLocal() as session:
        # User inserts
        print("Inserting Users...")
        for u in users_data:
            session.add(u)
        await session.commit()
        
        # Student inserts
        print("Inserting Students in batch...")
        for i in range(0, len(db_students), 100):
            chunk = db_students[i:i+100]
            session.add_all(chunk)
            await session.commit()
            
        # Session inserts
        print("Inserting Sessions in batch...")
        for i in range(0, len(sessions_to_insert), 500):
            chunk = sessions_to_insert[i:i+500]
            session.add_all(chunk)
            await session.commit()
            
        # Event inserts (which can be quite large)
        print("Inserting Behavioral Events in batch...")
        for i in range(0, len(events_to_insert), 2000):
            chunk = events_to_insert[i:i+2000]
            session.add_all(chunk)
            await session.commit()
            
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
