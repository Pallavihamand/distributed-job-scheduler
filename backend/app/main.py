
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine


# ============================================================
# IMPORT ALL DATABASE MODELS
# ============================================================

from app.models import (
    User,
    Organization,
    Project,
    Queue,
    RetryPolicy,
    Worker,
    Job,
    JobExecution,
    WorkerHeartbeat,
    JobLog,
    DeadLetterJob,
    ScheduledJob,
)


# ============================================================
# IMPORT API ROUTES
# ============================================================

from app.routes import (
    user,
    auth,
    organization,
    projects,
    queues,
    jobs,
    workers,
    scheduled_jobs,
    dashboard,
)


# ============================================================
# DATABASE TABLE CREATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Distributed Job Scheduler",
    description=(
        "Production-inspired distributed "
        "background job scheduling platform"
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REGISTER API ROUTERS
# ============================================================

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(projects.router)
app.include_router(queues.router)
app.include_router(jobs.router)
app.include_router(workers.router)
app.include_router(scheduled_jobs.router)
app.include_router(dashboard.router)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Distributed Job Scheduler API",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
    }

