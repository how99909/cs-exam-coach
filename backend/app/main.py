from fastapi import FastAPI

from app.routers import questions, grading, review, history, materials, feedback
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CS Exam Coach API",
    description="컴소 전공 시험 대비 AI 문제 생성 및 오답 복습 API",
    version="0.1.8",
)

app.include_router(questions.router)
app.include_router(grading.router)
app.include_router(review.router)
app.include_router(history.router)
app.include_router(materials.router)
app.include_router(feedback.router)

@app.get("/")
def root():
    return {"message": "Welcome to the CS Exam Coach API!"}