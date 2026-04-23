from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.alerts.router import router as alerts_router
from app.reminders.router import router as reminders_router
from app.debug.router import router as debug_router

app = FastAPI(title="Alera Backend")

Base.metadata.create_all(bind=engine)

app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(debug_router, prefix="/debug", tags=["debug"])
app.include_router(reminders_router)