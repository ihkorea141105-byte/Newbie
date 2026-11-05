# 기술 분석 보고서 — chatbot-training

## 1. 분석 범위와 신뢰 수준

분석 대상은 2026-11-04에 제공된 `chatbot-training.zip`이다. 압축 해제 후 Markdown/TXT/Python 파일, 두 개의 DOCX에서 추출한 텍스트, PNG 파일 목록과 메타데이터를 확인했다.

실행 확인:
- `portfolio/2026-11-3/response_validation.py`: 이 분석 실행 환경에서 8/8 사례 PASS.
- Python 파일 7개 문법 검사: 6개 통과, 오래된 `portfolio/2026-10-31/try-1/main.py` 1개 실패.
- `app.py`는 API 키가 설정되어 있지 않아 서버 import/실제 Groq API 호출/엔드포인트 통합 테스트를 하지 않았다.
- 위 결과는 사용자의 로컬 PC에서 실행한 결과가 아니다.

## 2. 좋은 점

- API 키를 환경 변수로 분리하려는 방향이 있고 `.env.example`이 포함되어 있다.
- 터미널 실험에서 FastAPI REST API로 옮기는 학습 단계가 기록되어 있다.
- LLM 출력 JSON 파싱과 Pydantic 검증을 구분하고 폴백 응답을 설계했다.
- 응답 도우미 대사를 `outer_speech`와 `inner_thought`로 분리해 UX에서 서로 다른 표시를 할 수 있다.
- 상태 라벨로 이미지 상태를 연결하는 데이터 흐름이 존재한다.
- AI의 제안과 실제 구현을 구분하려는 README/성장 기록의 원칙이 좋다.

## 3. 프롬프트와 응답 계약

공개본의 프롬프트는 일반적인 코딩 학습 응답 예제로 바꿨습니다. 기존 응답 필드와 JSON 계약은 보존했습니다.

## 4. 메인 FastAPI 코드 검토

대상: `portfolio/2026-11-1/try1/app.py`

### 현재 처리 흐름

1. `load_dotenv()`로 환경 변수를 읽는다.
2. 모듈 import 시 `GROQ_API_KEY`를 읽고 Groq 클라이언트를 만든다.
3. `ChatRequest`에서 사용자 입력, 과거 대화 이력, 총 예제 상태 점수 점수를 받는다.
4. 시스템 프롬프트 + 과거 대화 + 현재 사용자 입력을 `messages`로 조립한다.
5. Groq 동기 호출 후 `json.loads`와 `LLMResponse(**parsed_data)`를 수행한다.
6. 파싱/검증 실패 때 기본 대사를 만들고, 다른 예외는 HTTP 500으로 올린다.
7. 예제 상태 점수 점수를 합산하고 상태에 대응하는 PNG 파일명을 고른다.
8. 사용자/assistant 대화를 `updated_history`로 만들어 반환한다.

### 우선순위가 높은 개선

**P0 — 응답 검증 모듈 연결**
- 현재 `app.py` 안의 `LLMResponse`는 `response_state: str`, `state_score_change: int`이다. 설명에 범위를 써 둔 것은 실제 제약이 아니다.
- 11월 3일 `response_validation.py`에는 `Literal["normal", "focused", "completed"]`, `ge=-5`, `le=5`, `strict=True`가 있다.
- 중복 클래스를 삭제하고 `from response_validation import LLMResponse`를 연결해야 한다.
- 폴백 응답도 새 검증 모델을 통과해야 한다.

**P0 — 회귀 테스트**
- 정상 입력과 경계값 -5/+5 허용.
- 허용하지 않은 상태, -6/+6, 문자열 `"3"`, `True`, 필드 누락 거부.
- 잘못된 JSON에서 폴백 응답을 반환하는지 확인.
- 실제 Groq 호출 대신 가짜 응답(mock)을 주입해 검증 실패 경로를 재현한다.
- 독립 검증 스크립트 통과와 FastAPI 통합 통과를 별도 기록한다.

**P1 — 점수 정책**
- `state_score_change`의 한 번 변화량 -5~+5 제한과 `total_state_score` 누적값의 0~100 제한은 다른 규칙이다.
- 요청 점수에 0~100 검증을 추가하고, 점수를 서버가 관리하도록 바꾸는 것이 안전하다.
- 누적 결과가 0 미만/100 초과일 때 거부할지, 경계값으로 보정(clamp)할지 정책을 정하고 테스트한다.
- 클라이언트가 매 요청마다 임의의 점수를 전송하면 점수 조작이 가능하다.

**P1 — 대화 이력 스키마**
- `List[Dict[str, Any]]`는 임의의 role/content 형태를 허용한다.
- `role`을 `user`와 `assistant` 등 필요한 값으로 제한하고, `content`를 문자열로 검증한다.
- 최대 메시지 수와 최대 입력 길이를 정한다.
- 클라이언트가 보낸 대화 이력을 그대로 신뢰하지 말고, 향후 서버 세션/DB에서 대화를 관리한다.

**P1 — 보안·운영**
- CORS의 `allow_origins=["*"]`는 개발용으로만 둔다. 배포 시 실제 프론트엔드 도메인으로 제한한다.
- 쿠키 인증이 필요하지 않다면 `allow_credentials=True`를 켜둘 이유가 없다.
- `except Exception`에서 `str(e)`를 그대로 클라이언트에 반환하지 말고, 서버 로그에는 추적 정보를 남기되 API 응답은 일반화한다.
- `.env`를 Git에서 제외하는 `.gitignore`가 ZIP에 없다. 루트에 `.env`, `.venv/`, `__pycache__/`, `*.py[cod]` 등을 제외한다.
- API 호출량/사용자별 비용을 통제하려면 인증·rate limit·타임아웃을 추가한다.

**P2 — 구조와 UI 연결**
- `ChatResponse`에서도 `response_state`를 Literal로 제한한다.
- `current_image`는 파일명뿐 아니라 프론트엔드가 접근 가능한 URL 또는 고정 asset key로 반환해야 한다.
- 상태별 파일명 선택 구조를 학습 예제로 보존했습니다. 실제 이미지 파일은 포함하지 않습니다.
- LLM 동기 호출은 요청 처리 스레드를 점유한다. 먼저 기능/오류/비용을 측정하고, 필요할 때 비동기 클라이언트로 바꾸며 기존과 동일 조건으로 비교한다.

## 5. 저장·기억 설계 검토

현재 대화 이력과 점수는 클라이언트가 다음 요청에 다시 보내는 구조다. 이 방식은 프로토타입에는 단순하지만, 서버 영구 저장이나 장기 기억이라고 부를 수 없다.

권장 순서:
1. 최근 대화 N개만 유지하는 단기 컨텍스트 컷을 구현한다.
2. 대화 요약은 사실/사용자 선호/사건/미해결 약속을 분리하는 구조화된 형태로 저장한다.
3. 먼저 SQLite로 사용자/세션/메시지/상태 저장을 학습하고, 배포나 동시 사용자 요구가 생기면 PostgreSQL을 검토한다.
4. Redis는 캐시·세션·실시간 동시성 요구가 확인된 후 도입한다. 초기부터 필수로 추가하지 않는다.
5. 요약 호출 자체의 토큰과 지연도 전체 비용 계산에 포함한다. 요약이 항상 비용을 줄인다고 단정하지 않는다.

## 6. 독립 상태값 설계 학습

여러 상태값은 독립적인 범위와 자료형으로 정의하고 서버에서 검증합니다.
LLM은 변화량을 제안하고 서버가 규칙을 확인한 뒤 반영하도록 설계합니다.
확인된 사실, 추측, 미해결 항목을 메모리에서 구분합니다.
사용자가 말하지 않은 행동이나 정보를 사실처럼 기록하지 않습니다.

## 7. 파일 품질 및 정리

- 총 ZIP 항목: 105개(폴더 항목 포함), PNG 45개.
- Python 파일: 7개. 문법 검사 6개 통과, 오래된 `try-1/main.py`는 `[cite: 1]` 등의 잔여 문자열 때문에 SyntaxError.
- `try-2/main.py`와 `try-3/main.py`는 코드 구조가 거의 같고 모델 호출의 `temperature`/`max_tokens` 값만 다르다.
- `response_validation.py`는 `if __name__ == "__main__"`에서 직접 사례를 실행하는 형태다. 실행 확인에는 유용하지만 `pytest` 테스트 함수로 자동 수집되는 구조는 아니다.
- FastAPI 앱 폴더(`portfolio/2026-11-1/try1/`)에는 전용 `requirements.txt`가 없다. 초기 터미널 실험 폴더에만 requirements가 있다.
- ZIP에서 실제 API 키 패턴은 발견하지 못했고, `.env.example`에는 자리표시자 문자열만 있다. 그래도 실제 저장소에서는 키 유출 여부를 별도로 점검한다.
- `portfolio/2026-11-4/README.md`는 계획서다. 해당 폴더에 `app.py`와 `response_validation.py`가 실제 생성된 것으로 오인하지 않는다.

## 8. 검증 결과 상세

| 검사 | 결과 | 해석 |
|---|---|---|
| `response_validation.py` | 8/8 PASS | 이 분석 환경에서 독립 규칙 실행 성공 |
| Python 문법 검사 | 6/7 PASS | 구형 `try-1/main.py`만 SyntaxError |
| FastAPI 서버 import | 미실행 | API 키/서버 환경 미설정 |
| Groq 실 API 요청 | 미실행 | 외부 호출 검증 아님 |
| FastAPI 폴백 경로 | 미실행 | Mock 테스트 작성 필요 |
| 브라우저/UI/이미지 URL | 미실행 | 프론트엔드 미구현 |

