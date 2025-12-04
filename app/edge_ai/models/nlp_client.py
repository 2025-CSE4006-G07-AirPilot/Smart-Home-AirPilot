# app/edge_ai/models/nlp_client.py

from typing import Dict, Any
import json
import re

from openai import OpenAI
from app.edge_ai.core.config import settings


# OpenAI 클라이언트 (새 SDK 방식)
_client = OpenAI(api_key=settings.EDGE_OPENAI_API_KEY)


def _clean_json_text(text: str) -> str:
    """
    GPT가 ```json ... ``` 코드블록 형태로 답을 줄 때를 대비해서
    앞뒤의 코드블록 마커를 제거하고 순수 JSON 문자열만 남긴다.
    """
    text = text.strip()

    # ```json ... ``` 혹은 ``` ... ``` 패턴 제거
    if text.startswith("```"):
        text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.DOTALL).strip()

    return text


def call_gpt_json(system_prompt: str, user_content: str) -> Dict[str, Any]:
    """
    system_prompt: 역할/규칙 설명
    user_content : 사용자 입력(문자열)

    반환값: GPT가 만들어 준 JSON을 dict로 파싱한 객체
    """
    resp = _client.chat.completions.create(
        model=settings.EDGE_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )

    content = resp.choices[0].message.content or ""
    content = _clean_json_text(content)

    return json.loads(content)
