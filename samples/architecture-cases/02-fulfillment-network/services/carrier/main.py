from fastapi import FastAPI
from services.carrier.api import router
app = FastAPI(title='Carrier service')
app.include_router(router)
# Example deployment listens on port 8202.
