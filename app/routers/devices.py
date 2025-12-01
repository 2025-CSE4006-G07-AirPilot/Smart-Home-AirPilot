from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.device import Device, DeviceBase

from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


@router.get("/", response_model=List[Device])
def list_devices(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return devices


@router.post("/", response_model=Device)
def create_device(device_in: DeviceBase, session: Session = Depends(get_session)):
    device = Device.from_orm(device_in)
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


@router.get("/{device_id}", response_model=Device)
def get_device(device_id: str, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=Device)
def update_device(
    device_id: str,
    device_in: DeviceBase,
    session: Session = Depends(get_session),
):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.room_id = device_in.room_id
    device.name = device_in.name
    device.mode = device_in.mode
    device.smell_class = device_in.smell_class
    device.last_seen = device_in.last_seen
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


@router.delete("/{device_id}")
def delete_device(device_id: str, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    session.delete(device)
    session.commit()
    return {"ok": True}

class DeviceModeUpdate(BaseModel):
    mode: str


@router.post("/{device_id}/mode", response_model=Device)
def update_device_mode(
    device_id: str,
    payload: DeviceModeUpdate,
    session: Session = Depends(get_session),
):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.mode = payload.mode
    # 모드가 바뀌었다는 건 방금 서버와 통신했다는 뜻이라면, last_seen도 갱신하는 게 자연스러움
    device.last_seen = datetime.utcnow()

    session.add(device)
    session.commit()
    session.refresh(device)
    return device


class DeviceReport(BaseModel):
    id: str
    room_id: str
    name: str
    mode: str
    smell_class: str


@router.post("/report", response_model=Device)
def report_device_state(
    payload: DeviceReport,
    session: Session = Depends(get_session),
):
    # 1. 기존 디바이스 있는지 확인
    device = session.get(Device, payload.id)

    if device is None:
        # 없으면 새로 생성
        device = Device(
            id=payload.id,
            room_id=payload.room_id,
            name=payload.name,
            mode=payload.mode,
            smell_class=payload.smell_class,
            last_seen=datetime.utcnow(),
        )
        session.add(device)
    else:
        # 있으면 업데이트
        device.room_id = payload.room_id
        device.name = payload.name
        device.mode = payload.mode
        device.smell_class = payload.smell_class
        device.last_seen = datetime.utcnow()
        session.add(device)

    session.commit()
    session.refresh(device)
    return device
