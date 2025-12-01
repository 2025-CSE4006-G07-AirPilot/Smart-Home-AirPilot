from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

def gen_uuid() -> str:
    return str(uuid.uuid4())

class RoomBase(SQLModel):
    name: str
    description: Optional[str] = None

class Room(RoomBase, table=True):
    id: str = Field(default_factory=gen_uuid, primary_key=True, index=True)
