import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# Ensure root path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.database import engine, Base
from backend.routers import auth, users, exams, questions, attempts, results
from backend.seed import seed_database

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ExamCloud AI — Cloud Online Examination API",
    description="REST API powering the ExamCloud AI online examination platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed database automatically if clean setup
try:
    seed_database()
except Exception as e:
    print(f"Seed note: {e}")

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(exams.router)
app.include_router(questions.router)
app.include_router(attempts.router)
app.include_router(results.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ExamCloud AI Backend API", "version": "1.0.0"}

# Mount frontend as static directory if serving together
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="frontend")

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")
