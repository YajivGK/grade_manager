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

## License

MIT

