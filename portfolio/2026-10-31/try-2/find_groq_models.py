import os
from dotenv import load_dotenv
from groq import Groq

# 1. .env 파일 로드
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key == "gsk_your_actual_groq_api_key_here":
    print("❌ 오류: .env 파일에 올바른 GROQ_API_KEY를 입력해주세요.")
    exit()

client = Groq(api_key=api_key)

print("==================================================")
print(" 🔍 Groq API 호출 가능한 전체 무료 모델 자동 탐색")
print("==================================================\n")

try:
    # Groq API 서버에서 전체 모델 목록 가져오기
    models_list = client.models.list().data
    
    # active 상태인 모델만 추출
    active_models = [m.id for m in models_list if getattr(m, 'active', True)]
    
    print(f"📌 총 {len(active_models)}개의 활성화된 모델을 찾았습니다.\n")
    print("--------------------------------------------------")
    print(f"{'번호':<5} | {'모델 ID (main.py에 복사해서 쓸 이름)':<35} | {'호출 상태'}")
    print("--------------------------------------------------")

    working_models = []

    # 각 모델별 실제 API 호출 검증 (1토큰 테스트)
    for idx, model_id in enumerate(active_models, 1):
        try:
            # 아주 짧은 테스트 호출 진행
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            print(f"{idx:<5} | {model_id:<35} | 🟢 호출 가능")
            working_models.append(model_id)
        except Exception:
            # 404, 권한 없음, 폐기된 모델 처리
            print(f"{idx:<5} | {model_id:<35} | 🔴 호출 불가 (지원 중단/권한 없음)")

    print("--------------------------------------------------\n")
    print("💡 [추천] 바로 main.py의 model=\"...\" 에 복사해서 사용할 수 있는 최신 모델 ID:")
    for wm in working_models:
        print(f"   👉  model=\"{wm}\"")

except Exception as e:
    print(f"❌ API 접속 및 모델 목록 조회 실패: {e}")
