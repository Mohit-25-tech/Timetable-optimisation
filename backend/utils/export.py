"""Export helpers for the optimized timetable."""
from __future__ import annotations
import csv
import io
from typing import List

from backend.models.schemas import GeneOut


def timetable_to_csv(rows: List[GeneOut]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Day", "Period", "Subject", "Faculty", "Batch", "Room"])
    for r in sorted(rows, key=lambda g: (g.day, g.period)):
        writer.writerow([r.day, r.period, r.subject_name, r.faculty_name, r.batch_name, r.room_number])
    return buf.getvalue()
