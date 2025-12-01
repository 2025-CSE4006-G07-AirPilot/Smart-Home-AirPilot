# app/edge_ai/services/edge_suggestion_service.py
from app.edge_ai.schemas.control import State, Preference, Control, Suggestion
from app.edge_ai.models.nlp_client import call_gpt_json
import json

def build_suggestion_template(
    state: State,
    pref: Preference,
    ctrl: Control,
) -> Suggestion:
    reasons = []

    if ctrl.fan_level > state.fan_level:
        reasons.append("실내 공기질이 떨어져 공기청정기 세기를 올렸습니다.")
    elif ctrl.fan_level < state.fan_level:
        reasons.append("공기질이 충분히 좋아 세기를 낮춰 에너지를 아꼈습니다.")

    if ctrl.temp_mode == "COOL":
        reasons.append(f"실내 온도({state.temperature:.1f}℃)가 선호보다 높아 냉풍 {ctrl.temp_level}단을 설정했습니다.")
    elif ctrl.temp_mode == "HEAT":
        reasons.append(f"실내 온도({state.temperature:.1f}℃)가 선호보다 낮아 온풍 {ctrl.temp_level}단을 설정했습니다.")

    if ctrl.humid_mode == "DEHUMID":
        reasons.append(f"습도({state.humidity:.1f}%)가 높아 제습 {ctrl.humid_level}단을 설정했습니다.")
    elif ctrl.humid_mode == "HUMID":
        reasons.append(f"습도({state.humidity:.1f}%)가 낮아 가습 {ctrl.humid_level}단을 설정했습니다.")

    if not reasons:
        reasons.append("현재 온도와 공기질이 선호 범위 안에 있어 설정을 유지했습니다.")

    return Suggestion(
        title="실내 환경에 맞춰 설정을 조정했어요.",
        body=reasons,
    )

SYSTEM_PROMPT = """
너는 공기청정기/에어컨/제습기 설정을 설명하는 한국어 안내문 생성기이다.
입력으로 state, preference, control 정보가 JSON으로 주어진다.
아래 형식의 JSON만 출력하라.

{
  "title": "짧은 한 줄 제목",
  "body": ["문장1", "문장2", ...]
}

스타일:
- 공손하지만 간결하게.
- "-이렇기 때문에 -이런 것 같아요. -이런 건 어떨까요?" 느낌을 내도 괜찮다.
- JSON 외 텍스트는 절대 출력하지 말 것.
"""

def build_suggestion_gpt(
    state: State,
    pref: Preference,
    ctrl: Control,
) -> Suggestion:
    payload = {
        "state": state.model_dump(),
        "preference": pref.model_dump(),
        "control": ctrl.model_dump(),
    }
    data = call_gpt_json(SYSTEM_PROMPT,
                         json.dumps(payload, ensure_ascii=False))
    return Suggestion(**data)
