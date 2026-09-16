import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tools.db_tool import database_status
from trip_planner import router as trip_planner_router

app = FastAPI(title="AI Trip Planner", version="1.0.0")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
origins = ["*"] if frontend_origin == "*" else [frontend_origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_planner_router, tags=["Trip Planner"])


@app.get("/")
def home():
    return {
        "status": "AI Trip Planner backend is running",
        "planner": "/api/plan-trip",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    return database_status()
