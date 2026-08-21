import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.routers import auth


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine)

        def override_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        test_app = FastAPI()
        test_app.include_router(auth.router)
        test_app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(test_app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def test_register_login_and_me(self):
        register = self.client.post(
            "/auth/register",
            json={
                "user_name": "auth_tester",
                "email": "auth@example.com",
                "password": "password123",
            },
        )
        self.assertEqual(register.status_code, 200)

        login = self.client.post(
            "/auth/login",
            json={"user_name": "auth_tester", "password": "password123"},
        )
        self.assertEqual(login.status_code, 200)

        me = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["user_name"], "auth_tester")

    def test_missing_invalid_and_wrong_credentials_are_rejected(self):
        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.assertEqual(
            self.client.get(
                "/auth/me",
                headers={"Authorization": "Bearer invalid"},
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/auth/login",
                json={"user_name": "auth_tester", "password": "wrong-password"},
            ).status_code,
            401,
        )


if __name__ == "__main__":
    unittest.main()
