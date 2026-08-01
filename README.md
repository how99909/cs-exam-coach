# CS Exam Coach

컴소 전공 시험 대비를 위한 AI 문제 생성 및 오답 복습 서비스입니다.

현재 버전: v1.2  
주요 업데이트: 사용자 피드백 기반 문제 난이도 선택 기능 및 과목별 문제 생성 가이드 추가

## 1. 프로젝트 개요

CS Exam Coach는 사용자가 전공 공부 내용을 입력하면 AI가 시험 대비 문제를 생성하고, 사용자의 답안을 채점한 뒤, 오답 개념을 저장하여 복습 우선순위를 추천합니다.

## 2. 개발 동기

기존 AI 학습 도구는 강의자료 요약에는 강하지만, 컴퓨터공학 전공 시험에서 자주 나오는 코드 추적형, SQL 작성형, 개념 비교형 문제 생성에는 특화되어 있지 않습니다. 이 프로젝트는 컴소 전공생의 시험 대비 과정에 맞춘 AI 학습 코치를 목표로 합니다.

## 3. 주요 기능

- 과목별 공부 내용 입력
- AI 기반 예상문제 생성
- 객관식/단답형/서술형/코드추적형 등 문제 지원
- 사용자 답안 채점
- 오답 개념 저장
- 오답 빈도 기반 복습 추천
- Streamlit 기반 웹 UI
- Docker Compose 기반 실행 환경 구성
- 최근 생성 문제 조회
- 최근 오답 기록 조회
- 학습 기록 기반 복습 관리
- 문제 난이도 선택

## 4. 기술 스택

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

## 5. 시스템 구조

사용자는 Streamlit 화면에서 공부 내용을 입력합니다.  
Frontend는 FastAPI 서버에 문제 생성을 요청합니다.  
FastAPI는 AI API를 호출해 문제와 정답, 해설, 개념 태그를 생성합니다.  
생성된 문제와 사용자의 오답 기록은 PostgreSQL에 저장됩니다.  
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
 ↓
OpenAI API
```

## 6. 주요 API

### 1. 문제 생성 API

`POST /questions/generate`

#### Request

```json
{
  "subject": "운영체제",
  "content": "프로세스는 실행 중인 프로그램이다...",
  "question_type": "short_answer",
  "count": 5
}
```

#### Response

```json
{
  "material_id": 1,
  "questions": [
    {
      "id": 1,
      "question_text": "프로세스와 스레드의 차이를 설명하시오.",
      "answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
      "explanation": "스레드는 같은 프로세스의 메모리 공간을 공유한다.",
      "concept_tag": "프로세스와 스레드",
      "question_type": "short_answer"
    }
  ]
}
```

### 2. 채점 API

`POST /grading/grade`

#### Request

```json
{
  "question_id": 1,
  "question_text": "프로세스와 스레드의 차이를 설명하시오.",
  "correct_answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
  "user_answer": "프로세스와 스레드는 같은 개념이다.",
  "concept_tag": "프로세스와 스레드"
}
```

#### Response

```json
{
  "is_correct": false,
  "feedback": "프로세스와 스레드를 같은 개념으로 설명한 점이 틀렸습니다. 스레드는 프로세스 내부에서 실행되며 자원을 공유합니다.",
  "concept_tag": "프로세스와 스레드"
}
```

### 3. 복습 추천 API

`GET /review/recommendations`

#### Response

```json
[
  {
    "concept_tag": "프로세스와 스레드",
    "wrong_count": 3,
    "recommendation": "프로세스와 스레드 개념을 우선 복습하세요."
  }
]
```

### 4. 최근 생성 문제 조회 API

`GET /history/questions`

#### Response

```json
[
  {
    "id": 12,
    "material_id": 3,
    "question_text": "프로세스와 스레드의 차이를 설명하시오.",
    "answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
    "explanation": "같은 프로세스의 스레드는 메모리 공간과 자원을 공유한다.",
    "concept_tag": "프로세스와 스레드",
    "question_type": "short_answer",
    "created_at": "2026-07-30T17:45:12.123456"
  }
]
```

### 5. 최근 오답 기록 조회 API

`GET /history/wrong-answers`

#### Response

```json
[
  {
    "id": 8,
    "question_id": 12,
    "user_answer": "프로세스와 스레드는 같은 개념이다.",
    "correct_answer": "프로세스는 독립된 실행 단위이고, 스레드는 프로세스 내부의 실행 단위이다.",
    "concept_tag": "프로세스와 스레드",
    "feedback": "스레드는 프로세스 내부에서 실행되며 같은 프로세스의 자원을 공유합니다.",
    "is_correct": false,
    "created_at": "2026-07-30T17:48:31.654321"
  }
]
```

## 7. 실행 방법

### 1. 환경 변수 설정

`backend/.env` 파일을 생성합니다.

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/cs_exam_coach
OPENAI_API_KEY=your_openai_api_key
```

### 2. Docker Compose 실행

```bash
docker compose up --build
```

### 3. 접속 주소

```text
Frontend: http://localhost:8501
Backend API Docs: http://localhost:8000/docs
```

## 8. 시연 흐름

1. 과목을 선택합니다.
2. 공부 내용을 입력합니다.
3. 문제 유형과 문제 개수를 선택합니다.
4. AI가 시험 대비 문제를 생성합니다.
5. 사용자가 답안을 입력합니다.
6. AI가 답안을 채점하고 피드백을 제공합니다.
7. 오답 개념이 저장됩니다.
8. 복습 추천 화면에서 많이 틀린 개념을 확인합니다.

## 9. 시연 화면

### 메인 화면

![메인 화면](docs/images/main.png)

### 문제 생성

![문제 생성](docs/images/question-generation.png)

### 채점 결과

![채점 결과](docs/images/grading-result.png)

### 복습 추천

![복습 추천](docs/images/review-recommendation.png)

## 10. 향후 개선 사항

* PDF 업로드 기능
* RAG 기반 강의자료 질의응답
* 로그인 및 사용자별 학습 기록
* 과목별 학습 통계
* 시험 D-Day 기반 복습 계획
* 문제 난이도 자동 조절
* 스터디 그룹 공유 기능
* AWS EC2 배포
