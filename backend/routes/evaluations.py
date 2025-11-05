from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer
from typing import Optional
from datetime import date
from database import get_db
from models import StudentEvaluation, Student, Subject, EvaluationCriteria, InternalMarks
from schemas import EvaluateRequest, EvaluationResponse
from services.grade_calculator import (
    calculate_attendance_percent,
    calculate_grade,
    calculate_combined_marks,
    get_student_batch
)

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

@router.get("", response_model=list[EvaluationResponse])
def get_evaluations(
    subject_id: Optional[int] = Query(None),
    batch: Optional[int] = Query(None),
    evaluation_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get evaluations with optional filters"""
    query = db.query(StudentEvaluation)
    
    if subject_id:
        query = query.filter(StudentEvaluation.subject_id == subject_id)
    
    if batch:
        query = query.filter(StudentEvaluation.batch == batch)
    
    if evaluation_date:
        query = query.filter(StudentEvaluation.evaluation_date == evaluation_date)
    
    evaluations = query.order_by(StudentEvaluation.evaluation_date.desc()).all()
    return [EvaluationResponse(**e.to_dict()) for e in evaluations]

@router.post("/evaluate", response_model=list[EvaluationResponse], status_code=201)
def evaluate_students(
    request: EvaluateRequest,
    db: Session = Depends(get_db)
):
    """Evaluate students and calculate grades"""
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Get criteria for the subject
    criteria = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.subject_id == request.subject_id
    ).order_by(EvaluationCriteria.order_index).all()
    
    if not criteria:
        raise HTTPException(status_code=400, detail="No criteria defined for this subject")
    
    # Create a map of criterion_id to criterion for quick lookup
    criteria_map = {c.id: c for c in criteria}
    
    evaluations_created = []
    
    for eval_input in request.student_evaluations:
        # Verify student exists
        student = db.query(Student).filter(Student.id == eval_input.student_id).first()
        if not student:
            continue
        
        # Verify batch matches
        student_batch = get_student_batch(student.regno)
        if student_batch != request.batch:
            continue
        
        # Calculate attendance percentage (use provided value or calculate from records)
        if eval_input.attendance_percent is not None:
            attendance_percent = eval_input.attendance_percent
        else:
            attendance_percent = calculate_attendance_percent(
                db, eval_input.student_id, request.subject_id
            )
        
        # Calculate internal total (sum of all criteria marks)
        internal_total = 0.0
        internal_marks_data = []
        
        for internal_mark in eval_input.internal_marks:
            if internal_mark.criterion_id in criteria_map:
                criterion = criteria_map[internal_mark.criterion_id]
                # Validate marks don't exceed max_score
                marks = min(internal_mark.marks_obtained, float(criterion.max_score))
                internal_total += marks
                internal_marks_data.append({
                    'criterion_id': internal_mark.criterion_id,
                    'marks_obtained': marks
                })
        
        # Get external total
        external_total = eval_input.external_total
        
        # Calculate combined marks
        combined_marks = calculate_combined_marks(
            internal_total,
            external_total,
            request.internal_weight
        )
        
        # Calculate grade
        grade = calculate_grade(combined_marks, attendance_percent)
        
        # Check if evaluation already exists
        existing_eval = db.query(StudentEvaluation).filter(
            StudentEvaluation.student_id == eval_input.student_id,
            StudentEvaluation.subject_id == request.subject_id,
            StudentEvaluation.batch == request.batch,
            StudentEvaluation.evaluation_date == request.evaluation_date
        ).first()
        
        if existing_eval:
            # Update existing evaluation
            existing_eval.attendance_percent = attendance_percent
            existing_eval.internal_total = internal_total
            existing_eval.external_total = external_total
            existing_eval.combined_marks = combined_marks
            existing_eval.grade = grade
            existing_eval.internal_weight = request.internal_weight
            
            # Delete old internal marks
            db.query(InternalMarks).filter(
                InternalMarks.evaluation_id == existing_eval.id
            ).delete()
            
            # Create new internal marks
            for im_data in internal_marks_data:
                new_im = InternalMarks(
                    evaluation_id=existing_eval.id,
                    criterion_id=im_data['criterion_id'],
                    marks_obtained=im_data['marks_obtained']
                )
                db.add(new_im)
            
            db.commit()
            db.refresh(existing_eval)
            evaluations_created.append(existing_eval)
        else:
            # Create new evaluation
            new_evaluation = StudentEvaluation(
                student_id=eval_input.student_id,
                subject_id=request.subject_id,
                batch=request.batch,
                attendance_percent=attendance_percent,
                internal_total=internal_total,
                external_total=external_total,
                combined_marks=combined_marks,
                grade=grade,
                internal_weight=request.internal_weight,
                evaluation_date=request.evaluation_date
            )
            
            db.add(new_evaluation)
            db.flush()  # Get the ID
            
            # Create internal marks
            for im_data in internal_marks_data:
                new_im = InternalMarks(
                    evaluation_id=new_evaluation.id,
                    criterion_id=im_data['criterion_id'],
                    marks_obtained=im_data['marks_obtained']
                )
                db.add(new_im)
            
            db.commit()
            db.refresh(new_evaluation)
            evaluations_created.append(new_evaluation)
    
    return [EvaluationResponse(**e.to_dict()) for e in evaluations_created]

