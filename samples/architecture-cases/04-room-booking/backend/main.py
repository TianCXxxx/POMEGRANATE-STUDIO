from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api import router
from backend.dependencies import database

app = FastAPI(title="会议室预约系统")
database.initialize()
app.include_router(router)
app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "web", html=True), name="web")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
