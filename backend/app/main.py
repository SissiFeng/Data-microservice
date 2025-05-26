from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.endpoints import data, etl, annotations, websocket, optimizer # Added optimizer
from app.db.session import create_db_and_tables # Import create_db_and_tables

app = FastAPI(
    title="Data Processing Microservice",
    description="Microservice for Data Ingestion, ETL, Visualization & Annotation",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(etl.router, prefix="/api/etl", tags=["etl"])
app.include_router(annotations.router, prefix="/api/annotations", tags=["annotations"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["optimizer"]) # Added optimizer router
app.include_router(websocket.router, tags=["websocket"])

# Mount static files (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to Data Processing Microservice API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
