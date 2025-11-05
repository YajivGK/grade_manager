from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Numeric, Float, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

# Import existing models from cloud1 (reuse Student and Subject)
class Class(Base):
    """Class model"""
    __tablename__ = 'classes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    students = relationship('Student', backref='class_ref', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Class {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Student(Base):
    """Student model"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    regno = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    attendance_records = relationship('Attendance', backref='student_ref', lazy=True, cascade='all, delete-orphan')
    evaluations = relationship('StudentEvaluation', backref='student_ref', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.regno} - {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'regno': self.regno,
            'name': self.name,
            'class_id': self.class_id,
            'class_name': self.class_ref.name if self.class_ref else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Subject(Base):
    """Subject model"""
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    attendance_periods = relationship('AttendancePeriod', backref='subject_ref', lazy=True, cascade='all, delete-orphan')
    attendance_records = relationship('Attendance', backref='subject_ref', lazy=True, cascade='all, delete-orphan')
    criteria = relationship('EvaluationCriteria', backref='subject_ref', lazy=True, cascade='all, delete-orphan', order_by='EvaluationCriteria.order_index')
    evaluations = relationship('StudentEvaluation', backref='subject_ref', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Subject {self.code} - {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AttendancePeriod(Base):
    """Attendance Period model"""
    __tablename__ = 'attendance_periods'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    period_number = Column(Integer, nullable=False)
    name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('subject_id', 'period_number', name='unique_subject_period'),
        CheckConstraint('period_number >= 1 AND period_number <= 8', name='check_period_range')
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'period_number': self.period_number,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Attendance(Base):
    """Attendance record model"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    period_number = Column(Integer, nullable=False)
    hours = Column(Numeric(4, 2), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('period_number >= 1 AND period_number <= 8', name='check_attendance_period_range'),
    )

# New models for Grade Manager
class EvaluationCriteria(Base):
    """Evaluation Criteria model - stores internal criteria configuration per subject"""
    __tablename__ = 'evaluation_criteria'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    max_score = Column(Numeric(10, 2), nullable=False, default=100.0)
    order_index = Column(Integer, nullable=False, default=0)
    weight = Column(Numeric(5, 2), nullable=True)  # Optional weight for weighted calculation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    internal_marks = relationship('InternalMarks', backref='criterion_ref', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'name': self.name,
            'max_score': float(self.max_score) if self.max_score else 100.0,
            'order_index': self.order_index,
            'weight': float(self.weight) if self.weight else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StudentEvaluation(Base):
    """Student Evaluation model - stores evaluated grades per student/subject/batch"""
    __tablename__ = 'student_evaluations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    batch = Column(Integer, nullable=False)  # 1=odd, 2=even
    attendance_percent = Column(Numeric(5, 2), nullable=False)
    internal_total = Column(Numeric(10, 2), nullable=False)  # Sum of all criteria marks
    external_total = Column(Numeric(10, 2), nullable=False)
    combined_marks = Column(Numeric(10, 2), nullable=False)
    grade = Column(String(5), nullable=False)  # O, A+, A, B+, B, U, SA
    internal_weight = Column(Integer, nullable=False)  # 40 or 60
    evaluation_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'batch', 'evaluation_date', name='unique_student_evaluation'),
        CheckConstraint('batch IN (1, 2)', name='check_batch_value'),
        CheckConstraint('internal_weight IN (40, 60)', name='check_internal_weight')
    )
    
    internal_marks = relationship('InternalMarks', backref='evaluation_ref', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        # Build internal marks map for easy access
        internal_marks_map = {}
        if self.internal_marks:
            for im in self.internal_marks:
                internal_marks_map[im.criterion_id] = float(im.marks_obtained) if im.marks_obtained else 0.0
        
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_regno': self.student_ref.regno if self.student_ref else None,
            'student_name': self.student_ref.name if self.student_ref else None,
            'subject_id': self.subject_id,
            'subject_code': self.subject_ref.code if self.subject_ref else None,
            'subject_name': self.subject_ref.name if self.subject_ref else None,
            'batch': self.batch,
            'attendance_percent': float(self.attendance_percent) if self.attendance_percent else 0.0,
            'internal_total': float(self.internal_total) if self.internal_total else 0.0,
            'external_total': float(self.external_total) if self.external_total else 0.0,
            'combined_marks': float(self.combined_marks) if self.combined_marks else 0.0,
            'grade': self.grade,
            'internal_weight': self.internal_weight,
            'external_weight': 100 - self.internal_weight,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'internal_marks': internal_marks_map  # Include individual internal marks
        }

class InternalMarks(Base):
    """Internal Marks model - stores individual internal criterion scores"""
    __tablename__ = 'internal_marks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    evaluation_id = Column(Integer, ForeignKey('student_evaluations.id', ondelete='CASCADE'), nullable=False)
    criterion_id = Column(Integer, ForeignKey('evaluation_criteria.id', ondelete='CASCADE'), nullable=False)
    marks_obtained = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'criterion_id': self.criterion_id,
            'criterion_name': self.criterion_ref.name if self.criterion_ref else None,
            'marks_obtained': float(self.marks_obtained) if self.marks_obtained else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

def init_db():
    """Initialize database and create tables"""
    from config import engine
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
    except Exception as e:
        error_msg = str(e)
        if "Unknown database" in error_msg or "1049" in error_msg:
            print("❌ Database 'cloud1' does not exist. Please create it first.")
        elif "Can't connect" in error_msg or "Connection refused" in error_msg or "2003" in error_msg:
            print("❌ Cannot connect to MySQL server.")
            print("   Please check DB_HOST, DB_PORT in .env")
        else:
            print(f"❌ Database initialization error: {e}")
        raise

