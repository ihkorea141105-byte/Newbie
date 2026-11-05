"""응답 도우미 응답 검증 모델과 API 호출 없는 검증 사례."""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class LLMResponse(BaseModel):
    outer_speech: str = Field(description="주 응답")
    inner_thought: str = Field(description="응답의 보조 설명")

    response_state: Literal["normal", "focused", "completed"]

    state_score_change: int = Field(
        ge=-5,
        le=5,
        strict=True,
        description="한 번의 예제 상태 점수 변화량",
    )


def run_checks():
    # 상태, 변화량, 허용 여부
    cases = [
        ("normal", 0, True),
        ("normal", -5, True),
        ("completed", 5, True),
        ("angry", 0, False),
        ("normal", 100, False),
        ("normal", -6, False),
        ("normal", "3", False),
        ("normal", True, False),
    ]

    passed = 0

    for mood, score, expected in cases:
        try:
            LLMResponse(
                outer_speech="안녕!",
                inner_thought="반갑다.",
                response_state=mood,
                state_score_change=score,
            )
            accepted = True
        except ValidationError:
            accepted = False

        matched = accepted == expected
        if matched:
            passed += 1

        status = "PASS" if matched else "FAIL"
        actual = "허용" if accepted else "거부"

        print(
            f"{status}: mood={mood!r}, "
            f"change={score!r} → {actual}"
        )

    print(f"\n{passed}/{len(cases)} 검증 통과")

    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    run_checks()
