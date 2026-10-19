from fastapi import FastAPI
from services.identity.api import router
app = FastAPI(title='Identity service')
app.include_router(router)
# Example deployment listens on port 8301.
