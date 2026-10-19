from fastapi import FastAPI
from services.reports.api import router
app = FastAPI(title='Report service')
app.include_router(router)
# Example deployment listens on port 8303.
