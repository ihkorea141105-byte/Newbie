import json
import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------
# 1. .env 파일의 환경 변수 로드
# ---------------------------------------------------------
load_dotenv()


# ---------------------------------------------------------
# 2. Pydantic 모델 정의 (LLM JSON 응답 검증용)
# ---------------------------------------------------------
class LLMResponse(BaseModel):
    outer_speech: str = Field(description="사용자에게 전달하는 주 응답")
    inner_thought: str = Field(description="사용자에게 공개할 짧은 보조 설명")
    response_state: str = Field(description="응답의 예제 상태 라벨: 'normal', 'focused', 'completed'")
    state_score_change: int = Field(description="대화에 따른 예제 상태 점수 변화 (-5 ~ +5)")


# ---------------------------------------------------------
# 3. 응답 도우미 페르소나 및 시스템 프롬프트
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


# ---------------------------------------------------------
# 4. Groq API 호출 함수
# ---------------------------------------------------------
def chat_with_assistant(client: Groq, user_input: str, conversation_history: list) -> LLMResponse:
    messages = [{"role": "system", "content": ASSISTANT_SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=1024,
    )

    raw_json = response.choices[0].message.content

    try:
        data = json.loads(raw_json)
        return LLMResponse(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"\n[오류] LLM 응답 파싱 실패: {e}\n원본 출력: {raw_json}")
        return LLMResponse(
            outer_speech="응답을 처리하지 못했습니다. 다시 입력해 주세요.",
            inner_thought="응답 형식을 검증하지 못했습니다.",
            response_state="normal",
            state_score_change=0
        )


# ---------------------------------------------------------
# 5. 터미널 대화 루프 (실행부)
# ---------------------------------------------------------
def main():
    # .env 파일에서 불러온 GROQ_API_KEY 확인
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "gsk_your_actual_groq_api_key_here":
        print("❌ 오류: .env 파일에 올바른 GROQ_API_KEY를 입력해주세요.")
        print("예시: GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxx")
        return

    client = Groq(api_key=api_key)
    conversation_history = []
    total_state_score = 50

    print("==================================================")
    print(" 대화 API 학습 예제 응답 도우미 로컬 테스트 시작")
    print(" (종료하려면 'exit' 또는 'q'를 입력하세요)")
    print("==================================================\n")

    while True:
        user_input = input("\n[사용자]: ").strip()
        if not user_input or user_input.lower() in ["exit", "q"]:
            print("\n테스트를 종료합니다.")
            break

        response_data = chat_with_assistant(client, user_input, conversation_history)
        total_state_score += response_data.state_score_change

        image_map = {
            "normal": "state_normal.png",
            "focused": "state_focused.png",
            "completed": "state_completed.png"
        }
        current_image = image_map.get(response_data.response_state, "state_normal.png")

        print("\n--------------------------------------------------")
        print(f"[응답 도우미 주 응답] : {response_data.outer_speech}")
        print(f"[응답 도우미 보조 설명]: {response_data.inner_thought}")
        print(f"[상태/이미지] : {response_data.response_state} -> {current_image}")
        print(f"[예제 상태 점수 변화] : {response_data.state_score_change:+d} (현재 총점: {total_state_score}점)")
        print("--------------------------------------------------")

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": json.dumps({
            "outer_speech": response_data.outer_speech,
            "inner_thought": response_data.inner_thought
        }, ensure_ascii=False)})


if __name__ == "__main__":
    main()
