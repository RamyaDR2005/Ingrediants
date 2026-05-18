"""
SafeScan - Main Entry Point
Starts both the FastAPI backend and Streamlit frontend
"""
import subprocess
import time
import os
import sys
import signal

def run_app():
    """Run the application."""
    print("\n🔬 SafeScan - AI Ingredient Scanner")
    print("=" * 40)
    print("\nTech Stack:")
    print("  ✓ Frontend: Streamlit")
    print("  ✓ Backend: Python + FastAPI")
    print("  ✓ OCR: PaddleOCR")
    print("  ✓ Database: SQLite")
    print("  ✓ Image Processing: PIL")
    print("  ✓ Visualization: Plotly")
    print("\n" + "=" * 40)
    
    # Start backend
    print("\n🚀 Starting Backend API (Port 8000)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", 
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for backend to start
    time.sleep(3)
    
    try:
        print("✅ Backend API started at http://localhost:8000")
        print("📚 API Docs at http://localhost:8000/docs\n")
        
        # Start Streamlit
        print("🚀 Starting Streamlit Frontend (Port 8501)...")
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "main_app.py",
             "--server.port=8501", "--server.address=0.0.0.0"],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down...")
        backend_process.terminate()
        sys.exit(0)
    finally:
        backend_process.terminate()

if __name__ == "__main__":
    # Initialize database
    from backend.database import init_db
    init_db()
    
    # Run application
    run_app()

