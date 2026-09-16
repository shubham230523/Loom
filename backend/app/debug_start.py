import sys
import os
import traceback

sys.path.append(os.getcwd())

print("Attempting to start backend...")

try:
    import uvicorn
    from backend.app.main import app
    print("Starting uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
except Exception as e:
    with open("crash.txt", "w") as f:
        f.write(traceback.format_exc())
    print(f"CRASHED: {str(e)}")
    sys.exit(1)
except BaseException as be:
    with open("crash.txt", "w") as f:
        f.write(f"BaseException: {traceback.format_exc()}")
    print("BaseException CRASHED")
    sys.exit(1)
