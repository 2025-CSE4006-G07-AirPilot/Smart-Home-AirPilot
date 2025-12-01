# app/edge_ai/schemas/profile.py
from pydantic import BaseModel
from typing import Optional

class DeviceProfile(BaseModel):
    device_id: str

    # 온도 기준 (각 기기별 온도 타겟/밴드)
    temp_target: float = 24.0
    temp_band_comfort: float = 0.5
    temp_band_mild: float = 1.5
    temp_band_strong: float = 3.0

    # 습도 기준
    humid_target: float = 45.0
    humid_band_comfort: float = 5.0
    humid_band_mild: float = 10.0
    humid_band_strong: float = 20.0

    # 공기질 민감도 가중치
    w_pm25: float = 0.4
    w_co2: float = 0.3
    w_tvoc: float = 0.2
    w_odor: float = 0.1

    # 팬 세기 선호 (기본 룰 + bias)
    fan_bias: int = 0   # -2 ~ +2 정도로 관리

    # 간단한 “학습 상태”용 필드
    overrides_count: int = 0
    last_updated_ts: Optional[float] = None
