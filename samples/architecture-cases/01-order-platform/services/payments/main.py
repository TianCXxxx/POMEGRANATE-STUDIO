from fastapi import FastAPI
from services.payments.api import router
app = FastAPI(title='Payment service')
app.include_router(router)
# Example deployment listens on port 8102.
