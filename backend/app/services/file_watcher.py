import os
import time
import uuid
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import pandas as pd

from app.core.config import settings
from app.schemas.data import DataStatus, DataMetadata, DataSource
from app.services import s3_service
from app.db.session import engine
from app.db.models import DataFile as DBDataFile
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
import asyncio

class DataFileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.processed_files = set()
        self.processing_files = set()
        self.last_modified_times = {}

    def on_created(self, event):
        if event.is_directory:
            return

        # Check if file is a CSV or other supported format
        if not self._is_supported_file(event.src_path):
            return

        # Store the file path for processing after a delay
        self._schedule_processing(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return

        # Check if file is a CSV or other supported format
        if not self._is_supported_file(event.src_path):
            return

        # Update the last modified time
        self.last_modified_times[event.src_path] = time.time()

        # Schedule processing if not already scheduled
        if event.src_path not in self.processing_files:
            self._schedule_processing(event.src_path)

    def _schedule_processing(self, file_path):
        """Schedule a file for processing after a delay"""
        self.processing_files.add(file_path)
        self.last_modified_times[file_path] = time.time()

        # Start a thread to wait for file to stabilize before processing
        import threading
        thread = threading.Thread(target=self._wait_and_process, args=(file_path,))
        thread.daemon = True
        thread.start()

    def _wait_and_process(self, file_path):
        """Wait for file to stabilize (no modifications for a period) then process it"""
        # Wait for file to stabilize (no modifications for 2 seconds)
        stable_wait = 2  # seconds
        max_wait = 30    # maximum seconds to wait
        start_time = time.time()

        while True:
            current_time = time.time()
            last_modified = self.last_modified_times.get(file_path, 0)

            # If file hasn't been modified for stable_wait seconds, process it
            if current_time - last_modified >= stable_wait:
                break

            # If we've waited too long, process anyway
            if current_time - start_time >= max_wait:
                print(f"Max wait time reached for {file_path}, processing anyway")
                break

            time.sleep(0.5)

        # Process the file
        try:
            self._process_file(file_path)
        finally:
            # Remove from processing set
            self.processing_files.discard(file_path)
            # Remove from last modified times
            if file_path in self.last_modified_times:
                del self.last_modified_times[file_path]

    def _is_supported_file(self, file_path):
        """Check if file is a supported format"""
        supported_extensions = ['.csv', '.xlsx', '.xls', '.txt']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in supported_extensions

    def _process_file(self, file_path):
        """Process a new file"""
        # Check if already processed
        if file_path in self.processed_files:
            return

        # Check if file still exists (might have been deleted)
        if not os.path.exists(file_path):
            print(f"File no longer exists: {file_path}")
            return

        # Check if file is empty
        if os.path.getsize(file_path) == 0:
            print(f"Skipping empty file: {file_path}")
            return

        # Add to processed files set
        self.processed_files.add(file_path)

        try:
            # Create a unique ID for the file
            file_id = str(uuid.uuid4())
            filename = os.path.basename(file_path)

            # Try to validate the file format
            try:
                # For CSV files, try to read with pandas to validate
                if filename.lower().endswith('.csv'):
                    df = pd.read_csv(file_path)
                    if df.empty:
                        print(f"Skipping empty CSV file: {file_path}")
                        return

                    # Add row count to metadata
                    row_count = len(df)
                    column_count = len(df.columns)
                    print(f"File {filename} has {row_count} rows and {column_count} columns")
            except Exception as e:
                print(f"Warning: Could not validate file format for {file_path}: {str(e)}")
                # Continue processing anyway

            # Create metadata
            metadata = DataMetadata(
                source=DataSource.WATCH,
                timestamp=datetime.now(),
                additional_metadata={
                    "auto_detected": True,
                    "file_size_bytes": os.path.getsize(file_path),
                    "detection_time": datetime.now().isoformat()
                }
            )

            # Ensure data directory exists
            os.makedirs(settings.DATA_DIR, exist_ok=True)

            # Copy file to data directory
            dest_path = os.path.join(settings.DATA_DIR, f"{file_id}_{filename}")
            try:
                shutil.copy2(file_path, dest_path)
            except Exception as e:
                print(f"Error copying file to data directory: {str(e)}")
                return

            s3_key = None
            # Upload to S3 if configured
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                try:
                    s3_key = f"raw/{file_id}/{filename}"
                    s3_upload_success = s3_service.upload_file(dest_path, s3_key)
                    if s3_upload_success:
                        print(f"Successfully uploaded {filename} to S3 with key: {s3_key}")
                    else:
                        print(f"Failed to upload {filename} to S3")
                except Exception as e:
                    print(f"Error uploading to S3: {str(e)}")

            async def _save_record():
                async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                async with async_session() as session:
                    db_entry = DBDataFile(
                        id=file_id,
                        filename=filename,
                        s3_path=s3_key,
                        file_metadata=metadata.dict(),
                    )
                    session.add(db_entry)
                    await session.commit()

            asyncio.run(_save_record())

            print(f"Processed new file: {filename} (ID: {file_id})")

            # Notify via WebSocket (to be implemented)
            # await notify_clients("new_data", {"id": file_id, "filename": filename})

        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            # Remove from processed files set if processing failed
            # so we can try again later if the file is modified
            self.processed_files.discard(file_path)

class FileWatcher:
    def __init__(self, watch_dir=None):
        self.watch_dir = watch_dir or settings.WATCH_DIR
        self.event_handler = DataFileHandler()
        self.observer = None
        self.is_running = False
        self.health_check_interval = 60  # seconds

    def start(self):
        """Start watching for new files"""
        if self.is_running:
            print("File watcher is already running")
            return

        # Ensure watch directory exists
        os.makedirs(self.watch_dir, exist_ok=True)

        # Create and start observer
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_dir, recursive=True)

        try:
            self.observer.start()
            self.is_running = True
            print(f"Started watching directory: {self.watch_dir}")

            # Start health check thread
            import threading
            self.health_check_thread = threading.Thread(target=self._health_check)
            self.health_check_thread.daemon = True
            self.health_check_thread.start()

            # Process any existing files in the watch directory
            self._process_existing_files()

        except Exception as e:
            print(f"Error starting file watcher: {str(e)}")
            if self.observer:
                self.observer.stop()
                self.observer.join()
            self.is_running = False

    def stop(self):
        """Stop watching for new files"""
        if not self.is_running:
            print("File watcher is not running")
            return

        try:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("Stopped watching directory")
        except Exception as e:
            print(f"Error stopping file watcher: {str(e)}")

    def _health_check(self):
        """Periodically check if the observer is still running"""
        while self.is_running:
            time.sleep(self.health_check_interval)

            if not self.observer.is_alive():
                print("Observer thread died, restarting...")
                self.stop()
                time.sleep(1)
                self.start()

    def _process_existing_files(self):
        """Process any existing files in the watch directory"""
        try:
            for root, _, files in os.walk(self.watch_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if self.event_handler._is_supported_file(file_path):
                        print(f"Found existing file: {file_path}")
                        self.event_handler._schedule_processing(file_path)
        except Exception as e:
            print(f"Error processing existing files: {str(e)}")

# Singleton instance
file_watcher = None

def get_file_watcher():
    """Get or create the file watcher instance"""
    global file_watcher
    if file_watcher is None:
        file_watcher = FileWatcher()
    return file_watcher
