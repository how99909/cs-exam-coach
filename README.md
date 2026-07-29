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

## 4. 기술 스택

- Frontend: Streamlit
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- AI: OpenAI API
- Deployment: Docker, AWS EC2 예정

## 5. 시스템 구조

사용자 → Streamlit → FastAPI → PostgreSQL  
FastAPI → OpenAI API → 문제 생성/채점 결과 반환

## 6. 실행 방법

추가 예정

## 7. 향후 개선 사항

- PDF 업로드 기능
- RAG 기반 강의자료 질의응답
- 로그인 기능
- 과목별 학습 통계
- 시험 D-Day 기반 복습 계획
- 학회/스터디 그룹 기능