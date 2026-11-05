import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------
# 1. 환경 변수 로드 및 Groq 클라이언트 초기화
# ---------------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "gsk_your_actual_api_key_here":
    raise RuntimeError("❌ .env 파일에 올바른 GROQ_API_KEY를 설정해주세요.")

groq_client = Groq(api_key=GROQ_API_KEY)

# FastAPI 앱 생성
app = FastAPI(
    title="대화 API 학습 예제 AI Backend API",
    description="Groq LLM 기반 프롬프트 파싱 및 대화 백엔드 API",
    version="1.0.0"
)

# ---------------------------------------------------------
# 2. CORS 설정 (프론트엔드 통신 허용)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 전체 허용 (추후 웹 URL로 제한 가능)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 3. Pydantic 요청 및 응답 데이터 모델 정의
# ---------------------------------------------------------
class LLMResponse(BaseModel):
    outer_speech: str = Field(description="사용자에게 전달하는 주 응답")
    inner_thought: str = Field(description="사용자에게 공개할 짧은 보조 설명")
    response_state: str = Field(description="응답의 예제 상태 라벨: 'normal', 'focused', 'completed'")
    state_score_change: int = Field(description="대화에 따른 예제 상태 점수 변화 (-5 ~ +5)")

class ChatRequest(BaseModel):
    user_input: str = Field(..., example="안녕! 오늘 개발 잘돼가?")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="이전 대화 기록")
    total_state_score: int = Field(default=50, description="현재 총 예제 상태 점수 점수")

class ChatResponse(BaseModel):
    outer_speech: str
    inner_thought: str
    response_state: str
    current_image: str
    state_score_change: int
    total_state_score: int
    updated_history: List[Dict[str, Any]]

# ---------------------------------------------------------
# 4. 응답 도우미 프롬프트 및 상태 이미지 매핑
# ---------------------------------------------------------
ASSISTANT_SYSTEM_PROMPT = """
You are a general-purpose Korean coding practice assistant.
Return only a JSON object containing outer_speech (main answer),
inner_thought (a short public explanation, not private reasoning),
response_state (normal, focused, or completed as example state labels),
and state_score_change (an integer from -5 to 5 for a sample state score).
These field names and state labels are retained to study the existing schema.
Use a neutral coding example without personal context.


"""

IMAGE_MAP = {
    "normal": "state_normal.png",
    "focused": "state_focused.png",
    "completed": "state_completed.png"
}

# ---------------------------------------------------------
# 5. API 엔드포인트 구현
# ---------------------------------------------------------
@app.get("/")
def read_root():
    """서버 상태 확인용 헬스체크 API"""
    return {"status": "ok", "message": "대화 API 학습 예제 API Server Running"}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    유저 입력과 대화 기록을 받아 응답 도우미의 주 응답, 보조 설명, 상태 이미지, 업데이트된 대화 기록을 반환합니다.
    """
    messages = [{"role": "system", "content": ASSISTANT_SYSTEM_PROMPT}]
    messages.extend(request.conversation_history)
    messages.append({"role": "user", "content": request.user_input})

    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1024,
        )

        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)
        response_data = LLMResponse(**parsed_data)

    except (json.JSONDecodeError, ValidationError) as e:
        # LLM 파싱 예외 처리 (폴백 처리)
        response_data = LLMResponse(
            outer_speech="응답을 처리하지 못했습니다. 다시 입력해 주세요.",
            inner_thought="응답 형식을 검증하지 못했습니다.",
            response_state="normal",
            state_score_change=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Groq API 호출 중 오류 발생: {str(e)}"
        )

    # 점수 업데이트 및 이미지 결정
    new_total_score = request.total_state_score + response_data.state_score_change
    current_image = IMAGE_MAP.get(response_data.response_state, "state_normal.png")

    # 업데이트된 대화 기록 구성
    updated_history = list(request.conversation_history)
    updated_history.append({"role": "user", "content": request.user_input})
    updated_history.append({
        "role": "assistant",
        "content": json.dumps({
            "outer_speech": response_data.outer_speech,
            "inner_thought": response_data.inner_thought
        }, ensure_ascii=False)
    })

    return ChatResponse(
        outer_speech=response_data.outer_speech,
        inner_thought=response_data.inner_thought,
        response_state=response_data.response_state,
        current_image=current_image,
        state_score_change=response_data.state_score_change,
        total_state_score=new_total_score,
        updated_history=updated_history
    )
