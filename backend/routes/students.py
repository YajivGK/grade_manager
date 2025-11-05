from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
from typing import Optional
from database import get_db
from models import Student, Class
from schemas import StudentResponse

router = APIRouter(prefix="/api/students", tags=["students"])

@router.get("", response_model=list[StudentResponse])
def get_students(
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    batch: Optional[int] = Query(None, description="Filter by batch (1=odd, 2=even)"),
    search: Optional[str] = Query(None, description="Search by name or regno"),
    db: Session = Depends(get_db)
):
    """Get students with optional filters"""
    query = db.query(Student)
    
    # Filter by class
    if class_id:
        query = query.filter(Student.class_id == class_id)
    
    # Filter by batch (batch 1 = odd regno, batch 2 = even regno)
    if batch == 1:
        query = query.filter(cast(func.right(Student.regno, 1), Integer) % 2 == 1)
    elif batch == 2:
        query = query.filter(cast(func.right(Student.regno, 1), Integer) % 2 == 0)
    
    # Search by name or regno
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Student.name.like(search_term)) | (Student.regno.like(search_term))
        )
    
    students = query.order_by(Student.regno).all()
    return [StudentResponse(**s.to_dict()) for s in students]

@router.get("/classes", response_model=list[dict])
def get_classes(db: Session = Depends(get_db)):
    """Get all classes"""
    classes = db.query(Class).order_by(Class.name).all()
    return [{"id": c.id, "name": c.name} for c in classes]

