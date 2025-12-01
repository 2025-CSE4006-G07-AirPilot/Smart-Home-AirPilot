from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.room import Room, RoomBase

router = APIRouter()


@router.get("/", response_model=List[Room])
def list_rooms(session: Session = Depends(get_session)):
    rooms = session.exec(select(Room)).all()
    return rooms


@router.post("/", response_model=Room)
def create_room(room_in: RoomBase, session: Session = Depends(get_session)):
    room = Room.from_orm(room_in)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


@router.get("/{room_id}", response_model=Room)
def get_room(room_id: str, session: Session = Depends(get_session)):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.put("/{room_id}", response_model=Room)
def update_room(
    room_id: str,
    room_in: RoomBase,
    session: Session = Depends(get_session),
):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.name = room_in.name
    room.description = room_in.description
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


@router.delete("/{room_id}")
def delete_room(room_id: str, session: Session = Depends(get_session)):
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    session.delete(room)
    session.commit()
    return {"ok": True}
