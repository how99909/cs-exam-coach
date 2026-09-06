import streamlit as st


def init_session_state() -> None:
    defaults = {
        "access_token": None,
        "validated_access_token": None,
        "user_name": "default_user",
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
            
def clear_auth_state() -> None:
    st.session_state.access_token = None
    st.session_state.validated_access_token = None
    st.session_state.user_name = "default_user"