from pydantic import BaseModel
from datetime import datetime


class Metric(BaseModel):
    type: str
    value: float
    unit: str


class Timestamp(BaseModel):
    recordedAt: datetime
    receivedAt: datetime


class Device(BaseModel):
    id: str | None = None
    type: str | None = None
    batteryLevel: int | None = None
    isConnected: bool | None = None


class Event(BaseModel):
    eventId: str
    patientId: str
    metric: Metric
    timestamp: Timestamp
    device: Device | None = None