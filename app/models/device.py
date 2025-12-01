from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

from .room import Room  # FK 용도

def gen_uuid() -> str:
    return str(uuid.uuid4())

class DeviceBase(SQLModel):
    room_id: str = Field(foreign_key="room.id")
    name: str
    mode: str
    smell_class: str
    last_seen: datetime = Field(default_factory=datetime.utcnow)

class Device(DeviceBase, table=True):
    id: str = Field(default_factory=gen_uuid, primary_key=True, index=True)
