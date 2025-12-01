# app/edge_ai/schemas/feedback.py
from pydantic import BaseModel
from typing import Optional
from .control import State, Preference, Control

class Feedback(BaseModel):
    device_id: str
    state: State
    preference: Preference
    control_applied: Control    # 우리가 제안한 설정

    # 유저가 실제로 바꿨는지 / 평가
    user_overridden: bool = False
    user_final_fan_level: Optional[int] = None
    user_final_temp_target: Optional[float] = None
    user_final_humid_target: Optional[float] = None
    user_comfort_rating: Optional[int] = None   # 1~5
