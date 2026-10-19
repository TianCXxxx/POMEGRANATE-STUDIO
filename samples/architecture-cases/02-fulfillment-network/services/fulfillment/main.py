from fastapi import FastAPI
from services.fulfillment.api import router
app = FastAPI(title='Fulfillment service')
app.include_router(router)
# Example deployment listens on port 8200.
