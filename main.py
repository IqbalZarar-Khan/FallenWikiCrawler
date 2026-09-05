import os
import uvicorn
from app import app

if __name__ == "__main__":
    HOST = os.environ.get("HOST", "0.0.0.0")
    try:
        PORT = int(os.environ.get("PORT", "8000"))
    except (ValueError, TypeError):
        PORT = 8000
    uvicorn.run(app, host=HOST, port=PORT)
