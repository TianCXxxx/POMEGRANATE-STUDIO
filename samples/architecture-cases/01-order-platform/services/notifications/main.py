from fastapi import FastAPI
from services.notifications.api import router
app = FastAPI(title='Notification service')
app.include_router(router)
# Example deployment listens on port 8103.
