from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import EvaluationCriteria, Subject
from schemas import CriteriaCreate, CriteriaUpdate, CriteriaResponse

router = APIRouter(prefix="/api/criteria", tags=["criteria"])

@router.get("", response_model=list[CriteriaResponse])
def get_criteria(
    subject_id: int,
    db: Session = Depends(get_db)
):
    """Get all criteria for a subject"""
    criteria = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.subject_id == subject_id
    ).order_by(EvaluationCriteria.order_index).all()
    
    return [CriteriaResponse(**c.to_dict()) for c in criteria]

@router.post("", response_model=CriteriaResponse, status_code=201)
def create_criterion(
    criterion: CriteriaCreate,
    db: Session = Depends(get_db)
):
    """Create a new criterion"""
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == criterion.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Create criterion
    new_criterion = EvaluationCriteria(
        subject_id=criterion.subject_id,
        name=criterion.name,
        max_score=criterion.max_score,
        order_index=criterion.order_index,
        weight=criterion.weight
    )
    
    db.add(new_criterion)
    db.commit()
    db.refresh(new_criterion)
    
    return CriteriaResponse(**new_criterion.to_dict())

@router.put("/{criterion_id}", response_model=CriteriaResponse)
def update_criterion(
    criterion_id: int,
    criterion_update: CriteriaUpdate,
    db: Session = Depends(get_db)
):
    """Update a criterion"""
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criterion_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    
    # Update fields
    if criterion_update.name is not None:
        criterion.name = criterion_update.name
    if criterion_update.max_score is not None:
        criterion.max_score = criterion_update.max_score
    if criterion_update.order_index is not None:
        criterion.order_index = criterion_update.order_index
    if criterion_update.weight is not None:
        criterion.weight = criterion_update.weight
    
    db.commit()
    db.refresh(criterion)
    
    return CriteriaResponse(**criterion.to_dict())

@router.delete("/{criterion_id}", status_code=204)
def delete_criterion(
    criterion_id: int,
    db: Session = Depends(get_db)
):
    """Delete a criterion"""
    criterion = db.query(EvaluationCriteria).filter(
        EvaluationCriteria.id == criterion_id
    ).first()
    
    if not criterion:
        raise HTTPException(status_code=404, detail="Criterion not found")
    
    db.delete(criterion)
    db.commit()
    
    return None

