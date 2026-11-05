> **학습용 AI 대화·제안 기록 — 제출용 성과 자료가 아닙니다.**
> 아래 내용에는 당시 AI가 제안한 예시 코드·이력서 문구·향후 계획이 포함되어 있습니다.
> 현재 app.py는 동기 Groq 호출과 일반 JSON 응답을 사용합니다. 비동기 LLM 호출, SSE, DB·Redis, 대화 요약, React UI, 배포 및 성능 개선은 이 코드에서 구현·검증된 성과가 아닙니다.
> 수치 예시는 실측 결과가 아니며 이력서 성과로 사용하지 않습니다. 최신 구현 상태는 최상위 README를 기준으로 확인하세요.

나:AI프롬프트와 대화기억 로직부터 만들자

제미나이:프롬프트 설계와 대화 기억(Context Window) 처리 로직을 가장 먼저 다루는 것은 **면접관에게 '코드를 조립만 한 개발자'가 아닌 'LLM의 한계와 비용, 유저 경험을 다룰 줄 아는 엔지니어'임을 증명하는 최고의 전략**입니다.

바이브 코딩으로 만든 프로젝트는 대부분 LLM API에 단순 대화 배열(`messages`)을 계속 누적해서 보내다가 **토큰 초과 오류**가 나거나, **대화가 길어지면 응답 도우미가 이전 일을 까먹고 말투가 깨지는 문제**를 해결하지 못합니다.

이 문제를 직접 고민하고 코드로 해결한 과정을 포트폴리오의 메인으로 삼을 수 있도록 **프롬프트 구조 설계**부터 **대화 기억 로직 구현**, 그리고 **포트폴리오 서술법**까지 단계별로 정리했습니다.

---

## 1. 프롬프트 구조 설계 (페르소나 + 상태값 유지)

LLM 대화 API에서 시스템 프롬프트는 단순 지시문이 아니라 **응답 규칙, 시스템 설정, 현재 상태를 제어하는 규칙집** 역할을 해야 합니다.

### 프롬프트 구성 4요소

1. **Persona (역할 정의)**: 이름, 말투, 톤앤매너, 금지 행동
2. **Worldview & State (시스템 설정 및 현재 상태)**: 유저와의 예제 상태 점수, 현재 위치, 퀘스트 진행 상황
3. **Response Format (응답 형식)**: 대사 + 행동 묘사 + 상태 변화(JSON 형태 파싱)
4. **Constraints (제약 조건)**: AI임을 밝히지 말 것, 억지로 가르치려 들지 말 것 등

```python
# prompt_templates.py

SYSTEM_PROMPT_TEMPLATE = """
You are a general assistant configured as '{character_name}' in a structured response exercise.

[Persona & Tone]
- Personality: {personality}
- Speech Style: {speech_style}
- Follow the configured response format and do not invent personal details.

[Current Game State]
- Current Location: {location}
- User Relationship Score: {relationship_score}/100
- Active Quest: {current_quest}

[Rules for Output]
1. Write response in Korean.
2. Include internal monologue or actions inside brackets, e.g., (머뭇거리며 손을 떨며)
3. If the user's action affects the Relationship Score or Quest, output a hidden JSON state tag at the end.
"""

```

---

## 2. 대화 기억(Memory) 관리 로직 3단계

대화를 그대로 다 보내면 토큰 비용이 폭발하고 속도가 느려집니다. 반대로 너무 많이 자르면 대화 기억을 잃어버립니다. 이를 해결하기 위해 **슬라이딩 윈도우 + 요약(Summarizer) 혼합 구조**를 설계합니다.

```
[전체 대화 이력] 
  │
  ├── 1~10번째 대화 (오래된 대화)  ──► LLM 요약 ──► "핵심 기억 텍스트"로 압축 (System Prompt에 포함)
  │
  └── 11~15번째 대화 (최근 대화)  ──► 원본 그대로 유지 ──► OpenAI messages 배열에 전달

```

### Python 백엔드 구현 (FastAPI / OpenAI SDK)

```python
import openai
from pydantic import BaseModel
from typing import List, Dict

class MemoryManager:
    def __init__(self, max_recent_turns: int = 5):
        self.max_recent_turns = max_recent_turns  # 최근 유지할 대화 쌍 수

    async def summarize_old_history(self, old_messages: List[Dict[str, str]], current_summary: str) -> str:
        """오래된 대화 내용을 LLM을 통해 한두 문장으로 요약 축적"""
        prompt = f"""
        기존 요약: {current_summary}
        추가된 대화 내용: {old_messages}
        
        위 추가된 대화를 바탕으로, 응답 도우미가 앞으로 꼭 기억해야 할 중요한 사건/정보만 2-3문장으로 업데이트해서 요약하세요.
        """
        response = await openai.AsyncOpenAI().chat.completions.create(
            model="gpt-4o-mini", # 요약용은 가볍고 빠른 모델 사용 (비용 절감)
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content

    def build_final_messages(self, system_prompt: str, summary: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """최종 LLM에 전달할 메시지 구조 조립"""
        final_messages = []
        
        # 1. 기본 시스템 프롬프트 + 누적된 장기 기억(요약본)
        full_system_prompt = system_prompt
        if summary:
            full_system_prompt += f"\n\n[이전 대화 기억 요약]\n{summary}"
            
        final_messages.append({"role": "system", "content": full_system_prompt})
        
        # 2. 최근 대화 N개만 단기 기억으로 첨부
        recent_history = history[-(self.max_recent_turns * 2):]
        final_messages.extend(recent_history)
        
        return final_messages

```

---

## 3. 포트폴리오 및 GitHub README 서술 전략

이 로직을 완성한 후 GitHub README 및 포트폴리오에 작성할 때는 "무엇을 만들었다"가 아니라 "어떤 고민을 거쳐 이 구조를 선택했는가"를 보여주어야 합니다.

### 포트폴리오에 포함할 '성장/고민 과정' 서술 구조

#### 1. 문제 제기 (Why)

* *기존 문제*: 유저와 20턴 이상 대화 진행 시 컨텍스트 길이 증가로 인한 API 비용 상승 및 처리 속도 저하(Latency 증가), 대화 한계 초과 에러 발생.

#### 2. 기술적 대안 비교 (Trade-off 분석)

* **방안 A (단순 자르기)**: 최근 5개 대화만 유지.
* *결과*: 속도는 빠르나 10분 전 유저가 말한 설정(예: "내 이름은 민수야")을 잊어버리는 치명적 UX 저하.


* **방안 B (전체 대화 유지)**: 토큰 수가 수천 개로 비대해져 응답 시간이 5초 이상으로 지연되고 비용 급증.
* **최종 선택 (방안 C: Hybrid Memory Strategy)**:
* 오래된 대화는 `gpt-4o-mini`를 통해 백그라운드에서 실시간 요약(Summary Buffer) 생성.
* 최근 5턴 대화만 Raw Data로 유지하여 최근 맥락과 세부 어조를 동시에 유지.


#### 3. 엔지니어링 성과 (Result)

* **토큰 소비량**: 단순 누적 대비 절감률 측정 예정 (기존 65%는 미측정 설명용 예시).
* **응답 시간(Latency)**: 변경 전후 응답 시간 측정 예정 (기존 3.2초 → 1.4초는 미측정 설명용 예시).
* **기억 유지율**: 대화 50턴 이상 진행 후에도 핵심 사용자 정보 및 게임 퀘스트 상태 유지 확인.

---

## 4. 바로 시작할 수 있는 다음 구현 단계

1. **Python 스크립트 작성**: 위 `MemoryManager` 클래스를 작성하고 파이썬 터미널에서 대화를 10~20번 입력하며 요약이 잘 갱신되는지 콘솔 로그 출력으로 검증.
2. **FastAPI 엔드포인트 연동**: 대화 기록을 `PostgreSQL` 또는 `Redis`에 저장/조회하는 백엔드 API 제작.
3. **SSE(Server-Sent Events) 적용**: LLM 응답이 한 글자씩 출력되도록 스트리밍 응답 로직 추가.

이 파이썬 메모리 관리 로직 코드를 먼저 다듬어보면서, 파이썬 백엔드 API 형태로 만드는 것부터 진행해 보시는 것을 추천합니다.
