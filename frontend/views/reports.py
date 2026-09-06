import streamlit as st

from api.client import ApiClient


def render_study_report(
    api: ApiClient,
) -> None:
    st.header("개인 맞춤 학습 리포트")
    st.caption("응시 기록과 오답 개념을 바탕으로 AI가 학습 전략을 제안합니다.")
    
    report_subject = st.selectbox(
        "리포트 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="report_subject",
    )
    
    report_limit = st.slider(
        "분석할 최근 응시 기록 수",
        min_value=5,
        max_value=50,
        value=20,
        key="report_limit",
    )
    
    if st.button("개인 맞춤 학습 리포트 생성하기"):
        payload = {
            "limit": report_limit,
        }
        
        if report_subject != "전체":
            payload["subject"] = report_subject
            
        response = api.post(
            "/study-reports/generate",
            json=payload,
            timeout=180,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            st.success("학습 리포트가 생성되었습니다.")
            
            summary = result["attempt_summary"]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("응시 수", summary["attempt_count"])
            with col2:
                st.metric("평균 점수", summary["average_score"])
            with col3:
                st.metric("최근 점수", summary["latest_score"])
            with col4:
                st.metric("최고 점수", summary["best_score"])
                
            st.subheader("취약 개념")
            weak_concepts = result.get("weak_concept", [])
            
            if not weak_concepts:
                st.info("오답 기반 취약 개념이 없습니다.")
            else:
                for item in weak_concepts:
                    st.write(f"- {item['concept']}: 오답 {item['wrong_count']}회")
                    
            st.subheader("AI 학습 리포트")
            st.markdown(result["report"])
            
            st.download_button(
                label="학습 리포트 Markdown 다운로드",
                data=result["report"],
                file_name="study_report.md",
                mime="text/markdown",
            )
        else:
            st.error("학습 리포트 생성에 실패했습니다.")
            st.write(response.text)
            
            
def render_weekly_report(
    api: ApiClient,
) -> None:
    st.header("주간 학습 리포트")
    st.caption("최근 학습 세션, 응시 기록, 체크리스트를 종합해 주간리포트를 생성합니다.")
    
    weekly_subject = st.selectbox(
        "리포트 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="weakly_subject",
    )
    
    weekly_days = st.slider(
        "분석 기간",
        min_value=1,
        max_value=31,
        value=7,
        key="weekly_days",
    )
    
    if st.button("주간 학습 리포트 생성하기"):
        payload = {
            "days": weekly_days,
        }
        
        if weekly_subject != "전체":
            payload["subject"] = weekly_subject
            
        response = api.post(
            "/weekly-reports/generate",
            json=payload,
            timeout=180,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            st.success("주간 학습 리포트가 생성되었습니다.")
            
            session_summary = result["session_summary"]
            attempt_summary = result["attempt_summary"]
            checklist_summary = result["checklist_summary"]
            
            st.subheader("주간 요약")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("학습 세션", session_summary["session_count"])
            with col2:
                st.metric("총 공부 시간", f"{session_summary['total_hours']}시간")
            with col3:
                st.metric("응시 횟수", attempt_summary["attempt_count"])
            with col4:
                st.metric("체크리스트 진행률", f"{checklist_summary['progress_rate']}%")
                
            col5, col6, col7 = st.columns(3)
            
            with col5:
                st.metric("평균 집중도", session_summary["avg_focus_score"])
            with col6:
                st.metric("평균 점수", attempt_summary["avg_score"])
            with col7:
                st.metric("최근 점수", attempt_summary["latest_score"])
                
            st.subheader("취약 개념")
            weak_concepts = result.get("weak_concepts", [])
            
            if not weak_concepts:
                st.info("이번 기간의 오답 기반 취약 개념이 없습니다.")
            else:
                for item in weak_concepts:
                    st.write(f"- {item['concept']}: 오답 {item['wrong_count']}회")
                    
            st.subheader("AI 주간 학습 리포트")
            st.markdown(result["report"])
            
            st.download_button(
                label="주간 리포트 Markdown 다운로드",
                data=result["report"],
                file_name="weekly_study_report.md",
                mime="text/markdown",
            )
        else:
            st.error("주간 리포트 생성에 실패했습니다.")
            st.write(response.text)