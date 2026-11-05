"""설명과 실제 검증 규칙의 차이를 확인하는 학습 예제."""

from pydantic import BaseModel, Field, ValidationError


class DescriptionOnly(BaseModel):
    score: int = Field(description="-5부터 +5까지")


class ValidatedScore(BaseModel):
    score: int = Field(ge=-5, le=5, strict=True)


def main():
    # 설명만 작성하면 100도 통과한다.
    result = DescriptionOnly(score=100)
    print("설명만 있는 모델:", result.score)

    # 검증 규칙이 있는 모델과 비교한다.
    for value in [-5, 0, 5, 100, "3"]:
        try:
            result = ValidatedScore(score=value)
            print(f"{value!r}: 허용 → {result.score}")
        except ValidationError:
            print(f"{value!r}: 검증 실패")


if __name__ == "__main__":
    main()
