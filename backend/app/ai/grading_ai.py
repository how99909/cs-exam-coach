import json

from typing import Any

from app.ai import openai_client
from app.core.config import settings


def grade_answer(question_text: str, correct_answer: str, user_answer: str, concept: str | None):
    if openai_client.client is None:
        return {
            "is_correct": False,
            "feedback": "더미 채점 결과입니다. OPEN_API_KEY를 설정하면 실제 채점 결과를 받을 수 있습니다.",
            "concept": concept,
        }
        
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 채점자다.

문제:
{question_text}

모범 답안:
{correct_answer}

학생 답안:
{user_answer}

학생 답안이 맞는지 판단하고 피드백을 제공하라.

반드시 아래 JSON 형식으로만 답하라.

{{
  "is_correct": true 또는 false,
  "feedback": "구체적인 피드백",
  "concept": "{concept or ''}"
}}
"""

    response = openai_client.client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "너는 엄격하지만 친절한 컴퓨터공학 전공 채점자다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    
    text = response.choices[0].message.content
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "is_correct": False,
            "feedback": text,
            "concept": concept,
        }
        
       
def grade_exam_answer(
    question_text: str,
    correct_answer: str,
    explanation: str,
    user_answer: str,
) -> dict[str, Any]:
    if openai_client.client is None:
        is_coreect = user_answer.strip() == correct_answer.strip()
        
        return {
            "is_correct": is_coreect,
            "feedback": "OPENAI_API_KEY가 없어 단순 문자열 비교로 채점했습니다.",
        }
        
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 답안을 채점하는 조교다.

아래 문제, 모범답안, 해설을 기준으로 사용자의 답안을 채점하라.

문제:
{question_text}

모범답안:
{correct_answer}

해설:
{explanation}

사용자 답안:
{user_answer}

채점 기준:
- 핵심 개념이 맞으면 정답으로 처리한다.
- 표현이 달라도 의미가 같으면 정답으로 처리한다.
- 핵심 개념이 빠졌거나 반대로 설명했으면 오답으로 처리한다.

반드시 아래 JSON 형식으로만 응답하라.
마크다운 코드블록은 사용하지 마라.

{{
  "is_correct": true,
  "feedback": "채점 피드백"
}}
"""

    response = openai_client.client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 컴퓨터소프트웨어학 시험 답안을 엄격하지만 합리적으로 채점하는 조교다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
    )
    
    content = response.choices[0].message.content
    
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {
            "is_correct": False,
            "feedback": f"채점 결과 JSON 파싱에 실패했습니다. 원문 응답: {content}",
        }
        
    return {
        "is_correct": bool(result.get("is_correct", False)),
        "feedback": result.get("feedback", ""),
    }