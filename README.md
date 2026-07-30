# CS Exam Coach

컴소 전공 시험 대비를 위한 AI 문제 생성 및 오답 복습 서비스입니다.

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

사용자 → Streamlit → FastAPI → PostgreSQL  
FastAPI → OpenAI API → 문제 생성/채점 결과 반환

## 6. 실행 방법

### 1. 환경 변수 설정

`backend/.env` 파일을 생성하고 아래 내용을 입력합니다.

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/cs_exam_coach
OPENAI_API_KEY=your_openai_api_key
```

### 2. Docker Compose 실행

```bash
docker compose up --build
```

### 3. 접속 주소

* Frontend: [http://localhost:8501](http://localhost:8501)
* Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 7. 향후 개선 사항

- PDF 업로드 기능
- RAG 기반 강의자료 질의응답
- 로그인 기능
- 과목별 학습 통계
- 시험 D-Day 기반 복습 계획
- 학회/스터디 그룹 기능
