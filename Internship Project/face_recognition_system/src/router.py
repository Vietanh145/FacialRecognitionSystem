from fastapi import APIRouter, HTTPException, Request
from typing import List
from pydantic import BaseModel
from src.schemas.attendance import AttendanceCreate, AttendanceResponse
from src.database.models import Attendance
from src.database.database import get_db
from sqlalchemy.orm import Session
from src.services.face_recognition import FaceRecognitionService

router = APIRouter()
recognition_service = FaceRecognitionService()

class RecognizeRequest(BaseModel):
    name: str

@router.post("/checkin", response_model=AttendanceResponse)
def check_in(attendance: AttendanceCreate, db: Session = next(get_db())):
    db_attendance = Attendance(**attendance.dict())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@router.post("/checkout/{attendance_id}", response_model=AttendanceResponse)
def check_out(attendance_id: int, db: Session = next(get_db())):
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db_attendance.timeout = datetime.utcnow()
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@router.get("/attendance", response_model=List[AttendanceResponse])
def get_attendance_records(skip: int = 0, limit: int = 10, db: Session = next(get_db())):
    return db.query(Attendance).offset(skip).limit(limit).all()

@router.post("/recognize")
def recognize(request: RecognizeRequest):
    result = recognition_service.recognize_face(None)  # Thay None bằng ảnh nếu có
    return result