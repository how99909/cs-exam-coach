import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def generate_questions(subject: str, content: str, question_type: str, count: int):
    if client is None:
        return [
            {
                "question_text": f"{subject}의 핵심 개념을 설명하시오.", 
                "answer": "이것은 예시 답변입니다.",
                "explanation": "더미 해설입니다.",
                "concept_tag": "예시 개념 태그",
                "question_type": question_type,
            }
        ]
        
    prompt = f"""
너는 컴퓨터공학 전공 시험 대비 튜터다.

과목: {subject}
문제 유형: {question_type}
문제 개수: {count}

아래 공부 내용을 바탕으로 시험에 나올 법한 문제를 만들어라.

공부 내용:
{content}

반드시 JSON 배열로만 답하라.
각 객체는 다음 필드를 가져야 한다.

question_text: 문제
answer: 정답
explanation: 해설
concept_tag: 핵심 개념 태그
question_type: 문제 유형
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "너는 컴퓨터공학 전공 시험 대비 문제 출제자다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    
    text = response.choices[0].message.content
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [
            {
                "question_text": "AI 응답 파싱 실패",
                "answer": text,
                "explanation": "AI 응답을 JSON으로 파싱하는 데 실패했습니다.",
                "concept_tag": "파싱 오류",
                "question_type": question_type,
            }
        ]
        
        
def grade_answer(question_text: str, correct_answer: str, user_answer: str, concept_tag: str | None):
    if client is None:
        return {
            "is_correct": False,
            "feedback": "더미 채점 결과입니다. OPEN_API_KEY를 설정하면 실제 채점 결과를 받을 수 있습니다.",
            "concept_tag": concept_tag,
        }
        
    prompt = f"""
너는 컴퓨터공학 전공 시험 채점자다.

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
  "concept_tag": "{concept_tag or ''}"
}}
"""

    response = client.chat.completions.create(
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
            "concept_tag": concept_tag,
        }