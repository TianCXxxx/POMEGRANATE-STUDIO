from fastapi import FastAPI
from services.metrics.api import router
app = FastAPI(title='Metrics service')
app.include_router(router)
# Example deployment listens on port 8300.
