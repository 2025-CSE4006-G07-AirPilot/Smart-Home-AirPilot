from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

from .room import Room  # FK 용도로 import만

def gen_uuid() -> str:
    return str(uuid.uuid4())

class EdgeBase(SQLModel):
    from_room_id: str = Field(foreign_key="room.id")
    to_room_id: str = Field(foreign_key="room.id")

class Edge(EdgeBase, table=True):
    id: str = Field(default_factory=gen_uuid, primary_key=True, index=True)
