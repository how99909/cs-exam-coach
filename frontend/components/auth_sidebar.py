import requests
import streamlit as st

from api import auth_api
from state import clear_auth_state


def validate_session() -> None:
    token = st.session_state.access_token
    
    if not token:
        return
    
    try:
        response = auth_api.get_me(token)
        
    except requests.RequestException as error:
        st.error(
            f"인증 서버에 연결할 수 없습니다: "
            f"{error}"
        )
        st.stop()
        
    if response.status_code == 200:
        user = response.json()["user"]
        
        st.session_state.user_name = user["user_name"]
        st.session_state.validated_access_token = token
        
        return
    
    if response.status_code in (401, 403):
        clear_auth_state()
        st.rerun()

    st.error("인증 서버 오류입니다. 잠시 후 다시 시도하세요.")
    st.stop()
    
    
def render_auth_sidebar() -> None:
    st.sidebar.header("사용자")
    
    if st.session_state.access_token:
        st.sidebar.write(f"로그인됨: {st.session_state.user_name}")
        
        if st.sidebar.button("로그아웃"):
            clear_auth_state()
            st.rerun()
            
        return
            
    auth_mode = st.sidebar.radio(
        "인증 메뉴",
        ["로그인", "회원가입"],
    )
    
    if auth_mode == "로그인":
        _render_login()
    else:
        _render_register()
        
        
def _render_login() -> None:
    user_name = st.sidebar.text_input("user_name", key="login_user_name")
    password = st.sidebar.text_input(
        "password", 
        type="password", 
        key="login_password",
    )
    
    if not st.sidebar.button("로그인"):
        return
    
    try:
        response = auth_api.login(
            user_name=user_name, 
            password=password
        )
    except requests.RequestException as error:
        st.sidebar.error(
            f"서버 연결 실패: {error}"
        )
        return
    
    if response.status_code == 200:
        result = response.json()
        
        st.session_state.access_token = result["access_token"]
        st.session_state.user_name = result["user_name"]
        st.session_state.validated_access_token = None
        
        st.rerun()
        
    st.sidebar.error("로그인 실패")
    st.sidebar.write(response.text)
    
    
def _render_register() -> None:
    user_name = st.sidebar.text_input("새 user_name", key="register_user_name")
    email = st.sidebar.text_input("email (선택)", key="register_email")
    password = st.sidebar.text_input(
        "새 password", 
        type="password", 
        key="register_password",
    )
    
    if not st.sidebar.button("회원가입"):
        return
    
    try:
        response = auth_api.register(
            user_name=user_name, 
            email=email or None, 
            password=password
        )
    except requests.RequestException as error:
        st.sidebar.error(
            f"서버 연결 실패: {error}"
        )
        return
    
    if response.status_code == 200:
        st.sidebar.success("회원가입 성공! 로그인 후 사용하세요.")
        return
        
    st.sidebar.error("회원가입 실패")
    st.sidebar.write(response.text)
