import json

from openai import OpenAI
from typing import Any

from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

SUBJECT_GUIDES = {
    "알고리즘": """
알고리즘 문제는 단순 개념 암기보다 알고리즘의 동작 과정, 시간복잡도, 정당성, 반례 판단을 중심으로 출제하라.

우선 고려할 문제 유형:
- 시간복잡도와 공간복잡도 분석
- 정렬, 탐색, 그래프 탐색의 수행 과정 추적
- BFS/DFS/다익스트라/플로이드/위상정렬 등 알고리즘 동작 순서 예측
- 그리디 알고리즘의 정당성 판단
- 동적 계획법 점화식 설계
- 분할정복 과정 분석
- 주어진 의사코드의 출력 결과 또는 수행 횟수 계산
- 특정 알고리즘이 실패하는 반례 찾기
- 알고리즘 선택 이유 설명

문제 생성 시 다음을 반영하라:
- easy: 정의, 기본 동작, 대표 예시 확인
- medium: 작은 입력에 대해 알고리즘 과정을 직접 추적
- hard: 시간복잡도 분석, 반례, 정당성, 여러 알고리즘 비교
- exam_like: 실제 전공 시험처럼 입력 예시를 주고 결과, 과정, 복잡도, 이유를 함께 묻는 문제
""",

    "마이크로프로세서": """
마이크로프로세서 문제는 CPU 구조, 레지스터, 명령어 실행 과정, 인터럽트, 메모리/입출력 제어를 중심으로 출제하라.

우선 고려할 문제 유형:
- 레지스터의 역할 설명
- 명령어 fetch-decode-execute cycle 분석
- 주소 지정 방식 구분
- 스택과 서브루틴 호출 과정 추적
- 인터럽트 발생 시 처리 순서 설명
- 메모리 맵과 I/O 맵 방식 비교
- 어셈블리 코드 실행 결과 추적
- 플래그 레지스터 변화 예측
- 타이머, 카운터, 포트 입출력 동작 설명
- 버스 구조와 제어 신호의 역할 설명

문제 생성 시 다음을 반영하라:
- easy: 레지스터, 버스, 명령어 사이클 등 기본 개념 확인
- medium: 간단한 어셈블리 코드나 명령어 실행 순서 추적
- hard: 스택, 인터럽트, 주소 지정 방식, 플래그 변화를 함께 분석
- exam_like: 실제 시험처럼 코드 또는 회로/레지스터 상태를 주고 실행 결과와 이유를 묻는 문제
""",

    "수치해석": """
수치해석 문제는 수학 공식을 단순 암기시키기보다 근사 계산 과정, 오차 분석, 반복법의 수렴 조건을 중심으로 출제하라.

우선 고려할 문제 유형:
- 이분법, 뉴턴법, 할선법의 반복 과정 계산
- 절대오차, 상대오차, 유효숫자 계산
- 보간법 적용
- 최소제곱법 개념 및 계산
- 수치미분과 수치적분 공식 적용
- 사다리꼴 공식, Simpson 공식 계산
- 선형시스템 반복해법 Jacobi/Gauss-Seidel 비교
- 수렴 조건 판단
- 초기값에 따른 반복법 결과 비교
- 계산 과정에서 발생하는 반올림 오차와 절단 오차 설명

문제 생성 시 다음을 반영하라:
- easy: 공식의 의미와 기본 개념 확인
- medium: 작은 숫자 예시를 사용해 1~2회 반복 계산
- hard: 오차 분석, 수렴 조건, 방법 간 비교 포함
- exam_like: 실제 전공 시험처럼 함수, 초기값, 반복 횟수를 주고 계산 과정과 오차를 함께 묻는 문제
""",

    "시스템프로그래밍": """
시스템프로그래밍 문제는 운영체제와 가까운 저수준 프로그래밍 개념, 프로세스, 파일, 메모리, 시스템 콜, 컴파일/링킹 과정을 중심으로 출제하라.

우선 고려할 문제 유형:
- 시스템 콜과 라이브러리 함수의 차이
- 프로세스 생성과 fork/exec/wait 동작 추적
- 파일 디스크립터와 open/read/write/close 동작 설명
- 표준 입출력 리다이렉션 과정
- 메모리 영역 text/data/heap/stack 구분
- 정적 링크와 동적 링크 비교
- 컴파일, 어셈블, 링크, 로딩 과정 설명
- Makefile 의존성 분석
- signal 처리 흐름
- 포인터, 버퍼, 주소, 엔디언 관련 코드 추적

문제 생성 시 다음을 반영하라:
- easy: 시스템 콜, 프로세스, 파일 디스크립터 등 기본 개념 확인
- medium: 짧은 C 코드의 실행 결과 또는 시스템 콜 흐름 추적
- hard: fork/exec/wait, 리다이렉션, signal, 메모리 구조를 복합적으로 분석
- exam_like: 실제 시험처럼 C 코드나 명령어 실행 예시를 주고 출력, 프로세스 수, 파일 디스크립터 상태, 이유를 묻는 문제
""",
}

def generate_questions(
    subject: str, 
    content: str, 
    question_type: str, 
    count: int,
    difficulty: str,
):
    if client is None:
        return [
            {
                "question_text": f"{subject}의 핵심 개념을 설명하시오.", 
                "answer": "이것은 예시 답변입니다.",
                "explanation": "더미 해설입니다.",
                "concept": "예시 개념 태그",
                "question_type": question_type,
            }
        ]
        
    subject_guide = SUBJECT_GUIDES.get(subject, "일반적인 컴퓨터소프트웨어학 전공 시험 문제를 생성하라.")
        
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 대비 튜터다.

과목: {subject}
문제 유형: {question_type}
난이도: {difficulty}
문제 개수: {count}

과목별 출제 가이드:
{subject_guide}

난이도 기준:
- easy: 핵심 개념을 확인하는 기본 문제
- medium: 개념 이해와 적용을 함께 묻는 문제
- hard: 여러 개념을 연결하거나 함정을 포함한 문제
- exam_like: 실제 대학 전공 시험에 나올 법한 문제

아래 공부 내용을 바탕으로 시험에 나올 법한 문제를 만들어라.

공부 내용:
{content}

반드시 JSON 배열로만 답하라.
각 객체는 다음 필드를 가져야 한다.

question_text: 문제
answer: 정답
explanation: 해설
concept: 핵심 개념
question_type: 문제 유형
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "너는 컴퓨터소프트웨어학 전공 시험 대비 문제 출제자다."},
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
                "concept": "파싱 오류",
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
        
        
def generate_question_from_rag_chunks(
    subject: str,
    chunks: list[dict[str, Any]],
    question_type: str = "short_answer",
    difficulty: str = "medium",
    count: int = 5,
) -> list[dict[str, Any]]:
    if client is None:
        return [
            {
                "question": "RAG 기반 예시 문제입니다. OPENAI_API_KEY를 설정하면 실제 문제가 생성됩니다.",
                "answer": "예시 정답입니다.",
                "explanation": "예시 해설입니다.",
                "concept": "RAG",
                "source": {
                    "material_id": chunks[0]["metadata"].get("material_id") if chunks else None,
                    "page_number": chunks[0]["metadata"].get("page_number") if chunks else None,
                    "chunk_index": chunks[0]["metadata"].get("chunk_index") if chunks else None,
                },
            }
        ]
        
    context_text = "\n\n".join(
        [
            (
                f"[Source {index + 1} | "
                f"material_id={chunk['metadata'].get('material_id')} | "
                f"page={chunk['metadata'].get('page_number')} | "
                f"chunk={chunk['metadata'],get('chunk_index')}]\n"
                f"{chunk['content']}"
            )
            for index, chunk in enumerate(chunks)
        ]
    )
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 시험 문제를 만드는 조교다.

아래 문서 근거만 사용해서 예상문제 {count}개를 생성하라.
문서에 없는 내용을 추측해서 문제로 만들지 마라.
각 문제는 반드시 어떤 Source를 근거로 만들었는지 포함하라.

과목: {subject}
문제 유형: {question_type}
난이도: {difficulty}

문서 근거:
{context_text}

반드시 아래 JSON 배열 형식으로만 응답하라.
마크다운 코드블록은 사용하지 마라.

[
  {{
    "question": "문제 내용",
    "answer": "정답",
    "explanation": "해설",
    "concept": "핵심 개념",
    "source_number": 1
  }}
]
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 문서 기반으로만 컴퓨터소프트웨어학 시험 문제를 생성하는 조교다.",
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
        questions = json.loads(content)
    except json.JSONDecodeError:
        return [
            {
                "question": content,
                "answer": "JSON 파싱 실패",
                "explanation": "AI 응답이 JSON 배열 형식이 아니었습니다.",
                "concept": "format_error",
                "source": None,
            }
        ]
        
    enriched_questions = []
    
    for item in questions:
        source_number = item.get("source_number", 1)
        
        try:
            source_index = int(source_number) - 1
        except (TypeError, ValueError):
            source_index = 0
            
        if source_index < 0 or source_index >= len(chunks):
            source_index = 0
            
        source_chunk = chunks[source_index]
        
        enriched_questions.append(
            {
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "explanation": item.get("explanation", ""),
                "concept": item.get("concept", ""),
                "source": {
                    "material_id": source_chunk["metadata"].get("material_id"),
                    "page_number": source_chunk["metadata"].get("page_number"),
                    "chunk_index": source_chunk["metadata"].get("chunk_index"),
                },
            }
        )
        
    return enriched_questions


def generate_weakness_questions_from_rag_chunks(
    subject: str,
    weakness_concepts: list[str],
    chunks: list[dict[str, Any]],
    question_type: str = "short_answer",
    difficulty: str = "exam_like",
    count: int = 5,
) -> list[dict[str, Any]]:
    if client is None:
        return [
            {
                "question": "약점 기반 RAG 예시 문제입니다. OPENAI_API_KEY를 설정하면 실제 문제가 생성됩니다.",
                "answer": "예시 정답입니다.",
                "explanation": "예시 해설입니다.",
                "concept": weakness_concepts[0] if weakness_concepts else "RAG",
                "source": {
                    "material_id": chunks[0]["metadata"].get("material_id") if chunks else None,
                    "page_number": chunks[0]["metadata"].get("page_number") if chunks else None,
                    "chunk_index": chunks[0]["metadata"].get("chunk_index") if chunks else None,
                }
            }
        ]
        
    context_text = "\n\n".join(
        [
            (
                f"[Source {index + 1} | "
                f"material_id={chunk['metadata'].get('material_id')} | "
                f"page={chunk['metadata'].get('page_number')} | "
                f"chunk={chunk['metadata'].get('chunk_index')}]\n"
                f"{chunk['content']}"
            )
            for index, chunk in enumerate(chunks)
        ]
    )
    
    weakness_text = ", ".join(weakness_concepts)
    
    prompt = f"""
너는 컴퓨터공학 전공 시험 대비를 돕는 AI 튜터다.

사용자의 약점 개념은 다음과 같다:
{weakness_text}

아래 문서 근거만 사용해서 약점 보강용 예상문제 {count}개를 생성하라.
각 문제는 사용자의 약점 개념 중 하나와 연결되어야 한다.
문서에 없는 내용을 추측해서 문제로 만들지 마라.
각 문제는 반드시 어떤 Source를 근거로 만들었는지 포함하라.

과목: {subject}
문제 유형: {question_type}
난이도: {difficulty}

문서 근거:
{context_text}

반드시 아래 JSON 배열 형식으로만 응답하라.
마크다운 코드블록은 사용하지 마라.

[
  {{
    "question": "문제 내용",
    "answer": "정답",
    "explanation": "해설",
    "concept": "약점 개념",
    "source_number": 1
  }}
]
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 문서 근거와 사용자 오답 개념을 기반으로 복습 문제를 생성하는 컴퓨터소프트웨어학 튜터다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.25,
    )
    
    content = response.choices[0].message.content
    
    try:
        questions = json.loads(content)
    except json.JSONDecodeError:
        return [
            {
                "question": content,
                "answer": "JSON 파싱 실패",
                "explanation": "AI 응답이 JSON 배열 형식이 아니었습니다.",
                "concept": "format_error",
                "source": None,
            }
        ]
        
    enriched_questions = []
    
    for item in questions:
        source_number = item.get("source_number", 1)
        
        try:
            source_index = int(source_number) - 1
        except (TypeError, ValueError):
            source_index = 0
            
        if source_index < 0 or source_index >= len(chunks):
            source_index = 0
            
        source_chunk = chunks[source_index]
        
        enriched_questions.append(
            {
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "explanation": item.get("explanation", ""),
                "concept": item.get("concept", ""),
                "source": {
                    "material_id": source_chunk["metadata"].get("material_id"),
                    "page_number": source_chunk["metadata"].get("page_number"),
                    "chunk_index": source_chunk["metadata"].get("chunk_index"),
                },
            }
        )
        
    return enriched_questions


def grade_exam_answer(
    question_text: str,
    correct_answer: str,
    explanation: str,
    user_answer: str,
) -> dict[str, Any]:
    if client is None:
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

    response = client.chat.completions.create(
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
    
    
def generate_study_report(
    user_name: str,
    subject: str | None,
    attempt_summary: dict[str, Any],
    weak_concepts: list[dict[str, Any]],
    score_trend: list[dict[str, Any]],
) -> str:
    if client is None:
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

    response = client.chat.completions.create(
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