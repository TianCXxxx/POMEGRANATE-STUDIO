from fastapi import FastAPI
from services.orders.api import router
app = FastAPI(title='Order service')
app.include_router(router)
# Example deployment listens on port 8100.
