import streamlit as st
import pandas as pd

from api.client import ApiClient
from components.auth_sidebar import validate_session, render_auth_sidebar
from state import init_session_state
from views.home import render_home
from views.questions import render_questions
from views.materials import render_materials
from views.rag import render_rag_qa, render_rag_documents, render_rag_questions, render_weakness_rag_questions
from views.exams import render_exam_paper, render_exam_attempt, render_exam_analytics
from views.study import render_study_goals, render_goal_dashboard, render_smart_review, render_study_checklists, render_study_sessions
from views.reports import render_study_report, render_weekly_report
from views.review import render_review_recommendations, render_learning_history, render_study_plan
from views.feedback import render_feedback_dashboard, render_question_feedback, render_rag_feedback


st.set_page_config(
    page_title="CS Exam Coach", 
    page_icon="📚", 
    layout="wide",
)

init_session_state()
validate_session()
render_auth_sidebar()

st.title("📚 CS Exam Coach")
st.write("컴소 전공 시험 대비 AI 문제 생성 및 오답 복습 서비스")

if not st.session_state.access_token:
    st.info("CS Exam Coach를 사용하려면 로그인하거나 회원가입하세요.")
    st.stop()
    
api = ApiClient(access_token=st.session_state.access_token)

tab_home, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21, tab22 = st.tabs(
    [
        "홈",
        "문제 생성",
        "PDF 업로드",
        "RAG 질의응답",
        "RAG 문서 관리",
        "RAG 문제 생성",
        "약점 RAG 문제",
        "시험지 생성",
        "응시 모드",
        "응시 분석",
        "학습 리포트",
        "학습 목표",
        "목표 대시보드",
        "스마트 복습 큐",
        "학습 체크리스트",
        "학습 세션",
        "주간 리포트",
        "복습 추천",
        "학습 기록",
        "시험 계획",
        "문제 평가",
        "관리자 대시보드",
        "RAG 평가",
    ]
)

with tab_home:
    render_home(api)
    

with tab1:
    render_questions(api)
    
    
with tab2:
    render_materials(api)
    

with tab3:
    render_rag_qa(api)


with tab4:
    render_rag_documents(api)


with tab5:
    render_rag_questions(api)
    

with tab6:
    render_weakness_rag_questions(api)


with tab7:
    render_exam_paper(api)


with tab8:
    render_exam_attempt(api)


with tab9:
    render_exam_analytics(api)
    

with tab10:
    render_study_report(api)
    

with tab11:
    render_study_goals(api)
    

with tab12:
    render_goal_dashboard(api)


with tab13:
    render_smart_review(api)
    

with tab14:
    render_study_checklists(api)
    

with tab15:
    render_study_sessions(api)
    

with tab16:
    render_weekly_report(api)
    

with tab17:
    render_review_recommendations(api)
    

with tab18:
    render_learning_history(api)
    
            
with tab19:
    render_study_plan(api)
    
            
with tab20:
    render_question_feedback(api)
    
          
with tab21:
    render_feedback_dashboard(api)
    
        
with tab22:
    render_rag_feedback(api)        
