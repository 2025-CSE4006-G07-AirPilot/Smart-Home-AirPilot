# app/edge_ai/routers/nlp.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.edge_ai.schemas.control import Preference
from app.edge_ai.services.edge_nlp_service import parse_preference

router = APIRouter(prefix="/edge-ai/nlp", tags=["edge-ai"])

class TextIn(BaseModel):
    text: str

@router.post("/preference", response_model=Preference)
def nlp_preference(body: TextIn):
    return parse_preference(body.text)
