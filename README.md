# Grade Manager System (Cloud2)

A modern Grade Manager system built with FastAPI backend and React frontend for evaluating student grades based on attendance, internal assessments, and external assessments.

## Features

- **Student Evaluation**: Calculate grades based on attendance percentage, internal marks (multiple criteria), and external marks
- **Flexible Weightage**: Toggle between 40/60 or 60/40 internal/external weight distribution
- **Criteria Management**: Add/delete internal assessment criteria with customizable max scores
- **Batch Filtering**: Filter students by odd/even registration numbers
- **Grade Calculation**: Automatic grade assignment (O, A+, A, B+, B, U, SA)
- **Attendance Check**: Students with <75% attendance receive "SA" grade
- **Report Generation**: Generate HTML reports and upload to S3
- **Modern UI**: Responsive, interactive React frontend

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React
- **Database**: MySQL (shared with cloud1)
- **Storage**: AWS S3 for reports
- **Deployment**: Dockerized for ECR

## Prerequisites

- Python 3.11+
- Node.js 16+
- MySQL database (same as cloud1)
- AWS credentials configured
- Docker (for containerization)

## Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your database and AWS credentials.

### 4. Database

The system uses the same database as cloud1. Make sure:
- Database `cloud1` exists
- Tables from cloud1 are present (students, subjects, classes, attendance)
- New tables will be created automatically (evaluation_criteria, student_evaluations, internal_marks)

## Running the Application

### Development

**Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm start
```

The frontend will run on `http://localhost:3000` and connect to the backend at `http://localhost:8000`.

### Production with Docker

**Build:**
```bash
docker build -t grade-manager .
```

**Run:**
```bash
docker run -d -p 8000:8000 \
  -e DB_HOST=your-rds-endpoint \
  -e DB_PORT=3306 \
  -e DB_USER=admin \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=cloud1 \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  grade-manager
```

## Deploy to ECR

```bash
chmod +x deploy-to-ecr.sh
./deploy-to-ecr.sh
```

## API Endpoints

- `GET /api/students` - List students (with filters)
- `GET /api/subjects` - List subjects
- `GET /api/criteria?subject_id=X` - Get criteria for subject
- `POST /api/criteria` - Create criterion
- `DELETE /api/criteria/{id}` - Delete criterion
- `POST /api/evaluations/evaluate` - Evaluate students
- `GET /api/evaluations` - Get evaluations
- `POST /api/reports/generate` - Generate report
- `GET /api/reports` - List reports

## Grade Calculation

- **Attendance %**: Calculated from attendance records
- **Internal Total**: Sum of all criteria marks
- **External Total**: Single value input
- **Combined Marks**: (Internal × Internal Weight) + (External × External Weight)
- **Grade**: 
  - O: >90
  - A+: >80
  - A: >70
  - B+: >60
  - B: >50
  - U: <50
  - SA: Attendance < 75%

## Project Structure

```
cloud2/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── config.py
│   ├── schemas.py
│   ├── database.py
│   ├── aws_utils.py
│   ├── routes/
│   │   ├── students.py
│   │   ├── subjects.py
│   │   ├── criteria.py
│   │   ├── evaluations.py
│   │   └── reports.py
│   └── services/
│       ├── grade_calculator.py
│       └── report_generator.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── services/
│   │   └── styles/
│   └── public/
├── Dockerfile
├── docker-entrypoint.py
├── deploy-to-ecr.sh
└── .env
```

## Environment Variables

Create a `.env` at repo root or provide these as container envs:

```env
# MySQL (RDS) connectivity
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your-strong-password
DB_NAME=cloud1

# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-s3-bucket
```

## AWS Deployment Guide

This project uses four AWS services: EC2, RDS, S3, and ECR.

## 1) Amazon RDS (MySQL)

- Create an RDS MySQL instance (db.t3.micro or larger).
- Note endpoint, port, master username, and password.
- Security group: allow inbound MySQL (3306) from your EC2 security group.
- Populate required schema (shared with cloud1). New tables are auto-managed by app models/migrations if present.

## 2) Amazon S3

- Create a bucket, e.g., `grade-manager-reports-<env>`.
- Keep private by default; app uses presigned URLs for access.

### Minimum IAM policy for reports (attach to the app role/user)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-s3-bucket",
        "arn:aws:s3:::your-s3-bucket/*"
      ]
    }
  ]
}
```

## 3) Amazon ECR

- Create an ECR repo: `grade-manager`.
- Build and push image:

```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin <acct>.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t grade-manager:latest .
docker tag grade-manager:latest <acct>.dkr.ecr.$AWS_REGION.amazonaws.com/grade-manager:latest
docker push <acct>.dkr.ecr.$AWS_REGION.amazonaws.com/grade-manager:latest
```

## 4) Amazon EC2

- Launch Amazon Linux 2 (or Ubuntu) instance.
- Security group: allow 22 (SSH), 8000 (API) from trusted sources.
- Install Docker and start it:

```bash
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -aG docker ec2-user # re-login
```

- Pull and run the container:

```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin <acct>.dkr.ecr.$AWS_REGION.amazonaws.com

docker pull <acct>.dkr.ecr.$AWS_REGION.amazonaws.com/grade-manager:latest

# Option A: pass env inline
docker run -d --name grade-manager -p 8000:8000 \
  -e DB_HOST=your-rds-endpoint.rds.amazonaws.com \
  -e DB_PORT=3306 \
  -e DB_USER=admin \
  -e DB_PASSWORD=your-strong-password \
  -e DB_NAME=cloud1 \
  -e AWS_ACCESS_KEY_ID=AKIA... \
  -e AWS_SECRET_ACCESS_KEY=... \
  -e AWS_REGION=ap-south-1 \
  -e S3_BUCKET_NAME=your-s3-bucket \
  <acct>.dkr.ecr.$AWS_REGION.amazonaws.com/grade-manager:latest

# Option B: use an env file (recommended)
cat > .env <<'EOF'
DB_HOST=...
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=...
DB_NAME=cloud1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
S3_BUCKET_NAME=...
EOF
docker run -d --name grade-manager -p 8000:8000 --env-file .env \
  <acct>.dkr.ecr.$AWS_REGION.amazonaws.com/grade-manager:latest
```

### Optional: systemd service

Create `/etc/systemd/system/grade-manager.service` to auto-start on reboot.

# Deployment Runbook (Summary)

1. Create RDS (MySQL) and S3 bucket.
2. Build, tag, and push Docker image to ECR.
3. Launch EC2 and install Docker.
4. Pull image from ECR and run container with RDS/S3 env vars.
5. Verify health at `http://<EC2_PUBLIC_IP>:8000/docs`.

# Troubleshooting

- DB connection timeout: verify RDS SG allows inbound 3306 from EC2 SG; check `DB_HOST`, port, and credentials.
- S3 upload fails: verify IAM policy and `S3_BUCKET_NAME` region match.
- ECR auth fails: ensure `aws ecr get-login-password` uses correct region and account.
- API not reachable: open SG inbound 8000 or place behind ALB and update security groups accordingly.

## License

MIT
