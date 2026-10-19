from fastapi import FastAPI
from services.inventory.api import router
app = FastAPI(title='Inventory service')
app.include_router(router)
# Example deployment listens on port 8101.
