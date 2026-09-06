import streamlit as st

from api.client import ApiClient


def render_home(
    api: ApiClient,
) -> None:
    st.header("홈 대시보드")
    st.caption("오늘의 학습 상태와 우선순위를 한눈에 확인합니다.")
    
    home_subject = st.selectbox(
        "홈 대시보드 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="home_subject",
    )
    
    if not st.button("홈 대시보드 불러오기"):
        return
    
    payload = {}
    
    if home_subject != "전체":
        payload["subject"] = home_subject
        
    response = api.post(
        "/home-dashboard",
        json=payload,
        timeout=180,
    )
    
    if response.status_code != 200:
        st.error("홈 대시보드를 불러오지 못했습니다.")
        st.write(response.text)
        return
    
    result = response.json()
    
    st.success("홈 대시보드가 생성되었습니다.")
    
    goal_summary = result["goal_summary"]
    session_summary = result["session_summary"]
    attempt_summary = result["attempt_summary"]
    review_queue_summary = result["review_queue_summary"]
    checklist_summary = result["checklist_summary"]
    
    st.subheader("오늘의 핵심 지표")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if goal_summary:
            st.metric("가까운 목표 D-Day", f"D-{goal_summary['days_left']}")
        else:
            st.metric("가까운 목표", "없음")
            
    with col2:
        st.metric("최근 7일 학습 시간", f"{session_summary['total_hours']}시간")
        
    with col3:
        st.metric("최근 점수", attempt_summary["latest_score"])
        
    with col4:
        st.metric("복습 큐 완료율", f"{review_queue_summary['progress_rate']}%")
        
    st.subheader("목표 요약")
    
    if goal_summary:
        st.write(f"**목표:** {goal_summary['title']}")
        st.write(f"**과목:** {goal_summary['subject']}")
        st.write(f"**목표 점수:** {goal_summary['target_score']}점")
        st.write(f"**시험 날짜:** {goal_summary['exam_date']}")
    else:
        st.info("등록된 학습 목표가 없습니다.")
        
    st.subheader("실행 현황")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("학습 세션 수", session_summary["session_count"])
    with col6:
        st.metric(
            "평균 집중도", 
            session_summary["avg_focus_score"] 
            if session_summary["avg_focus_score"] is not None 
            else "-"
        )
    with col7:
        st.metric("체크리스트 진행률", f"{checklist_summary['progress_rate']}%")
    with col8:
        st.metric("최근 7일 응시 수", attempt_summary["attempt_count"])
        
    st.subheader("오늘 남은 복습 큐")
    
    pending_items = review_queue_summary.get("pending_items", [])
    
    if not pending_items:
        st.info("미완료 복습 큐가 없습니다.")
    else:
        for item in pending_items:
            st.write(
                f"- P{item['priority']} / {item['title']} "
                f"({item['estimated_minutes']}분)"
            )
            
    st.subheader("취약 개념 Top 5")
    
    weak_concepts = result.get("weak_concepts", [])
    
    if not weak_concepts:
        st.info("취약 개념 데이터가 없습니다.")
    else:
        for item in weak_concepts:
            st.write(f"- {item['concept']}: 오답 {item['wrong_count']}회")
            
    st.subheader("AI 오늘의 학습 코멘트")
    st.markdown(result["comment"])
    
    st.download_button(
        label="오늘의 학습 코멘트 다운로드",
        data=result["comment"],
        file_name="home_dashboard_comment.md",
        mime="text/markdown",
    )