# 2026-11-05 | JSON 파싱과 응답 모델 검증

## 읽은 코드

`portfolio/2026-11-1/try1/app.py`의 123~134줄을 읽고, JSON 문법 오류와 필수 필드 누락이 각각 어디서 발생하는지 설명했다.

| 입력 예시 | 실패 위치 | 이유 |
|---|---|---|
| `{"outer_speech": "안녕",}` | 124줄 `json.loads(raw_json)` | 마지막 항목 뒤의 쉼표 때문에 `JSONDecodeError` 발생 |
| `{"outer_speech": "안녕"}` | 125줄 `LLMResponse(**parsed_data)` | JSON 파싱은 성공하지만 `inner_thought`, `response_state`, `state_score_change`가 빠져 `ValidationError` 발생 |

두 오류는 모두 127줄의 같은 `except`에서 처리되며, 129~134줄에서 기본 응답을 구성한다.

## 학습 확인

코드와 설명을 참고해 두 예시가 실패하는 줄과 이유를 내 말로 설명했다. 이번에는 코드 읽기로 흐름을 확인했다.
