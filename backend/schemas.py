from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# Student schemas
class StudentBase(BaseModel):
    regno: str
    name: str
    class_id: int

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    class_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Subject schemas
class SubjectBase(BaseModel):
    code: str
    name: str

class SubjectCreate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: int
    
    class Config:
        from_attributes = True

# Criteria schemas
class CriteriaBase(BaseModel):
    subject_id: int
    name: str
    max_score: float = Field(default=100.0, ge=0)
    order_index: int = 0
    weight: Optional[float] = None

class CriteriaCreate(CriteriaBase):
    pass

class CriteriaUpdate(BaseModel):
    name: Optional[str] = None
    max_score: Optional[float] = None
    order_index: Optional[int] = None
    weight: Optional[float] = None

class CriteriaResponse(CriteriaBase):
    id: int
    
    class Config:
        from_attributes = True

# Evaluation schemas
class InternalMarkInput(BaseModel):
    criterion_id: int
    marks_obtained: float = Field(ge=0)

class EvaluationInput(BaseModel):
    student_id: int
    internal_marks: List[InternalMarkInput]
    external_total: float = Field(ge=0)
    attendance_percent: Optional[float] = Field(None, ge=0, le=100)

class EvaluateRequest(BaseModel):
    subject_id: int
    batch: int = Field(ge=1, le=2)
    internal_weight: int = Field(ge=40, le=60)
    evaluation_date: date
    student_evaluations: List[EvaluationInput]

class EvaluationResponse(BaseModel):
    id: int
    student_id: int
    student_regno: Optional[str] = None
    student_name: Optional[str] = None
    subject_id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    batch: int
    attendance_percent: float
    internal_total: float
    external_total: float
    combined_marks: float
    grade: str
    internal_weight: int
    external_weight: int
    evaluation_date: date
    
    class Config:
        from_attributes = True

# Report schemas
class ReportGenerateRequest(BaseModel):
    subject_id: int
    batch: int = Field(ge=1, le=2)
    evaluation_date: date

class ReportResponse(BaseModel):
    key: str
    filename: str
    size: int
    size_mb: float
    last_modified: str
    download_url: Optional[str] = None

