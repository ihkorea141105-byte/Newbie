# 응답 데이터 검증 개선

## 작업 범위

기존 응답 도우미 대화 API의 응답 모델에 적용할 검증 모듈이다.
전체 API 서버가 아니라 상태와 예제 상태 점수 변화량을 검증하는 코드다.

## 문제

기존 LLMResponse는 상태를 str로 선언하고,
예제 상태 점수 변화 범위를 description에만 작성했다.

따라서 목록에 없는 상태나 범위를 벗어난 정수가
모델 검증을 통과할 수 있었다.

## 수정

- Literal로 상태를 normal, focused, completed로 제한했다.
- ge=-5와 le=5로 변화량의 범위를 제한했다.
- strict=True로 문자열 등의 정수 자동 변환을 제한했다.

## 실행 방법

Python 3.8 이상과 Pydantic 2가 필요하다.
이 폴더에서 실행한다.

```bash
python -m pip install "pydantic>=2,<3"
python response_validation.py
```

정상적으로 실행되면 각 사례의 PASS와
"8/8 검증 통과"가 출력된다.

이 검증에는 Groq 호출이나 API 키가 필요하지 않다.

## 검증 사례

| 상태 | 변화량 | 예상 |
|---|---|---|
| normal | 0 | 허용 |
| normal | -5 | 허용 |
| completed | 5 | 허용 |
| angry | 0 | 거부 |
| normal | 100 | 거부 |
| normal | -6 | 거부 |
| normal | "3" | 거부 |
| normal | True | 거부 |

정수 필드의 strict=True는 불리언 True도 거부한다.

## 기존 API에 적용하는 방법

기존 파일을 보존하려면 다음 순서로 적용한다.

1. portfolio/2026-11-1/try1/app.py를 이 폴더에 복사한다.
2. 복사한 app.py에서 기존 LLMResponse 클래스 정의를 삭제한다.
3. 다음 import를 추가한다.

```python
from response_validation import LLMResponse
```

4. 기존의 JSON 파싱과 LLMResponse 생성 코드는 유지한다.
5. 기존 ValidationError 예외 처리도 유지한다.

모델이 잘못된 상태나 변화량을 반환하면,
검증 실패 후 기존 기본 응답 처리로 이어진다.

이 패키지는 API 실행 환경과 의존성 전체를 제공하지 않는다.
서버 실행에는 기존 FastAPI·Groq 환경 설정이 필요하다.

## 검증 상태

- 제공된 검증 규칙은 AI 작업 환경에서 8개 사례로 확인했다.
- 프로젝트 소유자의 로컬 실행 결과는 아직 기록하지 않았다.
- 실제 Groq 호출과 API 전체 연동은 이번 검증 범위에 포함하지 않았다.

직접 실행한 뒤 실행 날짜, Python·Pydantic 버전,
출력 결과를 여기에 추가한다.

## 남은 한계

- 제한 대상은 한 번의 예제 상태 점수 변화량이다.
- 누적 예제 상태 점수의 허용 범위는 별도로 정하고 검증해야 한다.
- 기존 API는 클라이언트가 보내는 점수와 대화 이력에 의존한다.
- DB 저장과 서버 세션은 이번 작업에서 구현하지 않았다.
- 응답의 적절성과 응답 규칙의 일관성은 별도 평가가 필요하다.
