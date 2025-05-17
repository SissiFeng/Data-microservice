import uvicorn
import os
from app.services.file_watcher import get_file_watcher

if __name__ == "__main__":
    # Start file watcher
    file_watcher = get_file_watcher()
    file_watcher.start()
    
    # Start FastAPI server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
