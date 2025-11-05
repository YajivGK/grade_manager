from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Subject
from schemas import SubjectResponse

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

@router.get("", response_model=list[SubjectResponse])
def get_subjects(db: Session = Depends(get_db)):
    """Get all subjects"""
    subjects = db.query(Subject).order_by(Subject.code).all()
    return [SubjectResponse(**s.to_dict()) for s in subjects]

