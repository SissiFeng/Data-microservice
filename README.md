# Data Processing Microservice

A modern microservice for data processing, visualization, and analysis with a focus on experimental data.

![Data Microservice Screenshot](docs/images/screenshot.png) <!-- Assuming this image exists -->

## Features

- **Data Upload**: Support for CSV, Excel, and text formats.
- **Data Processing**: Advanced ETL capabilities including:
  - Rolling mean calculation
  - Peak detection
  - Data quality assessment
  - Asynchronous ETL processing using Celery.
  - Support for Custom ETL Processing Workflows (via custom Python scripts).
- **Interactive Visualization**: Real-time visualization of raw and processed data.
- **Annotation System**: Add notes and annotations to data points and regions.
- **Real-time Updates**: ETL status and annotation changes are pushed to clients via WebSockets.
- **Optimizer Interface**: API for connecting to subsequent optimization modules.
- **Export Capabilities**: Export processed data in various formats (CSV, JSON).
- **Mock Mode**: Frontend can operate without backend for development and demonstration.

## Architecture

The application follows a microservice architecture with:

- **Frontend**: React + TypeScript application with modern UI components.
- **Backend**: Python Litestar service for data processing and storage.
- **Database**: PostgreSQL, managed with SQLModel (ORM) and Alembic for migrations.
- **File Storage**: Local or S3-compatible storage for data files.
- **Message Broker**: Redis (for Celery).
- **Task Queue**: Celery (for asynchronous ETL processing).
- **Optimizer API**: A dedicated API (`/api/optimizer`) for optimization tasks.

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- Redis (if running manually without Docker)

### Installation

#### Using Docker (Recommended)

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/data-microservice.git # Replace with actual repo URL
    cd data-microservice
    ```

2.  Create a `.env` file from `.env.example` and populate it with your AWS credentials (if using S3) and desired PostgreSQL settings (e.g., `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`). Celery and Redis settings will use defaults if not specified.
    ```bash
    cp .env.example .env
    # nano .env  (or your preferred editor to fill in details)
    ```

3.  Start the services:
    ```bash
    docker-compose up -d --build
    ```
    This command starts the frontend, backend, PostgreSQL database, Redis message broker, and Celery worker services.
    Database migrations (Alembic) should be applied automatically by the backend service on startup. If you need to run them manually after services are up:
    ```bash
    docker-compose exec backend alembic upgrade head
    ```

4.  Access the application at `http://localhost` (frontend) and the backend API at `http://localhost:8000`.

#### Manual Setup

1.  Clone the repository.
2.  **Set up the Backend**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    
    # Ensure you have a .env file in the project root (../.env) with database credentials
    # and other settings like AWS keys, Celery broker URL (e.g., redis://localhost:6379/0).
    # Example for .env:
    # POSTGRES_USER=user
    # POSTGRES_PASSWORD=password
    # POSTGRES_DB=app
    # POSTGRES_HOST=localhost
    # POSTGRES_PORT=5432
    # CELERY_BROKER_URL=redis://localhost:6379/0
    # CELERY_RESULT_BACKEND=redis://localhost:6379/0
    # AWS_ACCESS_KEY_ID=your_aws_key (optional)
    # AWS_SECRET_ACCESS_KEY=your_aws_secret (optional)
    # S3_BUCKET_NAME=your_bucket_name (optional)
    
    # Ensure PostgreSQL server and Redis server are running and accessible.
    
    # Apply database migrations
    alembic upgrade head
    
    # Start the Litestar backend (e.g., in one terminal)
    python run.py # This script now uses 'litestar run --reload'

    # Start the Celery worker (e.g., in another terminal, from the 'backend' directory)
    # Ensure your virtual environment is activated
    celery -A app.celery_worker.celery_app worker -l info -P eventlet 
    # (Use -P eventlet or -P gevent for async tasks with Celery with asyncio. Default is prefork.)
    ```

3.  **Set up the Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

4.  Access the frontend at `http://localhost:5173` and the backend API at `http://localhost:8000`.

## Usage

### Uploading Data
(As previously described)

### Processing Data
1.  Select a file from the file list.
2.  Choose a processing type (e.g., Rolling Mean, Peak Detection, Data Quality, or Custom).
3.  Configure processing parameters.
    -   For **Custom** processing, select "Custom" as the type, then provide the "Custom Script Name" (e.g., `example_custom_processor` without `.py`) and any specific parameters for that script in JSON format in the "Custom Parameters (JSON)" field.
4.  Click "Process Data". The task will be submitted to Celery for asynchronous processing. The UI will show a "PENDING" status and should update via WebSockets.
5.  View the results in the visualization panel. Status updates may appear in real-time.

### Annotating Data
(As previously described - updates are now real-time via WebSockets)

### Exporting Results
(As previously described)

### Triggering Optimization (Placeholder)
1.  After a processing result is generated and available.
2.  Navigate to the "Optimizer Panel" (now part of the main processing control area, visible when a processing result is selected).
3.  The Processing Result ID should be pre-filled if a result is selected.
4.  Provide any optimizer-specific parameters in JSON format.
5.  Click "Run Optimizer".
(Note: The optimizer functionality is currently a placeholder in the backend and simulates a run.)

## Development

### Project Structure
(Key additions/changes)
```
data-microservice/
├── backend/
│   ├── app/
│   │   ├── api/       # API Endpoints (data, etl, annotations, optimizer, websocket)
│   │   ├── core/      # Configuration, core settings
│   │   ├── db/        # Database session, SQLModel models
│   │   │   ├── models.py  # SQLModel ORM models
│   │   ├── etl/       # ETL processing logic
│   │   │   ├── processors/ # Standard and custom processors
│   │   │   │   ├── custom/ # Custom Python ETL scripts
│   │   ├── services/  # Business logic services (e.g., S3, optimizer)
│   │   ├── tasks.py   # Celery tasks (e.g., process_data_task)
│   │   └── celery_worker.py # Celery application instance
│   ├── alembic/       # Alembic migration scripts
│   └── ...
└── ...
```

### ETL Components
The ETL (Extract, Transform, Load) components are the core of the data processing functionality. See [ETL Documentation](docs/ETL_Documentation.md) for details on asynchronous processing and custom workflows.

### Mock Mode
(As previously described)

## API Documentation
The backend API documentation (Swagger UI) is available at `http://localhost:8000/schema/swagger` when the backend is running. Redoc documentation is available at `/schema/redoc`. This includes endpoints for data, ETL, annotations, and the new `/api/optimizer`.

## Contributing
(As previously described)

## License
(As previously described)
```
