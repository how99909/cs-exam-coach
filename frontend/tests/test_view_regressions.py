from unittest.mock import Mock
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from api.client import ApiClient
from api import auth_api


def test_authenticated_app_renders_all_tabs(monkeypatch):
    monkeypatch.setattr(auth_api, "get_me", Mock(return_value=Mock(
        status_code=200, json=lambda: {"user": {"user_name": "test-user"}})))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
    app.session_state["access_token"] = "test-token"
    app.run(timeout=20)
    assert not app.exception
    assert len(app.tabs) == 23


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_rag_feedback_uses_last_answer(monkeypatch):
    post = Mock(return_value=Mock(status_code=200, json=lambda: {"success": True}))
    monkeypatch.setattr(ApiClient, "post", post)
    app = AppTest.from_string('''
from views.rag import render_rag_qa
from api.client import ApiClient
render_rag_qa(ApiClient())
''')
    app.session_state["last_rag_subject"] = "algorithms"
    app.session_state["last_rag_material_id"] = 42
    app.session_state["last_rag_question"] = "Explain BFS"
    app.session_state["last_rag_answer"] = "Breadth first search"
    app.run()
    button(app, "RAG 답변 평가 저장").click().run()
    assert not app.exception
    payload = post.call_args.kwargs["json"]
    assert payload["material_id"] == 42
    assert payload["subject"] == "algorithms"
    assert payload["question"] == "Explain BFS"
    assert payload["answer"] == "Breadth first search"


def test_checklist_load_and_save(monkeypatch):
    item = dict(id=7, title="Review BFS", description="Trace a graph", subject="알고리즘",
                goal_id=1, priority=1, is_done=False)
    monkeypatch.setattr(ApiClient, "get", Mock(return_value=Mock(
        status_code=200, json=lambda: dict(items=[item], total_count=1, done_count=0, progress_rate=0))))
    patch = Mock(return_value=Mock(status_code=200))
    monkeypatch.setattr(ApiClient, "patch", patch)
    app = AppTest.from_string('''
from views.study import render_study_checklists
from api.client import ApiClient
render_study_checklists(ApiClient())
''').run()
    button(app, "체크리스트 불러오기").click().run()
    assert not app.exception
    app.checkbox[0].check().run()
    button(app, "상태 저장 item_id=7").click().run()
    assert not app.exception
    assert patch.call_args.args == ("/study-checklists/7",)
    assert patch.call_args.kwargs["json"] == {"is_done": True}


def test_logout_removes_previous_users_data():
    app = AppTest.from_string('''
import streamlit as st
from state import clear_auth_state
clear_auth_state()
''')
    app.session_state["questions"] = ["private question"]
    app.session_state["pdf_extracted_text"] = "private document"
    app.session_state["login_password"] = "private password"
    app.run()
    assert not app.exception
    assert app.session_state.filtered_state == {
        "access_token": None, "validated_access_token": None, "user_name": "default_user"}


@pytest.mark.parametrize("status", [401, 503])
def test_session_rechecks_token_and_preserves_state_on_server_error(monkeypatch, status):
    get_me = Mock(return_value=Mock(status_code=status))
    monkeypatch.setattr(auth_api, "get_me", get_me)
    app = AppTest.from_string('''
from state import init_session_state
from components.auth_sidebar import validate_session
init_session_state()
validate_session()
''')
    app.session_state["access_token"] = "previously-validated"
    app.session_state["validated_access_token"] = "previously-validated"
    app.session_state["pdf_extracted_text"] = "private document"
    app.run()
    assert not app.exception
    get_me.assert_called_once_with("previously-validated")
    assert app.session_state["access_token"] == (None if status == 401 else "previously-validated")
