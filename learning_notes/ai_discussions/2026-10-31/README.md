> **학습용 AI 대화·제안 기록 — 제출용 성과 자료가 아닙니다.**
> 아래 내용에는 당시 AI가 제안한 예시 코드·이력서 문구·향후 계획이 포함되어 있습니다.
> 현재 app.py는 동기 Groq 호출과 일반 JSON 응답을 사용합니다. 비동기 LLM 호출, SSE, DB·Redis, 대화 요약, React UI, 배포 및 성능 개선은 이 코드에서 구현·검증된 성과가 아닙니다.
> 수치 예시는 실측 결과가 아니며 이력서 성과로 사용하지 않습니다. 최신 구현 상태는 최상위 README를 기준으로 확인하세요.

# 나:요약 내용 적어줘!
# 제미나이의 답변
지금까지 정립한 **기술 학습 방향, 대표 프로젝트 기획, 기술 아키텍처 및 1단계 구현 내역 요약**입니다.

---

### 1. 기술 학습 방향 및 포트폴리오 방향

* **학습 분야 예시**: LLM 모델 직접 학습보다는 LLM API 연동, 응답 도우미 페르소나 제어, 세션 기억, 사용자 화면(UI)을 구현하는 **AI 서비스·풀스택 개발자**.
* **포트폴리오 구성**: 완성도 높은 대표 프로젝트 1개(LLM 대화 API)와 보조 프로젝트 1개로 구성해 잡코리아 및 GitHub 등록.

### 2. 메인 프로젝트 기획: 대화 API 학습 예제


* **시각적 UX 연동**: 상태 라벨(`response_state`) 파싱에 따른 동적 이미지 매핑 (`normal` $\rightarrow$ `state_normal.png`, `focused` $\rightarrow$ `state_focused.png`, `completed` $\rightarrow$ `state_completed.png`).


### 3. 핵심 기술 아키텍처 (엔지니어링 어필 포인트)

* **이중 구조 파싱(Dual-Layer Parsing)**: 1회 API 호출로 주 응답(`outer_speech`), 보조 설명(`inner_thought`), 상태 라벨(`response_state`), 예제 상태 점수 변화(`state_score_change`)를 JSON 형태로 동시 추출 및 Pydantic 검증.
* **대화 기억(Context Window) 관리**: 최근 대화는 슬라이딩 윈도우로 유지하고, 오래된 대화는 비동기 요약(Summarizer)을 적용해 토큰 비용 절감 및 대화 기억 유지.
* **보안 강화**: 클라이언트 단 API 키 노출 방지를 위해 파이썬 백엔드 경유 구조 설계 및 `.env` 파일 관리.

### 4. 1단계 로컬 테스트 세팅 현황

* **`requirements.txt`**: `groq`, `pydantic`, `python-dotenv` 패키지 구성.
* **`.env` / `.gitignore**`: API 키 분리 및 Git 버전 관리 보안 적용.
* **`main.py`**: Groq API(`llama-3.3-70b-versatile` 모델) 연동 및 JSON 모드 기반 터미널 대화 테스트 환경 구축 완료.
