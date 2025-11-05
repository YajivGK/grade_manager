from sqlalchemy import func, cast, Integer
from sqlalchemy.orm import Session
from models import Student, Attendance, Subject, EvaluationCriteria
from datetime import date

def calculate_attendance_percent(db: Session, student_id: int, subject_id: int) -> float:
    """Calculate attendance percentage for a student in a subject"""
    try:
        # Get total hours attended
        total_hours = db.query(func.sum(Attendance.hours)).filter(
            Attendance.student_id == student_id,
            Attendance.subject_id == subject_id
        ).scalar() or 0.0
        
        # Get total periods for the subject
        from models import AttendancePeriod
        total_periods = db.query(AttendancePeriod).filter(
            AttendancePeriod.subject_id == subject_id
        ).count()
        
        if total_periods == 0:
            # If no periods defined, check total attendance records
            total_records = db.query(func.count(Attendance.id)).filter(
                Attendance.student_id == student_id,
                Attendance.subject_id == subject_id
            ).scalar() or 0
            # If we have records but no periods, assume 100% if records exist
            return 100.0 if total_records > 0 else 0.0
        
        # Calculate percentage based on total hours vs expected hours
        # Assuming each period represents 1 hour of attendance opportunity
        # We can also count distinct dates and periods to get actual attendance opportunities
        # For simplicity, use hours attended vs total periods
        total_expected_hours = float(total_periods)  # Assuming 1 hour per period
        
        if total_expected_hours == 0:
            return 0.0
        
        attendance_percent = (float(total_hours) / total_expected_hours) * 100
        
        # Cap at 100%
        return min(attendance_percent, 100.0)
    except Exception as e:
        print(f"Error calculating attendance: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

def calculate_grade(combined_marks, attendance_percent):
    """
    Calculate grade based on combined marks and attendance
    Grade: O >90, A+ >80, A >70, B+ >60, B >50, U <50
    If attendance < 75%, grade = "SA"
    """
    if attendance_percent < 75.0:
        return "SA"
    
    if combined_marks > 90:
        return "O"
    elif combined_marks > 80:
        return "A+"
    elif combined_marks > 70:
        return "A"
    elif combined_marks > 60:
        return "B+"
    elif combined_marks > 50:
        return "B"
    else:
        return "U"

def calculate_combined_marks(internal_total, external_total, internal_weight):
    """
    Calculate combined marks based on internal and external weights
    internal_weight: 40 or 60
    external_weight: 60 or 40 (relative)
    """
    external_weight = 100 - internal_weight
    
    # Normalize to 100% scale
    combined = (internal_total * (internal_weight / 100.0)) + (external_total * (external_weight / 100.0))
    
    return round(combined, 2)

def get_student_batch(regno):
    """Determine batch from registration number (1=odd, 2=even)"""
    try:
        last_digit = int(str(regno)[-1])
        return 1 if last_digit % 2 == 1 else 2
    except:
        return 1  # Default to batch 1 if parsing fails

