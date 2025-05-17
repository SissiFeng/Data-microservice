# Data Processing Microservice

A modern microservice for data processing, visualization, and analysis with a focus on experimental data.

![Data Microservice Screenshot](docs/images/screenshot.png)

## Features

- **Data Upload**: Support for CSV, Excel, and text formats
- **Data Processing**: Advanced ETL capabilities including:
  - Rolling mean calculation
  - Peak detection
  - Data quality assessment
  - Custom processing workflows
- **Interactive Visualization**: Real-time visualization of raw and processed data
- **Annotation System**: Add notes and annotations to data points and regions
- **Export Capabilities**: Export processed data in various formats (CSV, JSON)
- **Mock Mode**: Frontend can operate without backend for development and demonstration

## Architecture

The application follows a microservice architecture with:

- **Frontend**: React + TypeScript application with modern UI components
- **Backend**: Python FastAPI service for data processing and storage
- **Database**: PostgreSQL for data persistence
- **File Storage**: Local or S3-compatible storage for data files

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- Docker and Docker Compose (for containerized deployment)

### Installation

#### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/data-microservice.git
   cd data-microservice
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Access the application at http://localhost:80

#### Manual Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/data-microservice.git
   cd data-microservice
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python run.py
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. Access the frontend at http://localhost:5173 and the backend at http://localhost:8000

## Usage

### Uploading Data

1. Navigate to the main page
2. Use the file upload component to select a CSV, Excel, or text file
3. Fill in the metadata (experiment ID, operator, material, etc.)
4. Click "Upload Data"

### Processing Data

1. Select a file from the file list
2. Choose a processing type (Rolling Mean, Peak Detection, etc.)
3. Configure processing parameters
4. Click "Process Data"
5. View the results in the visualization panel

### Annotating Data

1. Select a processed file
2. Choose an annotation type
3. Add notes or observations
4. Click "Save Annotation"

### Exporting Results

1. Process a file
2. Go to the Export panel
3. Choose an export format (CSV or JSON)
4. Click "Export"

## Development

### Project Structure

```
data-microservice/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   └── run.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── docs/
└── docker-compose.yml
```

### ETL Components

The ETL (Extract, Transform, Load) components are the core of the data processing functionality. See [ETL Documentation](docs/ETL_Documentation.md) for details.

### Mock Mode

The frontend includes a mock mode that allows it to function without a backend connection. This is useful for:
- Development without a backend
- Demonstrations
- Testing UI components

To enable mock mode, set `useMockData = true` in `frontend/src/services/api.ts`.

## API Documentation

The backend API documentation is available at http://localhost:8000/docs when the backend is running.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
