# Grade Manager System – Cloud Computing Mini Project

## Front Matter

- Name: ________________________________
- Register Number: _____________________
- Year / Semester: _____________________
- Department: __________________________
- Batch: _______________________________
- Subject Name: ________________________
- Subject Code: ________________________
- Date of Submission: __________________

Note on printing: Use Times New Roman, 12pt font, 1.5 line spacing. Titles in 14pt. Print in black and white. Add figure numbers as provided in captions.

---

## Title

A Cloud-Native Grade Manager on AWS (EC2, RDS, S3, ECR) using FastAPI and React

## Abstract

- Aim: Build a cloud-native web application to evaluate and manage student grades using attendance, internal assessments, and external marks with configurable weightage, and to generate shareable reports.
- Technology: FastAPI (Python), React, MySQL, Docker, AWS (EC2, RDS, S3, ECR).
- Tools Used: AWS EC2 for compute, AWS RDS for managed MySQL, AWS S3 for report storage and distribution, AWS ECR for container image registry.
- Outcome: A deployable system that calculates grades, persists evaluations, generates HTML reports uploaded to S3, and can be deployed to EC2 using images stored in ECR with RDS as the database backend.

---

## Introduction

- Objective: Design and implement a scalable grade management system with modular services for calculation and reporting, expose REST APIs, and deliver a user-friendly frontend.
- Scope: Student data listing and filtering, criteria management, evaluation (with configurable internal/external weights), grade computation, report generation and S3 upload, and production deployment on AWS.
- Tools Overview:
  - AWS EC2: Runs the backend container image, exposes API to the Internet/VPC.
  - AWS RDS (MySQL): Manages persistent relational data used by both cloud1 and this project (cloud2).
  - AWS S3: Stores generated HTML reports and enables presigned access.
  - AWS ECR: Hosts Docker images for deployment to EC2.

---

## System Architecture Overview

- Backend: FastAPI with SQLAlchemy services.
- Frontend: React SPA.
- Database: MySQL (RDS). Shared schema with cloud1; adds tables: `evaluation_criteria`, `student_evaluations`, `internal_marks`.
- Storage: AWS S3 for report artifacts.
- Deployment: Docker image pushed to ECR; pulled and run on EC2; backend configured with RDS endpoint and AWS credentials.

[Figure 1: High-level Architecture – React (client) -> FastAPI (EC2) -> RDS (MySQL); Reports -> S3]

![Figure 1: Architecture](./screenshots/fig-01-architecture.png)

---

## Project Workflow, Main Functions, and Logic

- Criteria Management API (`backend/routes/criteria.py`)
  - Get, create, update, delete criteria per subject.
  - Ensures subject existence and validates updates.

- Evaluation API (`backend/routes/evaluations.py`)
  - Accepts batch, subject, internal weight, evaluation date, and per-student internal marks, external total, and optional attendance percent.
  - Derives student batch from registration number, validates criteria, caps marks, computes combined marks and grade, upserts evaluations, and records internal marks breakdown.

- Grade Calculation Service (`backend/services/grade_calculator.py`)
  - `calculate_attendance_percent(db, student_id, subject_id)` computes attendance percentage from attendance records and periods.
  - `calculate_combined_marks(internal_total, external_total, internal_weight)` computes weighted sum.
  - `calculate_grade(combined_marks, attendance_percent)` assigns grade with SA if attendance < 75%.

- Report Generation Service (`backend/services/report_generator.py`)
  - `generate_evaluation_report_html(subject_id, batch, evaluation_date, db)` renders a styled HTML table of evaluated students, color-codes grades.

- S3 Utility (`backend/aws_utils.py`)
  - `upload_string_to_s3(content, s3_key, content_type)` uploads generated reports.
  - `get_presigned_url(s3_key)` shares download links.

- Frontend UI (`frontend/src/components/GradeEvaluationTable.jsx`, `CriteriaManager.jsx`)
  - Subject selection, criteria CRUD, marks entry, attendance input, batch selection, weight toggle, evaluation trigger, and grade display.

### Pseudocode Snippets (Grounded in Project)

1) Criteria creation (from `criteria.py`):

```pseudo
function create_criterion(criterion):
  subject = db.query(Subject).where(Subject.id == criterion.subject_id).first()
  if not subject: raise 404

  new_criterion = EvaluationCriteria(
    subject_id=criterion.subject_id,
    name=criterion.name,
    max_score=criterion.max_score,
    order_index=criterion.order_index,
    weight=criterion.weight
  )
  db.add(new_criterion); db.commit(); db.refresh(new_criterion)
  return new_criterion.to_dict()
```

2) Evaluate students (from `evaluations.py`):

```pseudo
function evaluate_students(request):
  subject = db.Subject.get(request.subject_id) or raise 404
  criteria = db.Criteria.where(subject_id == request.subject_id).order_by(order_index)
  if criteria.empty: raise 400

  criteria_map = { c.id: c for c in criteria }
  results = []

  for eval_input in request.student_evaluations:
    student = db.Student.get(eval_input.student_id)
    if not student: continue

    if get_student_batch(student.regno) != request.batch: continue

    attendance = eval_input.attendance_percent ?? calculate_attendance_percent(db, eval_input.student_id, request.subject_id)

    internal_total = 0
    internal_marks_data = []
    for im in eval_input.internal_marks:
      if im.criterion_id in criteria_map:
        allowed = min(im.marks_obtained, criteria_map[im.criterion_id].max_score)
        internal_total += allowed
        internal_marks_data.push({criterion_id: im.criterion_id, marks_obtained: allowed})

    external_total = eval_input.external_total
    combined = calculate_combined_marks(internal_total, external_total, request.internal_weight)
    grade = calculate_grade(combined, attendance)

    existing = db.StudentEvaluation.findUnique(student_id, subject_id, batch, evaluation_date)
    if existing:
      update existing with new totals and grade
      delete old InternalMarks where evaluation_id == existing.id
      create InternalMarks for internal_marks_data
      commit; refresh; results.push(existing)
    else:
      new_eval = StudentEvaluation(...)
      db.add(new_eval); db.flush()
      create InternalMarks for internal_marks_data with evaluation_id = new_eval.id
      commit; refresh; results.push(new_eval)

  return results.map(EvaluationResponse)
```

3) Grade calculation rules (from `grade_calculator.py`):

```pseudo
function calculate_grade(combined, attendance):
  if attendance < 75: return "SA"
  if combined > 90: return "O"
  else if combined > 80: return "A+"
  else if combined > 70: return "A"
  else if combined > 60: return "B+"
  else if combined > 50: return "B"
  else: return "U"
```

4) Report rendering (from `report_generator.py`):

```pseudo
function generate_evaluation_report_html(subject_id, batch, eval_date, db):
  subject = db.Subject.get(subject_id) or return "<h1>Subject not found</h1>"
  evaluations = db.StudentEvaluation.join(Student)
                  .where(subject_id, batch, evaluation_date)
                  .order_by(Student.regno)

  if evaluations.empty: return "<h1>No evaluations found</h1>"

  html_rows = []
  for e in evaluations:
    color = grade_color_map[e.grade]
    html_rows.append(tr(td(e.regno), td(e.name), td(e.attendance%), td(e.internal), td(e.external), td(e.combined), td(e.grade, color)))

  return wrap_html_with_styles(table(thead, tbody(html_rows)))
```

---

## Implementation (Code and Screenshots)

- Backend Startup (example): `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Frontend Startup: `npm start` (serves on localhost:3000)

Screenshots (add actual images before printing):

- [Figure 2: Landing UI – Subject/Batch/Weight Controls](./screenshots/fig-02-ui-controls.png)
- [Figure 3: Criteria Manager – Add/Delete Criteria](./screenshots/fig-03-criteria-manager.png)
- [Figure 4: Evaluation Table – Marks Entry](./screenshots/fig-04-evaluation-table.png)
- [Figure 5: Grades After Evaluation](./screenshots/fig-05-grades.png)
- [Figure 6: S3 Report Object](./screenshots/fig-06-s3-report.png)
- [Figure 7: EC2 Docker Container Running](./screenshots/fig-07-ec2-docker.png)
- [Figure 8: RDS Connectivity Test](./screenshots/fig-08-rds-connectivity.png)

Code references are available in the repository under `backend/` and `frontend/`.

---

## Results

- Successful grade computations for selected batch and subject.
- Reports generated as styled HTML and uploaded to S3.
- Evaluations persisted in RDS with internal marks breakdown.
- Frontend displays computed grades with color coding.

Screenshots:

- [Figure 9: Evaluation API Response](./screenshots/fig-09-api-response.png)
- [Figure 10: Report HTML Preview](./screenshots/fig-10-report-preview.png)

---

## Conclusion

The Grade Manager demonstrates cloud-native design: compute on EC2, persistent storage on RDS, artifact storage on S3, and container distribution via ECR. The system is modular, configurable (internal weight), and production-ready with Docker. Future work can include authentication, role-based access, CI/CD, and automated report scheduling.

---

## References

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- React: https://react.dev/
- AWS EC2: https://docs.aws.amazon.com/ec2/
- AWS RDS: https://docs.aws.amazon.com/rds/
- AWS S3: https://docs.aws.amazon.com/s3/
- AWS ECR: https://docs.aws.amazon.com/ecr/
- Docker: https://docs.docker.com/

---

# Tools/Experiments

## 1) AWS EC2

- Title: Deploy FastAPI Container on EC2
- Introduction: EC2 provides virtual servers to run containerized workloads.
- Purpose/Features: Host backend API, attach security groups, enable public/private networking.
- Deployment of a single feature (Hello API):
  1. Create EC2 (Amazon Linux 2), open ports 22, 8000.
  2. Install Docker: `sudo yum install docker -y && sudo service docker start`.
  3. Login to ECR, pull image: `docker pull <account>.dkr.ecr.<region>.amazonaws.com/grade-manager:latest`.
  4. Run: `docker run -d -p 8000:8000 --env-file .env <image>`.

  ![Figure 11: EC2 Instance Console](./screenshots/fig-11-ec2-console.png)

- Conclusion: EC2 reliably hosts the API in a scalable manner.

## 2) AWS RDS (MySQL)

- Title: Managed MySQL for Application Data
- Introduction: RDS provides managed relational databases.
- Purpose/Features: Automated backups, scaling, parameter groups, secure connectivity.
- Deployment of a single feature (Create DB and connect):
  1. Create RDS MySQL instance, note endpoint, port, user, password.
  2. Set env variables `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
  3. Start backend pointing to RDS; verify `engine` connectivity.

  ![Figure 12: RDS Instance Details](./screenshots/fig-12-rds-instance.png)

- Conclusion: RDS offloads database ops and ensures reliability.

## 3) AWS S3

- Title: Report Storage and Distribution
- Introduction: S3 stores objects at scale with high durability.
- Purpose/Features: Upload HTML reports, list objects, generate presigned URLs.
- Deployment of a single feature (Upload report):
  1. Use `upload_string_to_s3(content, key, 'text/html')`.
  2. Verify in S3 console bucket `S3_BUCKET_NAME`.
  3. Generate presigned URL for download.

  ![Figure 13: S3 Bucket Objects](./screenshots/fig-13-s3-bucket.png)

- Conclusion: S3 simplifies report distribution and archival.

## 4) AWS ECR

- Title: Private Docker Registry for Images
- Introduction: ECR stores and manages container images.
- Purpose/Features: Integrated with IAM, lifecycle policies, easy EC2 pulls.
- Deployment of a single feature (Build and push):
  1. `docker build -t grade-manager:latest .`
  2. Tag for ECR: `docker tag grade-manager:latest <acct>.dkr.ecr.<region>.amazonaws.com/grade-manager:latest`
  3. Login and push: `aws ecr get-login-password | docker login ... && docker push <ecr-uri>`

  ![Figure 14: ECR Repository View](./screenshots/fig-14-ecr-repo.png)

- Conclusion: ECR provides a secure, managed registry for deployment pipelines.

---

Printing and Formatting Notes:

- Use Times New Roman, 12pt, 1.5 spacing for body; 14pt for titles when converting to DOCX/PDF for submission.
- Keep figure numbering consistent with captions above.
- Staple neatly in black and white.
