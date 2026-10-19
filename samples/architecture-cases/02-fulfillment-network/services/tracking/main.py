from fastapi import FastAPI
from services.tracking.api import router
app = FastAPI(title='Tracking service')
app.include_router(router)
# Example deployment listens on port 8203.
