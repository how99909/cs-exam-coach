# CS Exam Coach

컴소 전공 시험 대비를 위한 AI 문제 생성 및 오답 복습 서비스입니다.

현재 버전: v3.9
주요 업데이트: 스마트 리뷰 큐 저장 기능 추가

## 1. 프로젝트 개요

CS Exam Coach는 사용자가 전공 공부 내용을 입력하면 AI가 시험 대비 문제를 생성하고, 사용자의 답안을 채점한 뒤, 오답 개념을 저장하여 복습 우선순위를 추천합니다.

## 2. 개발 동기

기존 AI 학습 도구는 강의자료 요약에는 강하지만, 컴퓨터공학 전공 시험에서 자주 나오는 코드 추적형, SQL 작성형, 개념 비교형 문제 생성에는 특화되어 있지 않습니다. 이 프로젝트는 컴소 전공생의 시험 대비 과정에 맞춘 AI 학습 코치를 목표로 합니다.

## 3. 주요 기능

- 직접 입력하거나 PDF에서 추출한 학습 자료로 AI 예상문제 생성
- 객관식, 단답형, 서술형, 코드 추적형 등 다양한 문제 유형과 난이도 지원
- AI 답안 채점, 피드백 저장, 오답 개념별 복습 우선순위 추천
- 사용자 이름별 문제·오답 이력과 시험 D-Day 기반 복습 계획 관리
- 문제·해설·시험 적합도·난이도 및 RAG 답변 품질 평가
- PDF 페이지 단위 Chroma 인덱싱과 문서 근거 기반 RAG 질의응답
- RAG 문서 또는 사용자 약점을 기반으로 한 개인화 예상문제 생성
- 선택한 문제를 Markdown 시험지로 구성하고 정답·해설 포함 여부 선택
- Streamlit UI, FastAPI API, PostgreSQL, Chroma를 포함한 Docker Compose 실행 환경
- 응시 모드
- 생성 문제 기반 실전 풀이
- 전체 답안 제출
- AI 자동 채점
- 점수 계산
- 문항별 피드백 제공
- 오답 자동 저장
- 응시 기록 조회
- 응시 결과 분석 대시보드
- 최근 응시 기록 기반 평균 점수 계산
- 최근 점수 변화 시각화
- concept별 취약 개념 랭킹
- 과목별 응시 요약
- 개인 맞춤 학습 리포트 생성
- 응시 기록 기반 학습 상태 요약
- 취약 개념 기반 복습 우선순위 추천
- 다음 응시 전략 추천
- Markdown 리포트 다운로드
- 학습 목표 관리
- 목표 점수 설정
- 시험 날짜 설정
- 현재 평균 점수와 목표 점수 비교
- 남은 날짜 계산
- 취약 개념 기반 AI 목표 달성 전략 생성
- 학습 체크리스트 생성
- 학습 목표 기반 AI 실행 항목 생성
- 체크리스트 완료 상태 관리
- 체크리스트 진행률 계산
- 학습 세션 기록
- 과목별 공부 시간 기록
- 목표/체크리스트와 학습 세션 연결
- 공부 내용 및 회고 기록
- 집중도 점수 기록
- 과목별 총 학습 시간 조회
- 주간 학습 리포트 생성
- 최근 N일 학습 세션 요약
- 최근 N일 응시 기록 요약
- 체크리스트 진행률 요약
- 취약 개념 기반 다음 주 학습 우선순위 추천
- Markdown 리포트 다운로드
- 목표별 통합 대시보드
- 목표별 체크리스트 진행률 조회
- 목표별 학습 세션 요약
- 목표 과목 응시 기록 요약
- 목표 과목 취약 개념 분석
- AI 목표 상태 코멘트 생성
- 스마트 복습 큐 생성
- 오답 concept 기반 복습 우선순위 추천
- 최근 응시 기록 기반 복습 추천
- 미완료 체크리스트 기반 실행 항목 추천
- 최근 학습 세션 기반 학습량 반영
- 오늘 실행할 복습 큐 Markdown 다운로드
- 스마트 복습 큐 저장
- 저장된 복습 큐 조회
- 복습 큐 항목별 완료 처리
- 복습 큐 완료율 계산

## 4. 제한사항

- 현재 PDF 업로드 기능은 텍스트 기반 PDF를 대상으로 합니다.
- 스캔본 PDF는 OCR을 지원하지 않아 텍스트 추출이 제한될 수 있습니다.
- 긴 PDF는 AI API 입력 길이 제한으로 인해 일부 내용만 사용하는 방식으로 개선할 예정입니다.
- 현재 사용자 구분은 로그인 방식이 아니라 사용자 이름 입력 방식으로 동작합니다.
- 동일한 사용자 이름을 입력하면 같은 학습 기록을 조회할 수 있습니다.
- 실제 서비스에서는 회원가입/로그인 및 인증 기능이 필요합니다.
- 시험 복습 계획은 오답 빈도를 기준으로 한 규칙 기반 추천이며, 실제 학습 효과를 보장하지 않습니다.
- 페이지 범위는 사용자가 직접 입력해야 합니다.
- 현재 관리자 대시보드는 별도 인증 없이 접근 가능합니다.
- 실제 서비스에서는 관리자 인증 및 권한 분리가 필요합니다.
- 현재 RAG는 텍스트 추출 가능한 PDF만 지원합니다.
- 현재 source는 PDF 페이지 번호와 chunk 번호를 기준으로 표시됩니다.
- PDF 텍스트 추출 품질에 따라 page metadata 정확도가 달라질 수 있습니다.
- RAG 문서 삭제는 Chroma Vector DB의 chunk만 삭제합니다.
- PostgreSQL의 StudyMaterial 기록은 유지됩니다.
- 현재 문서 삭제는 사용자 이름, 과목, material_id 기준으로 동작합니다.
- 특정 문서 검색은 material_id 기준으로 동작합니다.
- 현재 여러 material_id를 동시에 선택하는 기능은 지원하지 않습니다.
- RAG 답변 평가는 사용자의 주관적 평가이며, 실제 정답성을 보장하지 않습니다.
- 현재 평가 데이터는 프롬프트 자동 개선에 직접 사용되지는 않습니다.
- RAG 기반 문제 생성은 Chroma에 인덱싱된 chunk를 기반으로 동작합니다.
- source는 문제 생성에 참고한 chunk 기준이며, 문제 전체의 완전한 근거를 보장하지는 않습니다.
- 동일한 chunk에서 유사 문제가 반복 생성될 수 있습니다.
- 약점 기반 RAG 문제 생성은 기존 오답 기록이 있어야 동작합니다.
- 오답 concept 품질이 낮으면 약점 분석 정확도도 낮아질 수 있습니다.
- 현재 약점 개념은 단순 오답 빈도 기준으로 집계합니다.
- v2.9 시험지는 Markdown 형식으로 생성됩니다.
- PDF 시험지 출력은 아직 지원하지 않습니다.
- 객관식 보기 섞기, 자동 배점, 시험 시간 설정은 아직 지원하지 않습니다.
- 응시 모드의 채점은 AI 기반 평가이므로 실제 교수자의 채점과 다를 수 있습니다.
- 현재 제한 시간, 임시 저장, 객관식 보기 섞기는 지원하지 않습니다.
- 오답 저장은 자동으로 수행되지만, concept 품질은 생성된 문제의 concept 값에 의존합니다.
- 응시 분석은 저장된 응시 기록을 기반으로 계산됩니다.
- concept별 취약 개념은 문제 생성 시 저장된 concept 값의 품질에 영향을 받습니다.
- 현재 분석은 최근 N개 응시 기록 기준입니다.
- 학습 리포트는 저장된 응시 기록과 오답 데이터를 기반으로 생성됩니다.
- 응시 기록이 부족하면 리포트 품질이 낮아질 수 있습니다.
- AI 리포트는 학습 전략 제안이며 실제 성적 향상을 보장하지 않습니다.
- 학습 목표는 현재 생성과 조회만 지원합니다.
- 목표 수정, 삭제, 완료 처리는 아직 지원하지 않습니다.
- 목표 달성 전략은 응시 기록과 오답 데이터가 충분할수록 품질이 좋아집니다.
- 체크리스트는 목표 기반 실행 항목을 생성하지만, 실제 학습 수행 여부는 사용자가 직접 체크해야 합니다.
- 현재 체크리스트 수정/삭제 기능은 지원하지 않습니다.
- 학습 세션은 사용자가 직접 입력한 공부 시간과 내용을 기반으로 기록됩니다.
- 현재 자동 타이머, 수정, 삭제 기능은 지원하지 않습니다.
- 집중도 점수는 사용자의 주관적 평가입니다.
- 주간 리포트는 저장된 학습 세션, 응시 기록, 체크리스트 데이터를 기반으로 생성됩니다.
- 데이터가 부족하면 리포트 품질이 낮아질 수 있습니다.
- 현재 리포트는 저장되지 않고 요청 시 생성됩니다.
- 목표별 대시보드는 목표에 연결된 학습 세션과 해당 과목 응시 기록을 기반으로 생성됩니다.
- 응시 기록이 부족하면 목표 달성 상태 판단의 정확도가 낮아질 수 있습니다.
- 현재 목표 달성 확률을 수치 모델로 예측하지는 않습니다.
- 스마트 복습 큐는 저장되지 않고 요청 시 생성됩니다.
- 추천 품질은 오답 기록, 응시 기록, 체크리스트, 학습 세션 데이터의 양과 품질에 영향을 받습니다.
- 현재 복습 큐 완료 처리 기능은 지원하지 않습니다.
- 현재 스마트 복습 큐는 생성 후 수동 완료 처리 방식입니다.
- 자동 알림, 반복 복습 간격 계산, 캘린더 연동은 아직 지원하지 않습니다.

## 5. 기술 스택

### Frontend
- Streamlit
- Requests

### Backend
- FastAPI
- Pydantic
- SQLAlchemy

### Database
- PostgreSQL

### AI
- OpenAI API

### Infra
- Docker
- Docker Compose

### RAG / Vector Search
- Chroma
- OpenAI Embeddings
- Vector Similarity Search

## 6. 시스템 구조

사용자는 Streamlit 화면에서 공부 내용을 입력하고, Frontend는 FastAPI 서버에 문제 생성을 요청합니다. FastAPI는 OpenAI API를 호출해 문제와 정답, 해설, 개념을 생성합니다. 생성된 문제와 사용자의 오답 기록은 PostgreSQL에 저장됩니다.

복습 추천 API는 오답 개념 빈도를 집계하여 우선 복습할 개념을 반환합니다.

```text
User
 ↓
Streamlit Frontend
 ↓
FastAPI Backend
 ↓
PostgreSQL

FastAPI Backend
 ├─ OpenAI API (문제 생성, 채점, 임베딩, RAG 답변)
 └─ Chroma (문서 chunk 및 vector 검색)
```

## 7. 주요 API

아래는 대표 API 사용 예시입니다. 전체 엔드포인트와 최신 요청 스키마는 실행 후 [Swagger UI](http://localhost:8000/docs)에서 확인할 수 있습니다.

문제(`Question`), 채점 결과, 오답 기록(`WrongAnswer`)의 개념 필드는 모두 `concept`입니다. 문제 난이도는 `easy`, `medium`, `hard`, `exam_like` 중 하나를 사용합니다.

### 1. 문제 생성 API

`POST /questions/generate`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "content": "프로세스는 실행 중인 프로그램이다...",
  "question_type": "short_answer",
  "count": 5,
  "difficulty": "medium"
}
```

#### Response

```json
{
  "user_name": "user_a",
  "material_id": 1,
  "questions": [
    {
      "question_id": 1,
      "question_text": "프로세스와 스레드의 차이를 설명하시오.",
      "answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
      "explanation": "스레드는 같은 프로세스의 메모리 공간을 공유한다.",
      "concept": "프로세스와 스레드",
      "question_type": "short_answer",
      "difficulty": "medium"
    }
  ]
}
```

### 2. 채점 API

`POST /grading/grade`

#### Request

```json
{
  "user_name": "user_a",
  "question_id": 1,
  "question_text": "프로세스와 스레드의 차이를 설명하시오.",
  "correct_answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
  "user_answer": "프로세스와 스레드는 같은 개념이다.",
  "concept": "프로세스와 스레드"
}
```

#### Response

```json
{
  "is_correct": false,
  "feedback": "프로세스와 스레드를 같은 개념으로 설명한 점이 틀렸습니다. 스레드는 프로세스 내부에서 실행되며 자원을 공유합니다.",
  "concept": "프로세스와 스레드"
}
```

### 3. 복습 추천 API

`GET /review/recommendations`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |

#### Response

```json
[
  {
    "concept": "프로세스와 스레드",
    "wrong_count": 3,
    "recommendation": "프로세스와 스레드 개념을 우선 복습하세요."
  }
]
```

### 4. 최근 생성 문제 조회 API

`GET /history/questions`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |

#### Response

```json
[
  {
    "id": 12,
    "material_id": 3,
    "question_text": "프로세스와 스레드의 차이를 설명하시오.",
    "answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
    "explanation": "같은 프로세스의 스레드는 메모리 공간과 자원을 공유한다.",
    "concept": "프로세스와 스레드",
    "question_type": "short_answer",
    "difficulty": "medium",
    "created_at": "2026-07-30T17:45:12.123456"
  }
]
```

### 5. 최근 오답 기록 조회 API

`GET /history/wrong-answers`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |

#### Response

```json
[
  {
    "id": 8,
    "question_id": 12,
    "user_answer": "프로세스와 스레드는 같은 개념이다.",
    "correct_answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
    "concept": "프로세스와 스레드",
    "feedback": "스레드는 프로세스 내부에서 실행되며 같은 프로세스의 자원을 공유합니다.",
    "is_correct": false,
    "created_at": "2026-07-30T17:48:31.654321"
  }
]
```

### 6. PDF 텍스트 추출 API

`POST /materials/extract-pdf`

#### Request

Form Data:

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명 |
| start_page | 시작 페이지 |
| end_page | 끝 페이지 |
| file | PDF 파일 |

#### Response

```json
{
  "success": true,
  "user_name": "user_a",
  "material_id": 1,
  "subject": "운영체제",
  "filename": "os_chapter1.pdf",
  "page_count": 20,
  "selected_start_page": 3,
  "selected_end_page": 7,
  "selected_page_count": 5,
  "text_length": 8432,
  "preview": "운영체제란...",
  "content": "전체 추출 텍스트"
}
```

### 7. 시험 D-Day 복습 계획 API

`GET /review/study-plan`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| exam_date | 시험 날짜, YYYY-MM-DD 형식 |

#### Response

```json
{
  "success": true,
  "user_name": "user_a",
  "exam_date": "2026-08-15",
  "days_left": 14,
  "weak_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 3
    }
  ],
  "plan": [
    {
      "day": "D-14 ~ D-8",
      "task": "오답 빈도가 높은 개념부터 차근차근 복습하고, 관련 개념을 다시 정리하세요.",
      "concepts": ["프로세스와 스레드"]
    }
  ]
}
```

### 8. 문제 평가 저장 API

`POST /feedback/question`

#### Request

```json
{
  "user_name": "user_a",
  "question_id": 1,
  "quality_score": 5,
  "explanation_score": 4,
  "exam_relevance_score": 5,
  "difficulty_match_score": 4,
  "comment": "시험 대비에 도움이 되는 문제였습니다."
}
```

#### Response

```json
{
  "success": true,
  "message": "문제 평가가 저장되었습니다.",
  "feedback_id": 1
}
```

### 9. 문제 평가 요약 API

`GET /feedback/summary`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |

#### Response

```json
{
  "feedback_count": 3,
  "avg_quality_score": 4.67,
  "avg_explanation_score": 4.33,
  "avg_exam_relevance_score": 4.67,
  "avg_difficulty_match_score": 4.0
}
```

### 10. 관리자용 평가 대시보드 API

`GET /feedback/admin-dashboard`

#### Response

```json
{
  "feedback_count": 10,
  "summary": {
    "avg_quality_score": 4.1,
    "avg_explanation_score": 4.0,
    "avg_exam_relevance_score": 3.8,
    "avg_difficulty_match_score": 4.2
  },
  "low_score_questions": [],
  "low_exam_relevance_questions": [],
  "recent_comments": []
}
```

### 11. RAG 문서 인덱싱 API

`POST /rag/index`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "material_id": 1,
  "content": "운영체제 강의자료 텍스트..."
}
```

#### Response

```json
{
  "success": true,
  "message": "문서 인덱싱이 완료되었습니다.",
  "chunk_count": 8,
  "material_id": 1
}
```

### 12. RAG 문서 질의응답 API

`POST /rag/ask`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "question": "프로세스와 스레드의 차이는?",
  "top_k": 5,
  "material_id": 1
}
```

#### Response

```json
{
  "success": true,
  "search_scope": "material_id=1 문서",
  "material_id": 1,
  "answer": "프로세스는...",
  "sources": [
    {
      "source_number": 1,
      "material_id": 1,
      "page_number": 12,
      "chunk_index": 0,
      "distance": 0.23,
      "preview": "프로세스는 실행 중인 프로그램..."
    }
  ]
}
```

### 13. RAG 문서 목록 조회 API

`GET /rag/documents`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |

#### Response

```json
{
  "success": true,
  "document_count": 1,
  "documents": [
    {
      "user_name": "user_a",
      "subject": "운영체제",
      "material_id": 1,
      "chunk_count": 8,
      "pages": [2, 3, 4],
      "page_count": 3
    }
  ]
}
```

### 14. RAG 문서 삭제 API

`DELETE /rag/documents`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "material_id": 1
}
```

#### Response

```json
{
  "success": true,
  "message": "인덱싱 문서가 삭제되었습니다.",
  "deleted_count": 8,
  "material_id": 1
}
```

### 15. RAG 답변 평가 저장 API

`POST /rag-feedback/answer`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "material_id": 1,
  "question": "프로세스와 스레드의 차이는?",
  "answer": "프로세스는...",
  "accuracy_score": 5,
  "grounding_score": 4,
  "source_relevance_score": 5,
  "helpfulness_score": 5,
  "comment": "출처가 명확해서 좋았습니다."
}
```

#### Response

```json
{
  "success": true,
  "message": "RAG 답변 평가가 저장되었습니다.",
  "feedback_id": 1
}
```

### 16. RAG 답변 평가 요약 API

`GET /rag-feedback/summary`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |

#### Response

```json
{
  "feedback_count": 3,
  "avg_accuracy_score": 4.67,
  "avg_grounding_score": 4.33,
  "avg_source_relevance_score": 4.67,
  "avg_helpfulness_score": 4.0
}
```

### 17. RAG 기반 예상문제 생성 API

`POST /rag-questions/generate`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "material_id": 1,
  "question_type": "short_answer",
  "difficulty": "exam_like",
  "count": 5,
  "top_k": 8
}
```

#### Response

```json
{
  "success": true,
  "message": "RAG 기반 예상문제가 생성되었습니다.",
  "question_count": 5,
  "material_id": 1,
  "questions": [
    {
      "id": 10,
      "question": "프로세스와 스레드의 차이를 설명하시오.",
      "answer": "프로세스는...",
      "explanation": "문서에서는...",
      "concept": "프로세스와 스레드",
      "question_type": "short_answer",
      "difficulty": "exam_like",
      "source": {
        "material_id": 1,
        "page_number": 12,
        "chunk_index": 0
      }
    }
  ]
}
```

### 18. 약점 기반 RAG 복습 문제 생성 API

`POST /weakness-rag-questions/generate`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "material_id": 1,
  "weakness_count": 3,
  "question_count": 5,
  "question_type": "short_answer",
  "difficulty": "exam_like",
  "top_k_per_concept": 3
}
```

#### Response

```json
{
  "success": true,
  "message": "약점 기반 RAG 복습 문제가 생성되었습니다.",
  "weakness_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 3
    }
  ],
  "used_chunk_count": 6,
  "question_count": 5,
  "material_id": 1,
  "questions": [
    {
      "id": 21,
      "question": "프로세스와 스레드의 차이를 설명하시오.",
      "answer": "프로세스는...",
      "explanation": "문서에서는...",
      "concept": "프로세스와 스레드",
      "question_type": "short_answer",
      "difficulty": "exam_like",
      "source": {
        "material_id": 1,
        "page_number": 12,
        "chunk_index": 0
      }
    }
  ]
}
```

### 19. 시험지용 문제 목록 조회 API

`GET /exam-papers/questions`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명 |
| limit | 조회할 최근 문제 수 |

#### Response

```json
{
  "success": true,
  "question_count": 2,
  "questions": [
    {
      "id": 1,
      "question": "프로세스와 스레드의 차이를 설명하시오.",
      "answer": "프로세스는...",
      "explanation": "해설...",
      "concept": "프로세스와 스레드",
      "question_type": "short_answer",
      "difficulty": "exam_like"
    }
  ]
}
```

### 20. 시험지 생성 API

`POST /exam-papers/generate`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "question_ids": [1, 2, 3],
  "title": "운영체제 중간고사 대비 연습 시험지",
  "include_answers": false,
  "include_explanations": false
}
```

#### Response

```json
{
  "success": true,
  "message": "시험지가 생성되었습니다.",
  "title": "운영체제 중간고사 대비 연습 시험지",
  "question_count": 3,
  "include_answers": false,
  "include_explanations": false,
  "markdown": "# 운영체제 중간고사 대비 연습 시험지..."
}
```

### 21. 시험 응시 제출 API

`POST /exam-attempts/submit`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "title": "운영체제 연습 응시",
  "answers": [
    {
      "question_id": 1,
      "user_answer": "프로세스는 실행 중인 프로그램이고, 스레드는 프로세스 안의 실행 단위입니다."
    }
  ]
}
```

#### Response

```json
{
  "success": true,
  "message": "시험 응시 결과가 저장되었습니다.",
  "attempt_id": 1,
  "title": "운영체제 연습 응시",
  "subject": "운영체제",
  "total_questions": 5,
  "correct_count": 4,
  "score": 80,
  "results": [
    {
      "question_id": 1,
      "question": "프로세스와 스레드의 차이를 설명하시오.",
      "user_answer": "프로세스는...",
      "correct_answer": "프로세스는...",
      "is_correct": true,
      "feedback": "핵심 개념을 잘 설명했습니다.",
      "concept": "프로세스와 스레드"
    }
  ]
}
```

### 22. 응시 기록 조회 API

`GET /exam-attempts/history`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |
| limit | 조회할 최근 응시 기록 수 |

### 23. 응시 결과 분석 API

`GET /exam-attempts/analytics`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |
| limit | 분석할 최근 응시 기록 수 |

#### Response

```json
{
  "success": true,
  "attempt_count": 5,
  "average_score": 76.0,
  "latest_score": 80,
  "score_trend": [
    {
      "attempt_id": 1,
      "title": "운영체제 연습 응시",
      "subject": "운영체제",
      "score": 80,
      "correct_count": 4,
      "total_questions": 5,
      "created_at": "2026-08-08T12:00:00"
    }
  ],
  "weak_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 3
    }
  ],
  "subject_summary": [
    {
      "subject": "운영체제",
      "attempt_count": 3,
      "avg_score": 78.33,
      "max_score": 90,
      "min_score": 60
    }
  ]
}
```

### 24. 개인 맞춤 학습 리포트 생성 API

`POST /study-reports/generate`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "limit": 20
}
```

#### Response

```json
{
  "success": true,
  "message": "개인 맞춤 학습 리포트가 생성되었습니다.",
  "attempt_summary": {
    "attempt_count": 5,
    "average_score": 76.0,
    "latest_score": 80,
    "best_score": 90,
    "lowest_score": 60
  },
  "weak_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 3
    }
  ],
  "score_trend": [
    {
      "attempt_id": 1,
      "title": "운영체제 연습 응시",
      "subject": "운영체제",
      "score": 80
    }
  ],
  "report": "# 개인 맞춤 학습 리포트..."
}
```

### 25. 학습 목표 생성 API

`POST /study-goals`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "title": "운영체제 중간고사 목표",
  "target_score": 85,
  "exam_date": "2026-10-20"
}
```

#### Response

```json
{
  "success": true,
  "message": "학습 목표가 생성되었습니다.",
  "goal": {
    "id": 1,
    "subject": "운영체제",
    "title": "운영체제 중간고사 목표",
    "target_score": 85,
    "exam_date": "2026-10-20"
  }
}
```

### 26. 응시 기록 조회 API

`GET /study-goals/{goal_id}/status`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |

### 27. 목표 달성 전략 생성 API

`POST /study-goals/strategy`

#### Request

```json
{
  "user_name": "user_a",
  "goal_id": 1
}
```

### 28. 학습 체크리스트 생성 API

`POST /study-checklists/generate`

#### Request

```json
{
  "user_name": "user_a",
  "goal_id": 1,
  "item_count": 5
}
```

### 29. 학습 체크리스트 조회 API

`GET /study-checklists`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| goal_id | 학습 목표 ID, 선택 |
| subject | 과목명, 선택 |

### 30. 학습 체크리스트 상태 변경 API

`PATCH /study-checklists/{item_id}`

#### Request

```json
{
  "user_name": "user_a",
  "is_done": true
}
```

### 31. 학습 세션 생성 API

`POST /study-sessions`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "goal_id": 1,
  "checklist_item_id": 3,
  "duration_minutes": 60,
  "content": "프로세스와 스레드 개념 복습",
  "reflection": "스레드 동기화가 아직 헷갈림",
  "focus_score": 4
}
```

### 32. 학습 세션 조회 API

`GET /study-checklists`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |
| goal_id | 학습 목표 ID, 선택 |
| limit | 조회할 최근 세션 수 |

### 33. 학습 세션 요약 API

`GET /study-sessions/summary`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |

### 34. 주간 학습 리포트 생성 API

`POST /weekly-reports/generate`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "days": 7
}
```

#### Response

```json
{
  "success": true,
  "message": "주간 학습 리포트가 생성되었습니다.",
  "period_summary": {
    "days": 7,
    "start_at": "2026-08-01T00:00:00",
    "end_at": "2026-08-08T00:00:00"
  },
  "session_summary": {
    "session_count": 3,
    "total_minutes": 180,
    "total_hours": 3.0,
    "avg_focus_score": 4.0
  },
  "attempt_summary": {
    "attempt_count": 2,
    "avg_score": 75.0,
    "latest_score": 80
  },
  "weak_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 2
    }
  ],
  "checklist_summary": {
    "total_count": 5,
    "done_count": 3,
    "progress_rate": 60.0
  },
  "report": "# 주간 학습 요약 리포트..."
}
```

### 35. 목표별 대시보드 API

`POST /goal-dashboard`

#### Request

```json
{
  "user_name": "user_a",
  "goal_id": 1
}
```

#### Response

```json
{
  "success": true,
  "message": "목표별 대시보드가 생성되었습니다.",
  "goal": {
    "id": 1,
    "subject": "운영체제",
    "title": "운영체제 중간고사 목표",
    "target_score": 85,
    "exam_date": "2026-10-20",
    "days_left": 73
  },
  "checklist_summary": {
    "total_count": 5,
    "done_count": 3,
    "pending_count": 2,
    "progress_rate": 60.0
  },
  "session_summary": {
    "session_count": 4,
    "total_hours": 5.5,
    "avg_focus_score": 4.0
  },
  "attempt_summary": {
    "attempt_count": 3,
    "avg_score": 76.67,
    "latest_score": 80,
    "best_score": 85,
    "target_score": 85,
    "score_gap": 8.33
  },
  "weak_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 2
    }
  ],
  "comment": "# 목표 상태 코멘트..."
}
```

### 36. 스마트 복습 큐 생성 API

`POST /smart-review/queue/save`

#### Request

```json
{
  "user_name": "user_a",
  "subject": "운영체제",
  "limit": 5
}
```

#### Response

```json
{
  "success": true,
  "message": "스마트 복습 큐가 생성되었습니다.",
  "weak_concepts": [
    {
      "concept": "프로세스와 스레드",
      "wrong_count": 3
    }
  ],
  "pending_checklists": [
    {
      "id": 1,
      "subject": "운영체제",
      "title": "프로세스와 스레드 복습",
      "priority": 1
    }
  ],
  "session_summary": {
    "period_days": 7,
    "session_count": 3,
    "total_hours": 4.5,
    "avg_focus_score": 4.0
  },
  "attempt_summary": {
    "period_days": 7,
    "attempt_count": 2,
    "avg_score": 75.0,
    "latest_score": 80
  },
  "queue": "# 오늘의 스마트 복습 큐..."
}
```

### 37. 스마트 복습 큐 조회 API

`GET /smart-review/queue/items`

#### Query Parameters

| 이름 | 설명 |
|---|---|
| user_name | 사용자 이름 |
| subject | 과목명, 선택 |
| include_done | 완료 항목 포함 여부 |
| limit | 조회 개수 |

### 38. 스마트 복습 큐 상태 변경 API

`PATCH /smart-review/queue/items/{item_id}`

#### Request

```json
{
  "user_name": "user_a",
  "is_done": true
}
```

## 8. 실행 방법

### 사전 요구사항

- Docker 및 Docker Compose
- OpenAI API key

### 1. 환경 변수 설정

`backend/.env` 파일을 생성합니다.

```env
DATABASE_URL=postgresql://postgres:password@db:5432/cs_exam_coach
OPENAI_API_KEY=your_openai_api_key
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

`DATABASE_URL`의 사용자명, 비밀번호, DB 이름은 `docker-compose.yml`의 PostgreSQL 설정과 같아야 합니다. 모델 환경변수는 생략하면 위 값이 기본으로 사용됩니다.

### 2. DB와 Chroma 실행

```bash
docker compose up -d db chroma
```

### 3. DB migration 적용

```bash
docker compose run --rm backend alembic upgrade head
```

### 4. 전체 서비스 실행

```bash
docker compose up --build
```

### 5. 접속 주소

```text
Frontend: http://localhost:8501
Backend API Docs: http://localhost:8000/docs
Backend OpenAPI JSON: http://localhost:8000/openapi.json
```

## 9. Database Migration

이 프로젝트는 Alembic을 사용해 데이터베이스 스키마를 관리합니다.

### 모델 변경 후 migration 생성

```bash
docker compose run --rm backend alembic revision --autogenerate -m "Migration message"
```

### migration 적용

```bash
docker compose run --rm backend alembic upgrade head
```

### 주의 사항

기존에는 Base.metadata.create_all()로 테이블을 자동 생성했지만, v2.5부터는 Alembic migration을 통해 DB 스키마를 관리합니다.

## 10. Backend Structure

v2.6부터 백엔드 코드를 역할별로 분리했습니다.

```text
backend/app
├─ core/
│  └─ config.py          # 환경변수 및 설정 관리
├─ routers/              # HTTP API 엔드포인트
├─ rag_service.py         # RAG 인덱싱, 검색, 답변 생성 로직
├─ crud_rag_feedback.py   # RAG 답변 평가 DB 로직
├─ models.py              # SQLAlchemy DB 모델
├─ schemas.py             # Pydantic 요청/응답 스키마
├─ database.py            # DB 연결 및 세션 관리
└─ main.py                # FastAPI 앱 진입점
```

### 구조 개선 내용

- 환경변수 관리를 core/config.py로 통합
- RAG API 실패 케이스를 HTTPException 기반으로 처리
- RAG 답변 평가 DB 로직을 router에서 crud_rag_feedback.py로 분리
- router는 HTTP 요청/응답 처리에 집중하도록 정리

## 11. 시연 흐름

1. 과목을 선택합니다.
2. 공부 내용을 입력합니다.
3. 문제 유형과 문제 개수를 선택합니다.
4. AI가 시험 대비 문제를 생성합니다.
5. 사용자가 답안을 입력합니다.
6. AI가 답안을 채점하고 피드백을 제공합니다.
7. 오답 개념이 저장됩니다.
8. 복습 추천 화면에서 많이 틀린 개념을 확인합니다.

## 12. 시연 화면

### 메인 화면

![메인 화면](docs/images/main.png)

### 문제 생성

![문제 생성](docs/images/question-generation.png)

### 채점 결과

![채점 결과](docs/images/grading-result.png)

### 복습 추천

![복습 추천](docs/images/review-recommendation.png)

## 13. 향후 개선 사항

- 회원가입·로그인과 역할 기반 접근 제어
- 과목별 학습 성과 및 난이도별 정답률 통계
- 사용자 성취도에 따른 문제 난이도 자동 조절
- OCR 기반 스캔 PDF 지원
- PDF 시험지 출력, 자동 배점, 시험 시간 설정
- 스터디 그룹 문제·시험지 공유
