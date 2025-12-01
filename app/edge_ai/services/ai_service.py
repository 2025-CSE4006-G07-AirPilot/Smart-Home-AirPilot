# app/edge_ai/services/ai_service.py
from app.edge_ai.schemas.control import State, Preference, Control, Suggestion
from app.edge_ai.core.profile_store import load_profile
from app.edge_ai.models.policy_rule import decide_control_rule
from app.edge_ai.services.edge_suggestion_service import (
    build_suggestion_template,
    build_suggestion_gpt,
)

def decide_control_and_suggestion(
    device_id: str,
    state: State,
    pref: Preference,
    use_gpt_suggestion: bool = True,
) -> tuple[Control, Suggestion]:
    profile = load_profile(device_id)
    control = decide_control_rule(state, pref, profile)

    if use_gpt_suggestion:
        suggestion = build_suggestion_gpt(state, pref, control)
    else:
        suggestion = build_suggestion_template(state, pref, control)

    return control, suggestion
