from typing import Any

from app.ai import openai_client
from app.core.config import settings


def generate_study_report(
    user_name: str,
    subject: str | None,
    attempt_summary: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
    score_trend: list[dict[str, Any]],
) -> str:
    if openai_client.client is None:
        return """
# 개인 맞춤 학습 리포트

OPENAI_API_KEY가 설정되어 있지 않아 예시 리포트를 반환합니다.

## 요약
최근 응시 기록과 오답 개념을 바탕으로 복습 우선순위를 정리하세요.

## 복습 우선순위
1. 오답 횟수가 많은 개념
2. 최근 응시에서 틀린 개념
3. 점수가 낮았던 과목

## 다음 학습 전략
- 약점 개념을 먼저 복습하세요.
- RAG 기반 약점 문제를 생성해 다시 풀어보세요.
- 응시 모드로 재시험을 진행하세요.
"""

    subject_label = subject if subject else "전체 과목"
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공생을 위한 AI 학습 코치다.

아래 사용자의 응시 분석 데이터를 바탕으로 개인 맞춤 학습 리포트를 작성하라.

사용자: {user_name}
분석 과목: {subject_label}

응시 요약:
{attempt_summary}

취약 개념:
{weak_concepts}

최근 점수 변화:
{score_trend}

리포트는 아래 구조로 작성하라.

# 개인 맞춤 학습 리포트

## 1. 현재 학습 상태 요약
- 최근 점수 흐름을 설명
- 전반적인 학습 상태 판단

## 2. 주요 취약 개념
- 오답이 많은 개념을 우선순위로 정리
- 각 개념을 왜 복습해야 하는지 설명

## 3. 이번 주 복습 우선순위
- 1순위, 2순위, 3순위로 제안
- 구체적으로 무엇을 해야 하는지 제시

## 4. 다음 응시 전략
- 다음 시험지/응시 모드에서 어떻게 풀어야 하는지 제안

## 5. 추천 학습 루틴
- 짧고 실행 가능한 루틴으로 제안

주의:
- 사용자의 데이터에 근거해서 작성하라.
- 과장하지 마라.
- 데이터가 부족하면 데이터가 부족하다고 말하라.
- 한국어로 작성하라.
"""

    response = openai_client.client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.4,
    )
    
    return response.choices[0].message.content


def generate_weekly_study_report(
    user_name: str, 
    subject: str | None, 
    period_summary: dict[str, Any],
    session_summary: dict[str, Any],
    attempt_summary: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
    checklist_summary: dict[str, Any],
) -> str:
    if openai_client.client is None:
        return """
# 주간 학습 요약 리포트

OPENAI_API_KEY가 설정되어 있지 않아 예시 리포트를 반환합니다.

## 1. 이번 주 학습량
최근 학습 세션과 공부 시간을 확인하세요.

## 2. 응시 결과
최근 응시 점수와 오답 개념을 확인하세요.

## 3. 다음 주 학습 우선순위
오답이 많은 개념과 미완료 체크리스트를 우선 처리하세요.
"""

    subject_label = subject if subject else "전체 과목"
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.

아래 데이터를 바탕으로 주간 학습 요약 리포트를 작성하라.

사용자: {user_name}
분석 과목: {subject_label}

분석 기간:
{period_summary}

학습 세션 요약:
{session_summary}

응시 기록 요약:
{attempt_summary}

취약 개념:
{weak_concepts}

체크리스트 요약:
{checklist_summary}

아래 구조로 작성하라.

# 주간 학습 요약 리포트

## 1. 이번 주 학습량 요약
- 총 공부 시간
- 학습 세션 수
- 평균 집중도
- 학습량이 충분했는지 판단

## 2. 응시 결과 요약
- 응시 횟수
- 평균 점수
- 최근 점수 흐름
- 정답률에 대한 판단

## 3. 주요 취약 개념
- 오답이 많은 개념을 우선순위로 정리
- 왜 다음 주에 복습해야 하는지 설명

## 4. 체크리스트 진행 상태
- 완료율을 기준으로 실행력을 판단
- 미완료 항목이 많으면 원인을 짚어라

## 5. 다음 주 학습 우선순위
- 1순위, 2순위, 3순위로 구체적으로 제안

## 6. 다음 주 실행 계획
- 하루 단위가 아니라 실행 가능한 학습 블록 단위로 제안
- RAG 문제 생성, 응시 모드, 오답 복습, 학습 세션 기록을 활용하도록 제안

주의:
- 데이터에 근거해서 작성하라.
- 데이터가 부족하면 부족하다고 말하라.
- 과장하지 마라.
- 한국어로 작성하라.
"""

    response = openai_client.client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 학습 데이터를 분석해 주간 학습 리포트를 작성하는 컴퓨터소프트웨어학 학습 코치다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.35,
    )
    
    return response.choices[0].message.content

