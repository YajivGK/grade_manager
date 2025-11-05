#!/usr/bin/env python3
"""
Docker entrypoint script for FastAPI
Handles database connection waiting and initialization
"""
import os
import sys
import time
import subprocess
from pathlib import Path

def wait_for_database():
    """Wait for database to be ready"""
    if os.getenv("WAIT_FOR_DB", "false").lower() != "true":
        return True
    
    try:
        import pymysql
    except ImportError:
        print("⚠️  pymysql not available, skipping database wait")
        return True
    
    max_retries = 30
    retry_count = 0
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "admin")
    db_password = os.getenv("DB_PASSWORD", "")
    
    print("⏳ Waiting for database to be ready...")
    while retry_count < max_retries:
        try:
            connection = pymysql.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                connect_timeout=5
            )
            connection.close()
            print("✅ Database is ready!")
            return True
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"   Database not ready, retrying ({retry_count}/{max_retries})...")
                time.sleep(2)
            else:
                print(f"❌ Database connection failed after {max_retries} retries")
                print(f"   Error: {e}")
                return False
    
    return False

def main():
    """Main entrypoint"""
    # Wait for database if needed
    if not wait_for_database():
        sys.exit(1)
    
    # Run the FastAPI application
    print("🚀 Starting FastAPI application...")
    app_path = Path("/app/backend/main.py")
    
    if not app_path.exists():
        print("❌ Error: main.py not found!")
        sys.exit(1)
    
    # Get port from environment
    port = int(os.getenv("PORT", "8050"))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Execute FastAPI app with uvicorn
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host", host,
            "--port", str(port),
            "--workers", "1"
        ]
    )

if __name__ == "__main__":
    main()

