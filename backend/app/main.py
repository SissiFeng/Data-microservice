from litestar import Litestar, get
from litestar.middleware.cors import CORSMiddlewareConfig
from litestar.static_files import StaticFilesConfig
from litestar.di import Provide # Import Provide

# import uvicorn # Removed uvicorn import

# Import routers and session management
from app.api.endpoints.data import router as data_router
from app.api.endpoints.etl import etl_router # Import etl_router
from app.api.endpoints.annotations import annotations_router # Import annotations_router
from app.api.endpoints.optimizer import optimizer_router # Import optimizer_router
from app.api.endpoints.websocket import websocket_router # Import websocket_router
from app.db.session import create_db_and_tables, get_session # Import get_session

# Configure CORS
cors_config = CORSMiddlewareConfig(
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (if needed)
# static_files_config = StaticFilesConfig(directories=["static"], path="/static") # Updated for future use

async def on_startup_function(): # Renamed and defined for Litestar
    await create_db_and_tables()

app = Litestar(
    route_handlers=[data_router, etl_router, annotations_router, optimizer_router, websocket_router], # Added websocket_router
    title="Data Processing Microservice",
    description="Microservice for Data Ingestion, ETL, Visualization & Annotation",
    version="0.1.0",
    middleware=[cors_config.middleware],
    on_startup=[on_startup_function],
    dependencies={"session": Provide(get_session, sync_to_thread=False)}, # Added get_session dependency
    # static_files_config=[static_files_config], # Add if static files are needed
)

# Include other routers - These will be refactored and added to route_handlers later
# app.include_router(etl.router, prefix="/api/etl", tags=["etl"])
# app.include_router(annotations.router, prefix="/api/annotations", tags=["annotations"])
# app.include_router(optimizer.router, prefix="/api/optimizer", tags=["optimizer"]) # Added optimizer router
# app.include_router(websocket.router, tags=["websocket"])


@get("/")
async def root() -> dict[str, str]: # Updated for Litestar
    return {"message": "Welcome to Data Processing Microservice API"}

# Removed uvicorn.run block as Litestar uses CLI or separate Uvicorn config
# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
