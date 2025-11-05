from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
from database import get_db
from models import StudentEvaluation, Subject
from schemas import ReportGenerateRequest, ReportResponse
from services.report_generator import generate_evaluation_report_html
from aws_utils import upload_string_to_s3, get_presigned_url, list_files_in_s3

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.post("/generate")
def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate and upload HTML report to S3"""
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Check if evaluations exist
    evaluations = db.query(StudentEvaluation).filter(
        StudentEvaluation.subject_id == request.subject_id,
        StudentEvaluation.batch == request.batch,
        StudentEvaluation.evaluation_date == request.evaluation_date
    ).first()
    
    if not evaluations:
        raise HTTPException(status_code=404, detail="No evaluations found for the specified criteria")
    
    # Generate HTML report
    html_content = generate_evaluation_report_html(
        request.subject_id,
        request.batch,
        request.evaluation_date,
        db
    )
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_name = "odd" if request.batch == 1 else "even"
    filename = f"grade_report_{subject.code}_{batch_name}_{request.evaluation_date.strftime('%Y%m%d')}_{timestamp}.html"
    s3_key = f"reports/{filename}"
    
    # Upload to S3
    success, result = upload_string_to_s3(html_content, s3_key, 'text/html')
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Error uploading report to S3: {result}")
    
    # Generate presigned URL
    success_url, presigned_url = get_presigned_url(s3_key, expiration=3600)
    
    return {
        "success": True,
        "s3_key": s3_key,
        "filename": filename,
        "download_url": presigned_url if success_url else None,
        "message": f"Report generated and uploaded: {filename}"
    }

@router.get("", response_model=list[ReportResponse])
def list_reports(
    db: Session = Depends(get_db)
):
    """List all reports in S3"""
    prefix = 'reports/'
    success, files = list_files_in_s3(prefix)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {files}")
    
    # Filter only grade reports
    grade_reports = [f for f in files if f['key'].startswith('reports/grade_report_')]
    
    reports = []
    for file_info in grade_reports:
        key = file_info['key']
        filename = key.replace(prefix, '')
        
        # Generate presigned URL
        success_url, presigned_url = get_presigned_url(key, expiration=3600)
        
        reports.append({
            "key": key,
            "filename": filename,
            "size": file_info['size'],
            "size_mb": round(file_info['size'] / (1024 * 1024), 2),
            "last_modified": file_info['last_modified'],
            "download_url": presigned_url if success_url else None
        })
    
    return reports

@router.get("/download")
def get_report_download_url(
    s3_key: str = Query(..., description="S3 key of the report"),
    db: Session = Depends(get_db)
):
    """Get presigned URL for downloading a report"""
    # Validate key
    if not s3_key.startswith('reports/'):
        raise HTTPException(status_code=400, detail="Invalid report key")
    
    success, presigned_url = get_presigned_url(s3_key, expiration=3600)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Error generating download URL: {presigned_url}")
    
    return {"download_url": presigned_url}

