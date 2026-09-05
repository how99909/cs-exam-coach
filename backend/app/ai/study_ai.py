import json

from typing import Any

from app.ai import openai_client
from app.core.config import settings


def generate_goal_strategy(
    user_name: str,
    goal: dict[str, Any],
    current_status: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
) -> str:
    if openai_client.client is None:
        return """
# 목표 달성 전략

OPENAI_API_KEY가 설정되어 있지 않아 예시 전략을 반환합니다.

## 현재 상태
현재 평균 점수와 목표 점수의 차이를 확인하세요.

## 우선순위
1. 오답이 많은 개념 복습
2. 최근 응시에서 틀린 문제 재풀이
3. 약점 기반 RAG 문제 생성 후 응시 모드로 재시험

## 추천 루틴
- 매일 약점 개념 1개 복습
- 관련 RAG 문제 3개 풀이
- 주 2회 응시 모드로 점수 확인
"""

    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.

아래 사용자의 학습 목표와 현재 상태를 바탕으로 목표 달성 전략을 작성하라.

사용자:
{user_name}

학습 목표:
{goal}

현재 학습 상태:
{current_status}

취약 개념:
{weak_concepts}

아래 구조로 작성하라.

# 목표 달성 전략

## 1. 목표 요약
- 목표 점수
- 시험 날짜
- 남은 기간
- 현재 점수와 목표 점수 차이

## 2. 현재 상태 진단
- 현재 평균 점수 기준으로 현실적인 상태 분석
- 데이터가 부족하면 부족하다고 명시

## 3. 우선 복습해야 할 개념
- 취약 개념을 우선순위로 정리
- 왜 먼저 복습해야 하는지 설명

## 4. 남은 기간 학습 전략
- 남은 기간에 맞는 실행 계획 제안
- 너무 추상적으로 쓰지 말고 실제 행동 단위로 제안

## 5. 다음 응시 전략
- 다음 응시 모드에서 어떤 방식으로 풀어야 하는지 제안

주의:
- 사용자의 데이터에 근거해서 작성하라.
- 과장하지 마라.
- 한국어로 작성하라.
"""

    response = openai_client.client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 목표 기반 학습 전략을 제안하는 컴퓨터소프트웨어학 학습 코치다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.35,
    )
    
    return response.choices[0].message.content


def generate_study_checklist_items(
    goal: dict[str, Any],
    current_status: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
    item_count: int = 5,
) -> list[dict[str, Any]]:
    if openai_client.client is None:
        return [
            {
                "title": "약점 개념 복습하기",
                "description": "오답이 많은 개념을 정리하고 관련 문제를 다시 풀어보세요.",
                "priority": 1,
            }
        ]
        
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.

아래 학습 목표와 현재 상태를 바탕으로 사용자가 바로 실행할 수 있는 체크리스트 {item_count}개를 생성하라.

학습 목표:
{goal}

현재 상태:
{current_status}

취약 개념:
{weak_concepts}

반드시 아래 JSON 배열 형식으로만 응답하라.
마크다운 코드블록은 사용하지 마라.

[
  {{
    "title": "할 일 제목",
    "description": "구체적인 실행 설명",
    "priority": 1
  }}
]

규칙:
- priority는 1이 가장 중요하고 숫자가 커질수록 낮은 우선순위다.
- 할 일은 추상적이지 않게 작성하라.
- 각 항목은 30~60분 안에 실행 가능한 단위로 작성하라.
- 한국어로 작성하라.
"""

    response = openai_client.client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 목표 기반 학습 체크리스트를 만드는 컴퓨터소프트웨어학 학습 코치다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.3,
    )
    
    content = response.choices[0].message.content
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return [
            {
                "title": "AI 체크리스트 파싱 실패",
                "description": content,
                "priority": 1,
            }
        ]
        
        