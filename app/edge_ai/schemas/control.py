# app/edge_ai/schemas/control.py
from pydantic import BaseModel
from typing import Literal, Optional, List

TempMode = Literal["HEAT", "COOL", "OFF"]
HumidMode = Literal["HUMID", "DEHUMID", "OFF"]

class State(BaseModel):
    # 센서 값 (기기에서 직접 들어오는 값)
    temperature: float
    humidity: float
    pm25: float
    tvoc: float
    co2: float
    odor: float

    # 현재 기기 세팅 (참고용)
    fan_level: int             # 1~5
    temp_mode: TempMode
    temp_level: int            # 0~5
    humid_mode: HumidMode
    humid_level: int           # 0~5

class Preference(BaseModel):
    # 자연어에서 파싱한 유저 선호
    temp_pref: Literal["warmer", "cooler", "set", "none"] = "none"
    temp_target: Optional[float] = None
    temp_importance: float = 0.33

    humid_pref: Literal["wetter", "drier", "set", "none"] = "none"
    humid_target: Optional[float] = None
    humid_importance: float = 0.33

    air_pref: Literal["better", "none"] = "none"
    air_importance: float = 0.34

class Control(BaseModel):
    fan_level: int             # 1~5
    temp_mode: TempMode
    temp_level: int            # 0~5
    humid_mode: HumidMode
    humid_level: int           # 0~5
    duration_sec: int = 600    # 유지 시간

class Suggestion(BaseModel):
    title: str
    body: List[str]            # 문장 리스트

class VoicePreferenceResponse(BaseModel):
    recognized_text: str
    preference: Preference