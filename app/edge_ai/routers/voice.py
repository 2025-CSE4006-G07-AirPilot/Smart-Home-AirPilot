# app/edge_ai/routers/voice.py

from fastapi import APIRouter, UploadFile, File

from app.edge_ai.schemas.control import Preference, VoicePreferenceResponse
from app.edge_ai.services.speech_service import transcribe_korean
from app.edge_ai.services.edge_nlp_service import parse_preference


router = APIRouter(
    prefix="/edge-ai/voice",
    tags=["edge-ai-voice"],
)


# @router.post("/preference", response_model=Preference)
# def voice_preference(file: UploadFile = File(...)) -> Preference:
#     """
#     음성 파일을 받아서:
#     1) 한국어 STT로 텍스트 변환
#     2) 텍스트를 parse_preference()에 넘겨서 선호도 JSON 생성
#     """
#     text = transcribe_korean(file)
#     pref = parse_preference(text)
#     return pref

@router.post("/preference", response_model=VoicePreferenceResponse)
def voice_preference(file: UploadFile = File(...)) -> VoicePreferenceResponse:
    # 1) 음성 → 텍스트
    text = transcribe_korean(file)

    # 2) 텍스트 → 선호도 파싱
    pref: Preference = parse_preference(text)

    # 3) 둘 다 한 번에 리턴
    return VoicePreferenceResponse(
        recognized_text=text,
        preference=pref,
    )