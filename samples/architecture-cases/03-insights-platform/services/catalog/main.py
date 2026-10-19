from fastapi import FastAPI
from services.catalog.api import router
app = FastAPI(title='Catalog service')
app.include_router(router)
# Example deployment listens on port 8302.
