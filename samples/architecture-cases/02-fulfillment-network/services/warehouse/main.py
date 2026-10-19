from fastapi import FastAPI
from services.warehouse.api import router
app = FastAPI(title='Warehouse service')
app.include_router(router)
# Example deployment listens on port 8201.
