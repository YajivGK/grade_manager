from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from database import get_db
from models import init_db
import os
import traceback

# Initialize FastAPI app
app = FastAPI(
    title="Grade Manager API",
    description="API for Grade Management System",
    version="1.0.0"
)

# Configure CORS - MUST be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8088", "http://localhost:3000", "http://localhost:5173","http://13.233.80.196:8088"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Middleware to ensure CORS headers on all responses
class CORSResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Ensure CORS headers are present
        origin = request.headers.get("origin")
        if origin in ["http://localhost:8088", "http://localhost:3000", "http://localhost:5173"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(CORSResponseMiddleware)

# CORS headers for all responses
def add_cors_headers(headers: dict) -> dict:
    """Add CORS headers to response"""
    headers["Access-Control-Allow-Origin"] = "http://localhost:8088"
    headers["Access-Control-Allow-Credentials"] = "true"
    headers["Access-Control-Allow-Methods"] = "*"
    headers["Access-Control-Allow-Headers"] = "*"
    return headers

# Exception handlers to ensure CORS headers are sent even on errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=add_cors_headers({})
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers=add_cors_headers({})
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions and ensure CORS headers are included"""
    import traceback
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        },
        headers=add_cors_headers({})
    )

# Initialize database tables
try:
    init_db()
    print("✅ Database tables initialized successfully!")
except Exception as e:
    print(f"⚠️  Warning: Database initialization error: {e}")

# Include routers
from routes import students, subjects, criteria, evaluations, reports

app.include_router(students.router)
app.include_router(subjects.router)
app.include_router(criteria.router)
app.include_router(evaluations.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {"message": "Grade Manager API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8050))
    uvicorn.run(app, host="0.0.0.0", port=port)

