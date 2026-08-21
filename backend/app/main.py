from fastapi import FastAPI

from app.routers import (
    exam_papers,
    feedback,
    grading,
    history,
    materials,
    questions,
    rag,
    rag_feedback,
    rag_questions,
    review,
    weakness_rag_questions,
    exam_attempts,
    study_reports,
    study_goals,
    study_checklists,
    study_sessions,
    weekly_reports,
    goal_dashboard,
    smart_review,
    home_dashboard,
    auth
)

# Base.metadata.create_all(bind=engine)

APP_VERSION = "0.4.3"

app = FastAPI(
    title="CS Exam Coach API",
    description="컴소 전공 시험 대비 AI 문제 생성 및 오답 복습 API",
    version=APP_VERSION,
)

app.include_router(questions.router)
app.include_router(grading.router)
app.include_router(review.router)
app.include_router(history.router)
app.include_router(materials.router)
app.include_router(feedback.router)
app.include_router(rag.router)
app.include_router(rag_feedback.router)
app.include_router(rag_questions.router)
app.include_router(weakness_rag_questions.router)
app.include_router(exam_papers.router)
app.include_router(exam_attempts.router)
app.include_router(study_reports.router)
app.include_router(study_goals.router)
app.include_router(study_checklists.router)
app.include_router(study_sessions.router)
app.include_router(weekly_reports.router)
app.include_router(goal_dashboard.router)
app.include_router(smart_review.router)
app.include_router(home_dashboard.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to the CS Exam Coach API!",
        "version": APP_VERSION,
    }
