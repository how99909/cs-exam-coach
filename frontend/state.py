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
    # Cached documents, answers and widget values belong to the signed-in user.
    for key in list(st.session_state):
        del st.session_state[key]
    init_session_state()
