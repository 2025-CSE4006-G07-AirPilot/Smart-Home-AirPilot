# app/edge_ai/services/speech_service.py

from typing import Any
import os
import tempfile

from fastapi import UploadFile
from transformers import pipeline
import soundfile as sf
import numpy as np


# 한국어 STT 파이프라인 (애플리케이션 시작 시 1번만 로드)
_asr = pipeline(
    task="automatic-speech-recognition",
    model="SungBeom/whisper-small-ko",  # 필요 시 다른 모델명으로 교체 가능
    device="cpu",  # GPU 있으면 0으로
)


def transcribe_korean(upload_file: UploadFile) -> str:
    """
    업로드된 음성 파일을 받아서 한국어 텍스트로 변환.
    - 임시 파일에 저장
    - soundfile로 직접 디코딩 (ffmpeg 사용 안 함)
    - Whisper 파이프라인에는 numpy array + sampling_rate를 넘긴다.
    """
    # 1) 파일 전체를 메모리로 읽기
    data = upload_file.file.read()

    # 2) 임시 파일 생성
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        # fd를 파일 객체로 열어서 바이트 쓰기
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(data)

        # 3) ffmpeg 대신 soundfile로 직접 로드
        audio, sr = sf.read(path)  # audio: np.ndarray, sr: int

        # 스테레오면 모노로 다운믹스
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)

        # 4) Whisper 파이프라인에 array + sampling_rate 형태로 전달
        asr_input = {
            "array": audio.astype(np.float32),
            "sampling_rate": sr,
        }

        result: Any = _asr(asr_input)

    finally:
        # 5) 임시 파일 삭제 (실패하면 무시)
        try:
            os.remove(path)
        except OSError:
            pass

    # 6) 결과 텍스트 추출
    text = result.get("text", "").strip()
    return text
