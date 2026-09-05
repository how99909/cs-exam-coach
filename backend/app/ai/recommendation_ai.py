import json

from typing import Any

from app.ai import openai_client
from app.core.config import settings


def generate_smart_review_queue_items(
    user_name: str,
    subject: str | None,
    weak_concepts: list[dict[str, Any]],
    recent_wrong_answers: list[dict[str, Any]],
    pending_checklists: list[dict[str, Any]],
    session_summary: dict[str, Any],
    attempt_summary: dict[str, Any],
    limit: int = 5,
) -> list[dict[str, Any]]:
    if openai_client.client is None:
        return [
            {
                "title": "오답 개념 복습",
                "reason": "오답이 많은 개념을 복습해야 합니다.",
                "action": "가장 많이 틀린 개념을 복습하고 관련 문제를 다시 풀어보세요.",
                "estimated_minutes": 30,
                "priority": 1,
                "source_type": "wrong_answer",
            }
        ]

    subject_label = subject if subject else "전체 과목"
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비를 돕는 AI 학습 코치다.

아래 학습 데이터를 바탕으로 사용자가 오늘 바로 실행할 수 있는 스마트 복습 큐 {limit}개를 생성하라.

사용자: {user_name}
과목: {subject_label}

취약 개념:
{weak_concepts}

최근 오답:
{recent_wrong_answers}

미완료 체크리스트:
{pending_checklists}

학습 세션 요약:
{session_summary}

응시 요약:
{attempt_summary}

반드시 아래 JSON 배열 형식으로만 응답하라.
마크다운 코드블록은 사용하지 마라.

[
  {
    "title": "할 일",
    "reason": "추천 이유",
    "action": "구체적인 실행 방법",
    "estimated_minutes": 30,
    "priority": 1,
    "source_type": "wrong_answer"
  }
]

규칙:
- 총 {limit}개 이하로 작성하라.
- 오답이 많은 개념을 우선 배치하라.
- 미완료 체크리스트가 있으면 최소 1개 반영하라.
- RAG 문제 생성, 응시 모드, 오답 복습, 학습 세션 기록 기능을 활용하도록 제안하라.
- 추상적인 조언 대신 바로 실행 가능한 행동으로 작성하라.
- 데이터가 부족하면 데이터가 부족하다고 말하라.
- 한국어로 작성하라.
"""

    response = openai_client.client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 사용자의 학습 데이터를 바탕으로 오늘의 복습 우선순위를 정하는 컴퓨터소프트웨어학 학습 코치다.",
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
                "title": "AI 복습 큐 파싱 실패",
                "reason": "AI 응답이 JSON 형식이 아니었습니다.",
                "action": content,
                "estimated_minutes": 30,
                "priority": 1,
                "source_type": "format_error",
            }
        ]
        
     