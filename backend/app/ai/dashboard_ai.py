from typing import Any

from app.ai import openai_client
from app.core.config import settings


def generate_goal_dashboard_comment(
    user_name: str,
    goal: dict[str, Any],
    checklist_summary: dict[str, Any],
    session_summary: dict[str, Any],
    attempt_summary: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
) -> str:
    if openai_client.client is None:
        return """
# 목표 상태 코멘트

OPENAI_API_KEY가 설정되어 있지 않아 예시 코멘트를 반환합니다.

현재 목표 점수와 남은 기간을 기준으로 학습량, 체크리스트 진행률, 응시 점수를 함께 확인하세요.
취약 개념을 먼저 복습하고, 응시 모드로 다시 점수를 확인하는 흐름을 추천합니다.
"""

    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.

아래 목표별 대시보드 데이터를 바탕으로 목표 상태 코멘트를 작성하라.

사용자:
{user_name}

학습 목표:
{goal}

체크리스트 요약:
{checklist_summary}

학습 세션 요약:
{session_summary}

응시 요약:
{attempt_summary}

취약 개념:
{weak_concepts}

아래 구조로 작성하라.

# 목표 상태 코멘트

## 1. 목표 달성 상태
- 현재 목표가 순조로운지, 위험한지 판단
- 판단 근거를 데이터 기반으로 설명

## 2. 가장 큰 병목
- 체크리스트, 공부 시간, 응시 점수, 취약 개념 중 핵심 병목을 짚어라

## 3. 다음 행동
- 오늘 또는 다음 학습 세션에서 바로 할 일을 3개 제안

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
                "content": "너는 목표별 학습 상태를 진단하는 컴퓨터소프트웨어학 학습 코치다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.35,
    )
    
    return response.choices[0].message.content


def generate_home_dashboard_comment(
    user_name: str,
    subject: str | None,
    goal_summary: dict[str, Any],
    session_summary: dict[str, Any],
    attempt_summary: dict[str, Any],
    review_queue_summary: dict[str, Any],
    checklist_summary: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
) -> str:
    if openai_client.client is None:
        return """
# 오늘의 학습 코멘트

OPENAI_API_KEY가 설정되어 있지 않아 예시 코멘트를 반환합니다.

오늘은 미완료 복습 큐와 오답이 많은 개념을 먼저 확인하세요.
최근 학습 시간이 부족하다면 짧은 학습 세션을 기록하고, 응시 모드로 현재 점수를 확인하는 것을 추천합니다.
"""

    subject_label = subject if subject else "전체 과목"
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.

아래 홈 대시보드 데이터를 바탕으로 오늘의 학습 코멘트를 작성하라.

사용자:
{user_name}

과목:
{subject_label}

가장 가까운 목표:
{goal_summary}

최근 7일 학습 세션 요약:
{session_summary}

최근 7일 응시 요약:
{attempt_summary}

스마트 복습 큐 요약:
{review_queue_summary}

체크리스트 요약:
{checklist_summary}

취약 개념:
{weak_concepts}

아래 구조로 작성하라.

# 오늘의 학습 코멘트

## 1. 오늘 가장 먼저 할 일
- 가장 우선순위 높은 행동 1개를 제안

## 2. 현재 상태 요약
- 목표, 점수, 학습 시간, 복습 큐 상태를 간단히 진단

## 3. 오늘의 추천 루틴
- 30~90분 안에 실행 가능한 루틴으로 제안

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
                "content": "너는 홈 대시보드 데이터를 바탕으로 오늘의 학습 우선순위를 제안하는 컴퓨터소프트웨어학 학습 코치다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.35,
    )
    
    return response.choices[0].message.content