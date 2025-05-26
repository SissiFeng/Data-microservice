import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app # Main FastAPI app
from app.core.config import settings
from app.db.session import get_session # Original get_session dependency

# Ensure test database URL is used
# You can set this via environment variable or hardcode for tests
# For this example, we'll modify the settings object if a specific test DB URL is set
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://testuser:testpassword@localhost:5432/testdb")
settings.DATABASE_URL = TEST_DATABASE_URL
settings.ALEMBIC_GENERATE_OFFLINE = False # Ensure this is False for tests needing DB interaction

# Create a new async engine for testing
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False) # Set echo=True for SQL logs

# Create a sessionmaker for test sessions
TestAsyncSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Pytest-asyncio event loop fixture
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncEngine:
    """Yield an AsyncEngine instance for the test database."""
    return test_engine

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables(db_engine: AsyncEngine):
    """
    Create database tables before tests run and drop them after.
    Using SQLModel.metadata.create_all for simplicity.
    For Alembic:
    1. Ensure alembic.ini points to test DB (can be done via env var for sqlalchemy.url)
    2. Run `alembic upgrade head`
    3. After tests, `alembic downgrade base` or drop/recreate DB.
    This example uses SQLModel's create_all for simplicity, assuming no complex migrations needed for test setup.
    If Alembic is strictly required:
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini") # Ensure this path is correct
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    yield
    command.downgrade(alembic_cfg, "base")
    """
    async with db_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with db_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a new database session for each test function."""
    async with TestAsyncSessionLocal() as session:
        yield session

# Override FastAPI's get_session dependency for tests
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestAsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an AsyncClient for making requests to the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# --- Mock S3 Service ---
# This is a simplified mock. In a real scenario, you might use moto or a more complex mock.
@pytest.fixture(autouse=True)
def mock_s3_service(mocker):
    """Mocks S3 related operations to avoid actual S3 calls during tests."""
    
    # Mock settings related to S3 to simulate no S3 configured, or a mock bucket
    # This might make the code fall back to local storage or skip S3 steps.
    mocker.patch.object(settings, 'AWS_ACCESS_KEY_ID', None) # Simulate no AWS creds
    mocker.patch.object(settings, 'AWS_SECRET_ACCESS_KEY', None)
    mocker.patch.object(settings, 'S3_BUCKET_NAME', '')

    # If your s3_service module has functions like upload_file, download_file, delete_file,
    # you can mock them directly.
    # Example:
    # from app.services import s3_service as actual_s3_service
    # mocker.patch.object(actual_s3_service, 'upload_file', return_value=True) # or mock implementation
    # mocker.patch.object(actual_s3_service, 'download_file', return_value=True) # or mock implementation
    # mocker.patch.object(actual_s3_service, 'delete_file', return_value=True) # or mock implementation
    
    # For this example, simply disabling AWS keys might be enough if the code
    # gracefully handles it (e.g., by not attempting S3 operations).
    # If the code *requires* S3 interaction (e.g., s3_path is always generated),
    # then the functions themselves need mocking to simulate behavior.
    # For instance, make upload_file just "succeed" without doing anything.
    
    class MockS3Service:
        def upload_file(self, file_path: str, s3_key: str):
            print(f"MOCK S3: Uploading {file_path} to {s3_key} (simulated)")
            # Simulate creating an S3 path, as this is stored in DB
            # This mock assumes the s3_key passed is what should be returned/used
            return s3_key 

        def download_file(self, s3_key: str, local_path: str):
            print(f"MOCK S3: Downloading {s3_key} to {local_path} (simulated)")
            # To make processing tests work, this should create a dummy file at local_path
            # based on s3_key or a predefined test file.
            # For now, let's assume the test will provide the file for processing locally.
            # If the test relies on this download, create a dummy file:
            with open(local_path, 'w') as f:
                f.write("mock_column1,mock_column2\n1,2\n3,4\n") # Dummy CSV content

        def delete_file(self, s3_key: str):
            print(f"MOCK S3: Deleting {s3_key} (simulated)")
            return True

    # Find where s3_service is imported and used, then mock that specific instance or module.
    # If s3_service is a module:
    # mocker.patch('app.services.s3_service.upload_file', MockS3Service().upload_file)
    # mocker.patch('app.services.s3_service.download_file', MockS3Service().download_file)
    # mocker.patch('app.services.s3_service.delete_file', MockS3Service().delete_file)
    # This assumes s3_service module has these functions at the top level.
    # If they are methods of a class instance, mock the class or instance.
    # For now, the simple disabling of AWS keys might be enough if the code skips S3.
    # If not, more specific mocking of s3_service functions in tasks.py and data.py is needed.

    # Let's assume s3_service is imported in relevant modules like `app.api.endpoints.data` and `app.tasks`
    # A common pattern is to mock at the point of use or where it's imported.
    try:
        mocker.patch('app.api.endpoints.data.s3_service.upload_file', new=MockS3Service().upload_file)
        mocker.patch('app.api.endpoints.data.s3_service.delete_file', new=MockS3Service().delete_file)
    except AttributeError: # If not used directly in data.py, or path is different
        pass 
    try:
        mocker.patch('app.tasks.s3_service.download_file', new=MockS3Service().download_file)
        # If tasks.py also uploads (e.g. processed results), mock that too.
    except AttributeError:
        pass
    
    # This mock setup is basic. If s3_service is an instance of a class,
    # it would be better to mock the class or use dependency injection for it.
    # For now, patching where it's imported is a common approach.

    # The initial settings patch to disable AWS keys is a good first step.
    # If tests fail due to S3 calls, the specific function mocks above will be necessary.

# Fixture to provide a sample CSV file content for upload tests
@pytest.fixture
def sample_csv_file() -> tuple[str, bytes]:
    filename = "test_upload.csv"
    content = b"timestamp,value1,value2\n0,1,10\n1,2,20\n2,3,30\n3,4,40\n4,5,50"
    return filename, content

# Fixture for Celery app - needed for inspecting task results
# This requires Celery to be configured for testing (e.g., EAGER mode)
# For this integration test, we'll rely on polling the API, so direct Celery app fixture might not be strictly needed here
# but useful for more advanced Celery testing.
# @pytest.fixture(scope='session')
# def celery_app_for_testing(request):
#     from app.celery_worker import celery_app as actual_celery_app
#     actual_celery_app.conf.update(task_always_eager=True) # Run tasks locally, not in worker
#     return actual_celery_app
