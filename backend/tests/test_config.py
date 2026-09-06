import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize("secret", [None, "", "   ", "replace-with-a-long-random-secret"])
def test_jwt_secret_must_be_configured(monkeypatch, secret):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    if secret is None:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("JWT_SECRET_KEY", secret)
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        runpy.run_path(str(Path(__file__).parents[1] / "app/core/config.py"))


def test_config_accepts_explicit_secret(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-explicit-secret")
    config = runpy.run_path(str(Path(__file__).parents[1] / "app/core/config.py"))
    assert config["settings"].JWT_SECRET_KEY == "test-only-explicit-secret"
