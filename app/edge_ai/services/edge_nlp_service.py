# app/edge_ai/services/edge_nlp_service.py

from typing import Optional
import re

from app.edge_ai.models.nlp_client import call_gpt_json
from app.edge_ai.schemas.control import Preference
from openai import OpenAIError, RateLimitError

SYSTEM_PROMPT = """
너는 공기청정기/에어컨/제습기 제어를 위한 '선호도 파서'이다.
사용자의 한국어 문장을 아래 JSON 스키마에 맞게만 변환해라.

{
  "temp_pref": "warmer|cooler|set|none",
  "temp_target": float | null,
  "temp_importance": 0.0~1.0,

  "humid_pref": "more|less|set|none",
  "humid_target": float | null,
  "humid_importance": 0.0~1.0,

  "air_pref": "better|none",
  "air_importance": 0.0~1.0
}

규칙:
- JSON 외 텍스트 출력 금지.
- "너무 더워", "온도가 너무 높아" → temp_pref="cooler"
- "너무 추워", "온도가 너무 낮아" → temp_pref="warmer"
- "적정 온도는 XX도", "XX도로 맞춰줘" → temp_pref="set", temp_target=XX
- 온도 언급 없으면 temp_pref="none", temp_target=null
- "습도가 너무 높아", "습해", "눅눅해", "습기가 많아" → humid_pref="less"
- "습도가 너무 낮아", "건조해", "딩딩 마른 느낌", "촉촉했으면" → humid_pref="more"
- "적정 습도는 XX%" 등 → humid_pref="set", humid_target=XX
- 습도 언급 없으면 humid_pref="none", humid_target=null
- "공기질이 안 좋아", "숨 쉬기 불편해", "먼지 많아", "냄새나" → air_pref="better"
- 온도/습도/공기질 관련 언급 없으면 해당 importance는 0.0에 가깝게.
- 온도·습도·공기질 모두 언급 시 중요도 합이 1.0 근처가 되도록 조정.
- 간접 언급(예: "머리가 띵해", "답답해")은 약하게 반영.
"""

def _rule_based_preference(text: str) -> Preference:
    """
    GPT 없이도 한국어 표현만으로 어느 정도 쓸만한 선호를 만드는 룰 기반 파서.
    - 대장님 말투 기준으로 '너무 더워', '약간 시원하게', '살짝만' 같은 표현 대응
    - 마지막에 importance를 0~1 범위로 대략 정규화
    """
    t = text.replace(" ", "")
    pref = Preference()  # 기본: none / none / better + 0.33/0.33/0.34

    # --- 강도(수식어) 분석 ---
    strong_markers = ["너무", "완전", "진짜", "정말", "엄청", "개", "졸", "겁나"]
    mild_markers = ["조금", "살짝", "약간", "좀", "살짝만", "조금만", "약간만"]

    strong = any(m in t for m in strong_markers)
    mild = any(m in t for m in mild_markers)

    # 기본 가중치 (나중에 정규화)
    base_strong = 0.8
    base_normal = 0.6
    base_mild = 0.4

    # --- 온도 관련 ---
    is_hot = any(k in t for k in ["더워", "덥", "뜨거워", "후끈", "푹푹"])
    is_cold = any(k in t for k in ["추워", "춥", "차가워", "쌀쌀해", "싸늘해"])

    if is_hot:
        pref.temp_pref = "cooler"
        if strong:
            pref.temp_importance = base_strong
        elif mild:
            pref.temp_importance = base_mild
        else:
            pref.temp_importance = base_normal

    if is_cold:
        pref.temp_pref = "warmer"
        if strong:
            pref.temp_importance = base_strong
        elif mild:
            pref.temp_importance = base_mild
        else:
            pref.temp_importance = base_normal

    # "25도", "23도로", "22도로 맞춰" 등
    m_deg = re.search(r'(\d+)\s*도', text)
    if m_deg:
        target = float(m_deg.group(1))
        pref.temp_pref = "set"
        pref.temp_target = target
        pref.temp_importance = max(pref.temp_importance, base_normal if not strong else base_strong)

    # --- 습도 관련 ---
    is_dry = any(k in t for k in ["건조", "건조해", "입이바싹", "목마른", "촉촉했으면"])
    is_humid = any(k in t for k in ["습해", "눅눅", "습도높", "찝찝", "끈적"])

    if is_dry:
        pref.humid_pref = "more"
        if strong:
            pref.humid_importance = base_strong
        elif mild:
            pref.humid_importance = base_mild
        else:
            pref.humid_importance = base_normal

    if is_humid:
        pref.humid_pref = "less"
        if strong:
            pref.humid_importance = base_strong
        elif mild:
            pref.humid_importance = base_mild
        else:
            pref.humid_importance = base_normal

    # "50%" 같은 패턴 (습도)
    m_humid = re.search(r'(\d+)\s*%|\s*퍼센트', text)
    if m_humid and m_humid.group(1):
        target_h = float(m_humid.group(1))
        pref.humid_pref = "set"
        pref.humid_target = target_h
        pref.humid_importance = max(pref.humid_importance, base_normal if not strong else base_strong)

    # --- 공기질 관련 ---
    is_bad_air = any(
        k in t
        for k in [
            "공기질", "공기안좋", "공기가안좋", "숨막혀", "숨막힐",
            "숨쉬기불편", "먼지많", "먼지 많", "미세먼지", "냄새나", "악취", "답답"
        ]
    )

    if is_bad_air:
        pref.air_pref = "better"
        if strong:
            pref.air_importance = base_strong
        elif mild:
            pref.air_importance = base_mild
        else:
            pref.air_importance = base_normal

    # --- 중요도 정규화 (합이 1 근처가 되게) ---
    # 변화가 있었는지 기준으로 잡기
    flags = {
        "temp": pref.temp_pref != "none" or pref.temp_target is not None,
        "humid": pref.humid_pref != "none" or pref.humid_target is not None,
        "air": pref.air_pref != "none" and pref.air_pref != "",
    }

    temps = pref.temp_importance
    hums = pref.humid_importance
    airs = pref.air_importance

    # 어느 항목이라도 변경되었으면 그 항목들 기준으로 합을 1에 맞춤
    if any(flags.values()):
        # 언급 안 된 항목 importance 는 0으로
        if not flags["temp"]:
            temps = 0.0
        if not flags["humid"]:
            hums = 0.0
        if not flags["air"]:
            airs = 0.0

        s = temps + hums + airs
        if s > 0:
            temps /= s
            hums /= s
            airs /= s

        pref.temp_importance = temps
        pref.humid_importance = hums
        pref.air_importance = airs

    return pref

# def parse_preference(text: str) -> Preference:
#     data = call_gpt_json(SYSTEM_PROMPT, text)
#     return Preference(**data)

def parse_preference(text: str) -> Preference:
    """
    1) GPT로 정교하게 파싱 시도
    2) RateLimit / 기타 에러 나면 룰 기반 결과 반환
    """
    # 우선 룰 기반으로 기본값 한 번 만들어 두고
    base = _rule_based_preference(text)

    try:
        data = call_gpt_json(SYSTEM_PROMPT, text)
        return Preference(**data)
    except RateLimitError:
        # 쿼터 초과 → GPT 파트는 잠시 포기하고 룰 기반으로만 동작
        return base
    except OpenAIError:
        # 기타 OpenAI 관련 에러 → 마찬가지로 룰 기반
        return base
    except Exception:
        # JSON 파싱 실패 등 → 룰 기반
        return base