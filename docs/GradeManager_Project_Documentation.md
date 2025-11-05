# Grade Manager – Cloud Computing Mini Project

Front Page (fill and print on a separate cover sheet)
- Name: __________________________
- Register Number: __________________________
- Department: __________________________
- Year / Semester: __________________________
- Batch: __________________________
- Subject Name: __________________________
- Subject Code: __________________________
- Date of Submission: __________________________

Note on formatting when exporting to Word
- Font: Times New Roman
- Size: 12 (titles 14)
- Line spacing: 1.5
- Black and white, neatly stapled printouts

---

## Title
Grade Manager – Batch-wise Evaluation, Grading, and Reporting System on AWS

## Abstract
- Aim: Build a grade management system to calculate attendance percentage, compute combined internal/external marks, assign grades, and generate printable reports.
- Technology used: React frontend, Python backend with SQLAlchemy ORM, MySQL database, HTML/CSS for report layout.
- Tools used: AWS EC2, RDS (MySQL), S3, ECR; Docker; GitHub; python-docx (for .docx), SQLAlchemy.
- Outcome: End-to-end evaluation pipeline with UI, API, grade logic, and downloadable reports; deployable on AWS with containerization.

## Introduction
- Tools overview: 
  - React for UI, Axios-based API client.
  - Python web service (FastAPI/Flask style) with SQLAlchemy for DB access.
  - MySQL for persistent storage.
  - AWS services for deployment: EC2 (compute), RDS (managed MySQL), S3 (object storage), ECR (container registry).
- Objective: Provide a configurable, reliable, and repeatable grade evaluation workflow with batch-wise execution and reporting.
- Scope: Subject & student management, criteria configuration, evaluation execution, HTML report generation, and AWS-based deployment.

## Project Workflow and Main Logic
1) Data flow
- Load subjects, criteria, and batch selection in the UI.
- Fetch students and existing evaluations; compute or fetch results for the selected date.

2) Attendance percentage
- From `backend/services/grade_calculator.py`:
```python
attendance_percent = (float(total_hours) / total_expected_hours) * 100
attendance_percent = min(attendance_percent, 100.0)
```

3) Combined marks and grade rules
- From `backend/services/grade_calculator.py`:
```python
def calculate_combined_marks(internal_total, external_total, internal_weight):
    external_weight = 100 - internal_weight
    return round(
        (internal_total * (internal_weight / 100.0)) +
        (external_total * (external_weight / 100.0)), 2)

def calculate_grade(combined_marks, attendance_percent):
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
```

4) Report generation
- From `backend/services/report_generator.py`: build styled HTML table including reg. no, name, attendance %, internal/external totals, combined marks, and grade with color coding.

## Implementation
### Backend
- Config: `backend/config.py` sets SQLAlchemy engine and `SessionLocal` to connect to MySQL (RDS) using env vars: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
- Services: 
  - `grade_calculator.py` for attendance %, combined marks, and grade mapping.
  - `report_generator.py` for printable HTML report per subject and batch.
- Routes: `backend/routes/` provide endpoints for criteria, evaluations, students, subjects, reports.

### Frontend
- Key components: 
  - `GradeEvaluationTable.jsx`: orchestrates subject/batch selection, criteria, evaluation trigger, and listing.
  - `CriteriaManager.jsx`: configure internal components.
  - `EvaluateButton.jsx`: triggers evaluation.
  - `ReportsList.jsx`: lists and opens generated reports.
- API: `frontend/src/services/api.js` for backend calls.

### Representative UI Flow
- Select subject and batch → configure internal weight → Run evaluation → View results → Open report.

## Screenshots (placeholders with figure numbers)
- Figure 1: Frontend home (App)
- Figure 2: Grade Evaluation Table populated for a subject
- Figure 3: Criteria Manager configuration
- Figure 4: Evaluate button action and status
- Figure 5: Reports list
- Figure 6: Sample HTML report preview

Place screenshots in `docs/screenshots/` and embed when exporting to Word.

## Deployment on AWS (EC2 + RDS + S3 + ECR)
### Prerequisites
- AWS account, IAM user with ECR/EC2/RDS/S3 permissions
- Docker, Git, AWS CLI configured (`aws configure`)

### 1) Amazon RDS (MySQL)
- Create RDS MySQL instance (e.g., db.t3.micro) in your VPC, set public/private access per design.
- Security group: allow inbound from EC2 security group on port 3306.
- Record endpoint, username, and password.
- Initialize schema/tables using your ORM migrations or SQL scripts (models not shown here).
- App environment variables:
```
DB_HOST=<rds-endpoint>
DB_PORT=3306
DB_USER=<username>
DB_PASSWORD=<password>
DB_NAME=cloud1
```

### 2) Amazon ECR (Container Registry)
- Create a private repository (e.g., `grade-manager`).
- Build and push image:
```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
REPO=<acct>.dkr.ecr.<region>.amazonaws.com/grade-manager
docker build -t grade-manager .
docker tag grade-manager:latest $REPO:latest
docker push $REPO:latest
```

### 3) Amazon EC2 (Compute)
- Launch EC2 (e.g., Amazon Linux 2023) with security group allowing HTTP/HTTPS (80/443) and app port if needed, and SSH (22) from your IP.
- Install Docker, pull and run container:
```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable --now docker
aws ecr get-login-password --region <region> | sudo docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
sudo docker pull $REPO:latest
# Provide env vars mapping to RDS and any S3/AWS keys
sudo docker run -d --name grade-manager -p 80:8080 \
  -e DB_HOST=$DB_HOST -e DB_PORT=3306 -e DB_USER=$DB_USER -e DB_PASSWORD=$DB_PASSWORD -e DB_NAME=cloud1 \
  -e AWS_REGION=ap-south-1 -e S3_BUCKET_NAME=crestora-uploads \
  $REPO:latest
```
- Optionally put Nginx in front for TLS or use ALB.

### 4) Amazon S3 (Object Storage)
- Create bucket (e.g., `grade-manager-uploads-<acct>`). Keep private by default; enable bucket policy/role if needed.
- Set env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME`.
- Use `backend/aws_utils.py` (if applicable) to upload or serve static artifacts like reports.

### Environment Variable Summary
```
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME
```

### CI/CD (Optional)
- Use GitHub Actions to build and push to ECR on every main branch push, then SSH or SSM into EC2 to pull latest image and restart container.

## Operations and Maintenance
- Logs: Tail container logs via `docker logs -f grade-manager` or ship to CloudWatch.
- Database: Snapshots via RDS automated backups.
- Scaling: Increase EC2 instance type or use ECS/EKS with Auto Scaling.
- Security: Limit security group ingress; rotate DB credentials; use IAM roles for EC2 to access S3/ECR without static keys.

## Tools / Experiments (AWS)

### 1) AWS EC2
- Introduction: Elastic compute service for running application containers/VMs.
- Purpose: Host the Grade Manager container, expose HTTP endpoint.
- Deployment (single feature): Run Dockerized backend+frontend on port 80.
- Screenshot: Figure 7 – EC2 instance running (console view).
- Conclusion: Provides flexible compute with control over networking and security.

### 2) AWS RDS (MySQL)
- Introduction: Managed relational database service.
- Purpose: Persist students, subjects, attendance, and evaluation results.
- Deployment (single feature): Create DB instance and connect using `backend/config.py` env vars.
- Screenshot: Figure 8 – RDS instance details and connectivity test.
- Conclusion: Offloads database management and backups.

### 3) AWS S3
- Introduction: Highly durable object storage.
- Purpose: Store uploaded artifacts (e.g., reports/exports) if enabled.
- Deployment (single feature): Create bucket and upload a sample export.
- Screenshot: Figure 9 – Bucket objects list with a report file.
- Conclusion: Simple, scalable storage for artifacts.

### 4) AWS ECR
- Introduction: Private container registry for Docker images.
- Purpose: Store and version backend container images.
- Deployment (single feature): Build, tag, and push image commands shown above.
- Screenshot: Figure 10 – ECR repository with latest image tag.
- Conclusion: Integrates with AWS auth and CI/CD flows.

## Results
- Provide screenshots (Figures 1–6) demonstrating evaluation, grade assignment, and generated report, plus AWS screenshots (Figures 7–10).
- Report should list student-wise attendance %, internal/external totals, combined marks, and grades.

## Conclusion
- The system streamlines evaluation workflows with data-driven criteria, consistent grade mapping, and printable reports. AWS services (EC2, RDS, S3, ECR) provide a robust deployment baseline.

## References
- React: https://react.dev
- SQLAlchemy: https://docs.sqlalchemy.org
- FastAPI: https://fastapi.tiangolo.com / Flask: https://flask.palletsprojects.com
- python-docx: https://python-docx.readthedocs.io
- MySQL: https://dev.mysql.com/doc/
- AWS EC2: https://docs.aws.amazon.com/ec2/
- AWS RDS: https://docs.aws.amazon.com/rds/
- AWS S3: https://docs.aws.amazon.com/s3/
- AWS ECR: https://docs.aws.amazon.com/ecr/
