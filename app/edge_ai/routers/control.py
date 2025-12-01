# app/edge_ai/routers/control.py
from fastapi import APIRouter
from app.edge_ai.schemas.control import State, Preference
from app.edge_ai.schemas.feedback import Feedback
from app.edge_ai.services.ai_service import decide_control_and_suggestion
from app.edge_ai.services.feedback_service import apply_feedback

router = APIRouter(prefix="/edge-ai/control", tags=["edge-ai"])

@router.post("/decide")
def control_decide(device_id: str, state: State, preference: Preference):
    control, suggestion = decide_control_and_suggestion(
        device_id=device_id,
        state=state,
        pref=preference,
        use_gpt_suggestion=True,
    )
    return {
        "control": control,
        "suggestion": suggestion,
        "pass_through": {
            "device_id": device_id,
            "state": state,
        },
    }

@router.post("/feedback")
def control_feedback(fb: Feedback):
    profile = apply_feedback(fb)
    return {"ok": True, "profile": profile}
