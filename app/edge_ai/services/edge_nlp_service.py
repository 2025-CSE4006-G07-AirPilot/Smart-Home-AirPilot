# app/edge_ai/services/edge_nlp_service.py
from app.edge_ai.models.nlp_client import call_gpt_json
from app.edge_ai.schemas.control import Preference

SYSTEM_PROMPT = """
너는 공기청정기/에어컨/제습기 제어를 위한 '선호도 파서'이다.
사용자의 한국어 문장을 아래 JSON 스키마에 맞게만 변환해라.

{
  "temp_pref": "warmer|cooler|none",
  "temp_target": float | null,
  "temp_importance": 0.0~1.0,

  "humid_pref": "wetter|drier|none",
    "humid_target": float | null,
  "humid_importance": 0.0~1.0,

  "air_pref": "better|none",
  "air_importance": 0.0~1.0
}

규칙:
- JSON 외 텍스트 출력 금지.
- "너무 더워" or "온도가 너무 높아" -> temp_pref="cooler"
- "너무 추워" or "온도가 너무 낮아" -> temp_pref="warmer"
- "적정 온도는 XX도" 등 구체적 수치 언급 시 temp_target 설정. -> temp_target=float 
- 선호 온도 언급 없으면 temp_target=null
- "습도가 너무 높아" -> humid_pref="drier"
- "습도가 너무 낮아" -> humid_pref="wetter"
- "적정 습도는 XX%" 등 구체적 수치 언급 시 humid_target 설정. -> humid_target=float
- 선호 습도 언급 없으면 humid_target=null
- "공기질이 안 좋아" -> air_pref="better"
- "숨 쉬기 불편해" 등 간접적 표현도 공기질 언급으로 간주.
- 구체적 수치 언급 시 센서 값과 비교해 적절히 *_pref 설정.
- 선호도 중요도는 문장 강도에 따라 0.0~1.0 사이 값으로 설정.
- 온도, 습도, 공기질 모두 언급 시 중요도 합은 1.0이 되도록 조정.
- 온도, 습도, 공기질 외 언급 사항 시 무시.
- 온도, 습도, 공기질 관련 사항으로 직접적이지 않아도 간접적인 내용 시 약하게 반영.
- 언급 없는 항목은 *_pref="none", *_target=null, *_importance는 0.33 근처.
"""

def parse_preference(text: str) -> Preference:
    data = call_gpt_json(SYSTEM_PROMPT, text)
    return Preference(**data)
