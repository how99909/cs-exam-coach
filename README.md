# CS Exam Coach

컴퓨터공학 전공 시험 대비를 위한 AI 문제 생성·채점·복습 관리 서비스입니다.

- 제품 버전: **v3.9**
- API 버전: **0.3.9**
- 최근 주요 변경: 스마트 복습 큐 저장 및 완료 상태 관리

## 1. 프로젝트 소개

CS Exam Coach는 사용자가 직접 입력하거나 PDF에서 추출한 학습 자료를 바탕으로 예상문제를 생성하고, 답안을 채점한 뒤 오답과 학습 기록을 분석해 다음 학습 행동을 추천합니다.

단순한 자료 요약보다 컴퓨터공학 시험에서 자주 다루는 개념 비교, 코드 추적, SQL 작성, 서술형 문제의 생성과 반복 학습에 초점을 맞춥니다.

## 2. 주요 기능

### 문제 생성과 채점

- 직접 입력한 학습 내용 또는 PDF 추출 텍스트로 AI 예상문제 생성
- 객관식, 단답형, 서술형, 코드 추적형 등 문제 유형과 난이도 선택
- 개별 답안 및 모의시험 전체 답안 AI 채점
- 문항별 피드백, 점수, 오답 및 관련 개념 저장
- 최근 문제와 오답 기록 조회

### 시험과 학습 분석

- 선택한 문제로 Markdown 시험지 생성
- 정답과 해설 포함 여부 선택
- 응시 기록, 상세 결과, 평균 점수와 점수 추이 조회
- 과목별 응시 요약과 취약 개념 집계
- 개인 학습 리포트 및 다음 응시 전략 생성

### 목표와 학습 실행 관리

- 목표 점수와 시험일을 포함한 학습 목표 생성
- 현재 성적, 남은 기간, 취약 개념을 반영한 목표 달성 전략 생성
- 목표별 AI 체크리스트 생성 및 완료 상태 관리
- 공부 시간, 내용, 회고, 집중도와 목표·체크리스트 연결 기록
- 최근 학습 세션, 응시 기록, 체크리스트를 반영한 주간 리포트 생성
- 목표별 진행률과 학습 현황을 통합한 대시보드 제공

### RAG와 품질 평가

- PDF 페이지 단위 텍스트 추출 및 Chroma 문서 인덱싱
- 문서 근거 기반 질의응답과 출처 chunk 표시
- 인덱싱된 문서 또는 오답 취약 개념 기반 예상문제 생성
- 생성 문제와 RAG 답변에 대한 사용자 평가 저장
- 저평가 문제, 최근 의견, 평가 요약을 제공하는 운영 대시보드

### 스마트 복습 큐

- 오답 개념, 최근 응시 결과, 미완료 체크리스트, 학습량을 종합한 복습 항목 생성
- 생성한 복습 큐를 PostgreSQL에 저장
- 저장된 항목 조회, 항목별 완료 처리, 완료율 계산
- 오늘의 복습 큐를 Markdown으로 다운로드

## 3. 시스템 구성

```text
사용자
  ↓
Streamlit Frontend (:8501)
  ↓
FastAPI Backend (:8000)
  ├─ PostgreSQL (:5432) — 문제, 오답, 응시 및 학습 기록
  ├─ Chroma (:8001)     — 문서 chunk와 embedding
  └─ OpenAI API         — 생성, 채점, 리포트 및 embedding
```

| 영역 | 기술 |
| --- | --- |
| Frontend | Streamlit, Requests, Pandas |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| AI | OpenAI API |
| RAG | Chroma, OpenAI Embeddings, Vector Similarity Search |
| Infra | Docker, Docker Compose |

정확한 Python 패키지 버전은 `backend/requirements.txt`와 `frontend/requirements.txt`에 고정되어 있습니다.

## 4. 실행 방법

### 사전 요구사항

- Docker 및 Docker Compose
- AI 기능을 실제로 사용하려면 OpenAI API key

### 1. 환경 변수 준비

프로젝트 루트의 `.env.example`을 `.env`로 복사하고 DB 비밀번호를 변경합니다.

```env
POSTGRES_PASSWORD=change-me
```

`backend/.env.example`을 `backend/.env`로 복사하고 애플리케이션 환경 변수를 설정합니다.

```env
DATABASE_URL=postgresql://postgres:change-me@db:5432/cs_exam_coach
OPENAI_API_KEY=your_openai_api_key
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

Docker Compose에서는 루트 `.env`의 `POSTGRES_PASSWORD`로 백엔드 DB 연결 문자열을 구성합니다. 백엔드를 호스트에서 직접 실행한다면 `DATABASE_URL`의 호스트를 `localhost`로, Chroma 포트를 `8001`로 설정합니다.

### 2. DB와 Chroma 시작

```bash
docker compose up -d db chroma
```

### 3. DB 마이그레이션 적용

```bash
docker compose run --rm backend alembic upgrade head
```

### 4. 전체 서비스 시작

```bash
docker compose up --build
```

### 5. 접속 주소

| 서비스 | 주소 |
| --- | --- |
| Frontend | http://localhost:8501 |
| Swagger UI | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json |

## 5. 데이터베이스 마이그레이션

모델을 변경한 후 새 migration을 생성합니다.

```bash
docker compose run --rm backend alembic revision --autogenerate -m "Migration message"
```

생성된 migration 내용을 검토한 후 적용합니다.

```bash
docker compose run --rm backend alembic upgrade head
```

스키마는 Alembic으로 관리합니다. `Base.metadata.create_all()`을 별도로 실행하지 마세요.

## 6. 테스트

현재 회귀 테스트는 Python 표준 `unittest`로 실행합니다.

PowerShell:

```powershell
$env:PYTHONPATH="backend"
python -m unittest discover -s backend/tests -v
```

Bash:

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

## 7. API 요약

요청 필드, 허용 범위, 응답 모델의 최신 정의는 실행 중인 [Swagger UI](http://localhost:8000/docs)를 기준으로 확인하세요.

| Method | Endpoint | 설명 |
| --- | --- | --- |
| GET | `/` | API 이름과 버전 확인 |

### 문제·채점·이력

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/questions/generate` | 학습 자료 기반 문제 생성 및 저장 |
| POST | `/grading/grade` | 단일 답안 채점 및 오답 저장 |
| GET | `/history/questions` | 최근 생성 문제 조회 |
| GET | `/history/wrong-answers` | 최근 오답 조회 |
| GET | `/review/recommendations` | 오답 개념별 복습 우선순위 조회 |
| GET | `/review/study-plan` | 시험일까지의 복습 계획 생성 |
| POST | `/materials/extract-pdf` | PDF 페이지 범위 텍스트 추출 및 저장 |

### 문제 및 RAG 평가

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/feedback/question` | 생성 문제 평가 저장 |
| GET | `/feedback/question/{question_id}` | 특정 문제 평가 요약 |
| GET | `/feedback/summary` | 전체 문제 평가 요약 |
| GET | `/feedback/low-score-questions` | 품질 점수가 낮은 문제 조회 |
| GET | `/feedback/low-exam-relevance` | 시험 적합도가 낮은 문제 조회 |
| GET | `/feedback/recent-comments` | 최근 평가 의견 조회 |
| GET | `/feedback/admin-dashboard` | 문제 평가 운영 대시보드 |
| POST | `/rag-feedback/answer` | RAG 답변 평가 저장 |
| GET | `/rag-feedback/summary` | RAG 평가 요약 |
| GET | `/rag-feedback/recent` | 최근 RAG 평가 조회 |

### RAG

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/rag/index` | 문서 페이지 또는 텍스트 인덱싱 |
| POST | `/rag/ask` | 인덱싱된 문서 기반 질의응답 |
| GET | `/rag/documents` | 인덱싱된 문서 목록 조회 |
| DELETE | `/rag/documents` | 지정 문서의 Chroma chunk 삭제 |
| POST | `/rag-questions/generate` | 문서 기반 예상문제 생성 |
| POST | `/weakness-rag-questions/generate` | 오답 취약 개념과 문서 기반 문제 생성 |

### 시험과 분석

| Method | Endpoint | 설명 |
| --- | --- | --- |
| GET | `/exam-papers/questions` | 시험지에 사용할 문제 조회 |
| POST | `/exam-papers/generate` | Markdown 시험지 생성 |
| POST | `/exam-attempts/submit` | 전체 답안 채점 및 응시 결과 저장 |
| GET | `/exam-attempts/history` | 응시 기록 조회 |
| GET | `/exam-attempts/{attempt_id}` | 응시 상세 결과 조회 |
| GET | `/exam-attempts/analytics` | 점수 추이와 취약 개념 분석 |
| POST | `/study-reports/generate` | 개인 맞춤 학습 리포트 생성 |

### 목표·체크리스트·학습 세션

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/study-goals` | 학습 목표 생성 |
| GET | `/study-goals` | 학습 목표 조회 |
| GET | `/study-goals/{goal_id}/status` | 목표 진행 상태 조회 |
| POST | `/study-goals/strategy` | 목표 달성 전략 생성 |
| POST | `/study-checklists/generate` | 목표 기반 체크리스트 생성 |
| GET | `/study-checklists` | 체크리스트 조회 |
| PATCH | `/study-checklists/{item_id}` | 체크리스트 완료 상태 변경 |
| POST | `/study-sessions` | 학습 세션 기록 |
| GET | `/study-sessions` | 학습 세션 조회 |
| GET | `/study-sessions/summary` | 과목별 학습시간 요약 |
| POST | `/weekly-reports/generate` | 주간 학습 리포트 생성 |
| POST | `/goal-dashboard` | 목표별 통합 대시보드 생성 |

### 스마트 복습 큐

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/smart-review/queue/save` | 복습 큐 생성 및 저장 |
| GET | `/smart-review/queue/items` | 저장된 복습 큐 조회 |
| PATCH | `/smart-review/queue/items/{item_id}` | 복습 항목 완료 상태 변경 |

## 8. 제한 사항

### 사용자와 보안

- 회원가입, 로그인, 세션, 역할 기반 권한 관리가 없습니다.
- 사용자는 `user_name` 문자열로만 구분되므로 같은 이름을 입력하면 같은 기록에 접근할 수 있습니다.
- 평가 운영 대시보드에 별도의 관리자 인증이 없습니다.
- Docker Compose의 서비스 포트가 호스트에 노출됩니다. 외부 배포 시 방화벽, TLS, 인증, 비밀 관리가 필요합니다.
- 기본 PostgreSQL 비밀번호는 로컬 개발 편의를 위한 값이므로 실제 배포에서는 반드시 변경해야 합니다.

### AI 생성과 채점

- AI 결과는 비결정적이며 문제, 정답, 해설, 개념 태그와 채점 결과의 정확성을 보장하지 않습니다.
- 채점 결과는 교수자 또는 공식 채점 기준과 다를 수 있습니다.
- 오답 분석과 추천 품질은 생성된 `concept` 값과 누적 데이터의 품질에 크게 의존합니다.
- 리포트와 전략은 학습 보조 제안이며 성적 향상이나 목표 달성을 보장하지 않습니다.
- OpenAI API 사용량, 입력 길이, 모델 가용성 및 네트워크 상태의 영향을 받습니다.

### PDF와 RAG

- 텍스트가 포함된 PDF만 지원하며 스캔본 OCR은 지원하지 않습니다.
- 파일 크기 제한과 악성 PDF 전용 검증이 아직 없습니다.
- PDF 텍스트 추출 품질에 따라 페이지 정보와 검색 근거의 정확도가 달라질 수 있습니다.
- 한 번의 질의에서 여러 `material_id`를 조합해 선택하는 기능은 없습니다.
- RAG 문서 삭제는 Chroma의 chunk만 삭제하며 PostgreSQL의 `StudyMaterial`은 유지합니다.
- 표시되는 source는 검색된 페이지와 chunk 기준이며 답변 전체의 완전한 근거를 보장하지 않습니다.
- 유사한 chunk에서 비슷한 문제가 반복 생성될 수 있습니다.
- 저장된 사용자 평가는 현재 프롬프트나 모델을 자동 개선하는 학습 데이터로 연결되지 않습니다.

### 시험과 학습 관리

- 시험지는 Markdown만 지원하며 PDF 출력, 자동 배점, 제한 시간, 임시 저장, 보기 섞기는 지원하지 않습니다.
- 목표는 생성과 조회만 지원하며 수정, 삭제, 완료 처리는 지원하지 않습니다.
- 체크리스트는 완료 상태만 변경할 수 있으며 내용 수정과 삭제는 지원하지 않습니다.
- 학습 세션은 수동 입력 방식이며 자동 타이머, 수정, 삭제 기능은 없습니다.
- 집중도와 RAG 품질 평가는 사용자의 주관적 점수입니다.
- 주간·개인 학습 리포트와 목표 대시보드는 요청 시 생성되며 별도 결과물로 저장되지 않습니다.
- 스마트 복습 큐는 저장하고 수동 완료 처리할 수 있지만 자동 알림, 간격 반복 계산, 캘린더 연동은 없습니다.

### 운영과 품질 보증

- API는 동기 방식으로 AI, PDF 및 일부 DB 작업을 처리하므로 큰 요청이나 동시 사용자가 많을 때 지연될 수 있습니다.
- 요청 속도 제한, 백그라운드 작업 큐, 중앙 로그, 모니터링과 장애 알림이 없습니다.
- 현재 자동 테스트는 핵심 회귀 사례 중심이며 실제 PostgreSQL·Chroma·OpenAI를 연결한 통합 테스트와 브라우저 E2E 테스트는 없습니다.
- 날짜·시간은 timezone 정보가 없는 UTC 값으로 저장되므로 사용자별 시간대 표시는 별도 처리가 필요합니다.

## 9. 프로젝트 구조

```text
cs-exam-coach/
├─ backend/
│  ├─ alembic/              # DB migration
│  ├─ app/
│  │  ├─ core/config.py     # 환경 변수와 모델 설정
│  │  ├─ routers/           # FastAPI endpoint
│  │  ├─ ai_service.py      # AI 생성·채점·리포트
│  │  ├─ rag_service.py     # Chroma 인덱싱·검색·RAG
│  │  ├─ models.py          # SQLAlchemy model
│  │  ├─ schemas.py         # Pydantic request/response schema
│  │  ├─ database.py        # DB engine과 session
│  │  └─ main.py            # FastAPI 진입점
│  └─ tests/                # 회귀 테스트
├─ frontend/
│  └─ app.py                # Streamlit UI
├─ docs/images/             # README 화면 이미지
└─ docker-compose.yml
```

## 10. 기본 사용 흐름

1. 사용자 이름과 과목을 입력합니다.
2. 학습 내용을 직접 입력하거나 PDF에서 텍스트를 추출합니다.
3. 문제 유형, 난이도, 개수를 선택해 예상문제를 생성합니다.
4. 개별 문제를 풀거나 시험지를 구성해 모의시험에 응시합니다.
5. 채점 결과와 문항별 피드백을 확인합니다.
6. 오답 추천, 학습 목표, 체크리스트 또는 스마트 복습 큐로 다음 학습을 계획합니다.
7. 학습 세션을 기록하고 주간 리포트와 목표 대시보드에서 진행 상황을 확인합니다.

## 11. 화면 예시

### 메인 화면

![메인 화면](docs/images/main.png)

### 문제 생성

![문제 생성](docs/images/question-generation.png)

### 채점 결과

![채점 결과](docs/images/grading-result.png)

### 복습 추천

![복습 추천](docs/images/review-recommendation.png)
