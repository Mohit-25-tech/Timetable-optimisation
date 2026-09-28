"""Generates a realistic sample university dataset so the app works out of the box."""
from __future__ import annotations
from backend.models.schemas import DatasetInput, Subject, Faculty, Room, Batch

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS_PER_DAY = 6

_FACULTY_NAMES = [
    "Dr. A. Sharma", "Dr. B. Mehta", "Dr. C. Rao", "Dr. D. Iyer", "Dr. E. Nair",
    "Dr. F. Kapoor", "Dr. G. Desai", "Dr. H. Verma", "Dr. I. Joshi", "Dr. J. Pillai",
    "Dr. K. Bose", "Dr. L. Chatterjee", "Dr. M. Reddy", "Dr. N. Gupta", "Dr. O. Singh",
    "Dr. P. Khan", "Dr. Q. Patil", "Dr. R. Shah", "Dr. S. Menon", "Dr. T. Dutta",
]

_DEPARTMENTS = ["CSE", "AI & ML", "Mathematics", "Electronics"]

_SUBJECT_NAMES = [
    "Artificial Intelligence", "Machine Learning", "Deep Learning",
    "Database Management Systems", "Operating Systems", "Computer Networks",
    "Data Structures", "Algorithms", "Big Data Systems", "Software Engineering",
    "Web Technologies", "Cloud Computing", "Computer Architecture", "Mathematics-III",
    "Statistics for AI", "Natural Language Processing", "Computer Vision",
    "Reinforcement Learning", "Distributed Systems", "Compiler Design",
    "Theory of Computation", "Human-Computer Interaction", "Information Security",
    "Data Visualization", "Optimization Techniques", "Robotics Fundamentals",
    "Mobile Application Development", "DevOps Practices", "Blockchain Basics",
    "Ethics in AI",
]

_BATCH_NAMES = ["AIML-A", "AIML-B", "CSE-A", "CSE-B", "CSE-C"]

_ROOM_TYPES = ["Lecture", "Lab", "Seminar"]


def build_sample_dataset() -> DatasetInput:
    faculty = [
        Faculty(faculty_id=f"F{idx+1:02d}", name=name, department=_DEPARTMENTS[idx % len(_DEPARTMENTS)])
        for idx, name in enumerate(_FACULTY_NAMES)
    ]

    batches = [
        Batch(batch_id=f"B{idx+1}", name=name, student_count=45 + (idx * 5) % 30)
        for idx, name in enumerate(_BATCH_NAMES)
    ]

    rooms = []
    for idx in range(10):
        room_type = _ROOM_TYPES[idx % len(_ROOM_TYPES)]
        capacity = 40 if room_type == "Lab" else (80 if room_type == "Lecture" else 60)
        rooms.append(Room(room_id=f"R{idx+1:02d}", room_number=f"{'LT' if room_type=='Lecture' else 'LB' if room_type=='Lab' else 'SR'}-{idx+1}", capacity=capacity, room_type=room_type))

    subjects = []
    for idx, name in enumerate(_SUBJECT_NAMES):
        faculty_id = faculty[idx % len(faculty)].faculty_id
        batch_id = batches[idx % len(batches)].batch_id
        sessions = 3 if idx % 3 == 0 else (2 if idx % 3 == 1 else 4)
        expected_students = next(b.student_count for b in batches if b.batch_id == batch_id)
        preferred = "Lab" if "Programming" in name or name in ("Machine Learning", "Deep Learning", "Computer Vision") else None
        subjects.append(Subject(
            subject_id=f"S{idx+1:02d}",
            name=name,
            faculty_id=faculty_id,
            batch_id=batch_id,
            sessions_per_week=sessions,
            expected_students=expected_students,
            preferred_room_type=preferred,
        ))

    return DatasetInput(
        subjects=subjects,
        faculty=faculty,
        rooms=rooms,
        batches=batches,
        days=DAYS,
        periods_per_day=PERIODS_PER_DAY,
    )
