import uvicorn
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.app.main import app

if __name__ == "__main__":
    print("Starting Loom API Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
