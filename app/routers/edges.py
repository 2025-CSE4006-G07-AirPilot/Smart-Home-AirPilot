from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.edge import Edge, EdgeBase

router = APIRouter()


@router.get("/", response_model=List[Edge])
def list_edges(session: Session = Depends(get_session)):
    edges = session.exec(select(Edge)).all()
    return edges


@router.post("/", response_model=Edge)
def create_edge(edge_in: EdgeBase, session: Session = Depends(get_session)):
    edge = Edge.from_orm(edge_in)
    session.add(edge)
    session.commit()
    session.refresh(edge)
    return edge


@router.get("/{edge_id}", response_model=Edge)
def get_edge(edge_id: str, session: Session = Depends(get_session)):
    edge = session.get(Edge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge


@router.put("/{edge_id}", response_model=Edge)
def update_edge(
    edge_id: str,
    edge_in: EdgeBase,
    session: Session = Depends(get_session),
):
    edge = session.get(Edge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")

    edge.from_room_id = edge_in.from_room_id
    edge.to_room_id = edge_in.to_room_id
    session.add(edge)
    session.commit()
    session.refresh(edge)
    return edge


@router.delete("/{edge_id}")
def delete_edge(edge_id: str, session: Session = Depends(get_session)):
    edge = session.get(Edge, edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")

    session.delete(edge)
    session.commit()
    return {"ok": True}
