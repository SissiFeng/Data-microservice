import subprocess # Import subprocess
import os
from app.services.file_watcher import get_file_watcher

if __name__ == "__main__":
    # Start file watcher
    file_watcher = get_file_watcher()
    file_watcher.start()
    
    # Start Litestar server using subprocess
    try:
        subprocess.run(
            ["litestar", "run", "--host", "0.0.0.0", "--port", "8000", "--reload"], 
            check=True
        )
    except FileNotFoundError:
        print("Error: 'litestar' command not found. Make sure Litestar is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Litestar server: {e}")
