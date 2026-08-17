import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database import get_db
from app.main import APP_VERSION
from app.routers import exam_attempts
from app.schemas import QuestionGenerateRequest, StudySessionCreateRequest


class EmptyQuery:
    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def all(self):
        return []


class EmptyDatabase:
    def query(self, *args, **kwargs):
        return EmptyQuery()


def empty_database_override():
    yield EmptyDatabase()


class ApiRegressionTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI(version=APP_VERSION)
        app.include_router(exam_attempts.router)
        app.dependency_overrides[get_db] = empty_database_override
        self.client = TestClient(app)

    def test_analytics_is_not_captured_as_attempt_id(self):
        response = self.client.get(
            "/exam-attempts/analytics",
            params={"user_name": "tester"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attempt_count"], 0)

    def test_query_limit_is_bounded(self):
        response = self.client.get(
            "/exam-attempts/history",
            params={"user_name": "tester", "limit": 0},
        )

        self.assertEqual(response.status_code, 422)


class SchemaValidationTests(unittest.TestCase):
    def test_question_count_is_bounded(self):
        with self.assertRaises(ValidationError):
            QuestionGenerateRequest(subject="os", content="content", count=0)

    def test_study_session_values_are_bounded(self):
        with self.assertRaises(ValidationError):
            StudySessionCreateRequest(
                subject="os",
                duration_minutes=0,
                content="review",
                focus_score=6,
            )


if __name__ == "__main__":
    unittest.main()
