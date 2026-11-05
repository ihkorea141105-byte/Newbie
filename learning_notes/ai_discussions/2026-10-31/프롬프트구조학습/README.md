# 프롬프트·JSON·상태 매핑 학습 기록

> 당시 AI의 기술 제안과 예시 코드입니다. 실제 구현·측정 성과와 구분합니다.
> 작품 설명은 제외하고 기술 학습 부분을 보존했습니다.

## 배운 설계 개념

- 주 응답과 보조 설명, 상태 변화량을 한 번의 구조화 응답으로 반환하는 설계
- JSON 파싱과 Pydantic 검증, 출력 규칙을 명시하는 프롬프트 설계
- 상태 라벨에 따라 표시용 파일명을 선택하는 분기
- 긴 대화의 요약과 서버 세션 저장을 검토하되 아직 구현 성과로 기록하지 않음
- 프롬프트 변경 전후의 형식 유지와 비용은 동일 조건에서 측정해야 함

## 당시 예시 코드

```python
# prompt_builder.py
import json

ASSISTANT_SYSTEM_PROMPT = """
You are a general-purpose Korean coding practice assistant.
Return only a JSON object containing outer_speech (main answer),
inner_thought (a short public explanation, not private reasoning),
response_state (normal, focused, or completed as example state labels),
and state_score_change (an integer from -5 to 5 for a sample state score).
These field names and state labels are retained to study the existing schema.
Use a neutral coding example without personal context.


"""

```

```python
from fastapi import FastAPI
from pydantic import BaseModel
import openai

class StructuredResponse(BaseModel):
    outer_speech: str
    inner_thought: str
    state_update: dict

@app.post("/chat")
async def chat_with_assistant(user_message: str, user_id: str):
    # LLM 호출 및 JSON 응답 파싱
    raw_response = await call_llm(ASSISTANT_SYSTEM_PROMPT, user_message)
    parsed_data = json.loads(raw_response)
    
    # 예제 상태에 따라 표시용 파일명을 선택
    image_state = "state_normal.png"
    if parsed_data["state_update"]["response_state"] == "focused":
        image_state = "state_focused.png"
    elif parsed_data["state_update"]["response_state"] == "completed":
        image_state = "state_completed.png"
        
    return {
        "speech": parsed_data["outer_speech"],
        "thought": parsed_data["inner_thought"],
        "state_image": image_state,
        "current_score": update_user_score(user_id, parsed_data["state_update"]["state_score_change"])
    }

```
