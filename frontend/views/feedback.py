import streamlit as st

from api.client import ApiClient


def render_question_feedback(
    api: ApiClient
) -> None:
    st.header("문제 평가 요약")
        
    if st.button("내 평가 요약 불러오기"):
        response = api.get(
            "/feedback/summary",
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("feedback_count", 0) == 0:
                st.info(result.get("message", "아직 평가 데이터가 없습니다."))
            else:
                st.metric("평가 수", result["feedback_count"])
                st.metric("평균 문제 품질", result['avg_quality_score'])
                st.metric("평균 해설 품질", result['avg_explanation_score'])
                st.metric("평균 시험 적합성", result['avg_exam_relevance_score'])
                st.metric("평균 난이도 적합성", result['avg_difficulty_match_score'])
        else:
            st.error("문제 평가 요약을 가져오는데 실패했습니다.")
            st.write(response.text)
    
    
def render_feedback_dashboard(
    api: ApiClient,
) -> None:
    st.header("문제 품질 대시보드")
    st.caption("평가를 기반으로 AI 생성 문제의 품질을 확인합니다.")
    
    response = None
    if st.button("관리자 대시보드 불러오기"):
        response = api.get(
            "/feedback/admin-dashboard",
            timeout=30,
        )
        
    if response is not None and response.status_code == 200:
        data = response.json()
        
        if data.get("feedback_count", 0) == 0:
            st.info(data.get("message", "아직 평가 데이터가 없습니다."))
        else:
            st.subheader("전체 평가 요약")
            
            summary = data["summary"]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("평가 수", data["feedback_count"])
            with col2:
                st.metric("문제 품질", summary["avg_quality_score"])
            with col3:
                st.metric("해설 품질", summary["avg_explanation_score"])
            with col4:
                st.metric("시험 적합도", summary["avg_exam_relevance_score"])
            with col5:
                st.metric("난이도 적절성", summary["avg_difficulty_match_score"])
                
            st.divider()

            st.subheader("문제 품질 낮은 문제")

            if not data["low_score_questions"]:
                st.info("문제 품질 점수가 낮은 문제가 없습니다.")
            else:
                for item in data["low_score_questions"]:
                    with st.expander(f"Question ID: {item['question_id']}"):
                        st.write(f"평가 수: {item['feedback_count']}")
                        st.write(f"평균 문제 품질: {item['avg_quality_score']}")
                        st.write(f"평균 해설 품질: {item['avg_explanation_score']}")
                        st.write(f"평균 시험 적합도: {item['avg_exam_relevance_score']}")
                        st.write(f"평균 난이도 적절성: {item['avg_difficulty_match_score']}")

            st.subheader("시험 적합도 낮은 문제")

            if not data["low_exam_relevance_questions"]:
                st.info("시험 적합도 점수가 낮은 문제가 없습니다.")
            else:
                for item in data["low_exam_relevance_questions"]:
                    with st.expander(f"Question ID: {item['question_id']}"):
                        st.write(f"평가 수: {item['feedback_count']}")
                        st.write(f"평균 문제 품질: {item['avg_quality_score']}")
                        st.write(f"평균 해설 품질: {item['avg_explanation_score']}")
                        st.write(f"평균 시험 적합도: {item['avg_exam_relevance_score']}")
                        st.write(f"평균 난이도 적절성: {item['avg_difficulty_match_score']}")

            st.subheader("최근 사용자 코멘트")

            if not data["recent_comments"]:
                st.info("최근 코멘트가 없습니다.")
            else:
                for comment in data["recent_comments"]:
                    with st.expander(
                        f"{comment['user_name']} / Question ID: {comment['question_id']}"
                    ):
                        st.write(f"문제 품질: {comment['quality_score']}")
                        st.write(f"해설 품질: {comment['explanation_score']}")
                        st.write(f"시험 적합도: {comment['exam_relevance_score']}")
                        st.write(f"난이도 적절성: {comment['difficulty_match_score']}")
                        st.write("코멘트")
                        st.write(comment["comment"])
                        st.caption(f"작성 시간: {comment['created_at']}")
    elif response is not None:
        st.error("관리자 대시보드를 불러오지 못했습니다.")
        st.write(response.text)
    
    
def render_rag_feedback(
    api: ApiClient
) -> None:
    st.header("RAG 답변 평가 요약")
        
    rag_feedback_subject = st.selectbox(
        "평가 요약 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="rag_feedback_subject",
    )
    
    params = {}
    
    if rag_feedback_subject != "전체":
        params["subject"] = rag_feedback_subject
        
    if st.button("내 RAG 평가 요약 불러오기"):
        response = api.get(
            "/rag-feedback/summary",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("feedback_count", 0) == 0:
                st.info(result.get("message", "아직 RAG 답변 평가 데이터가 없습니다."))
            else:
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("평가 수", result["feedback_count"])
                with col2:
                    st.metric("답변 정확도", result["avg_accuracy_score"])
                with col3:
                    st.metric("근거 충분성", result["avg_grounding_score"])
                with col4:
                    st.metric("출처 적합성", result["avg_source_relevance_score"])
                with col5:
                    st.metric("도움 여부", result["avg_helpfulness_score"])
        else:
            st.error("RAG 평가요약을 불러오지 못했습니다.")
            st.write(response.text)
            
    if st.button("최근 RAG 평가 코멘트 불러오기"):
        response = api.get(
            "/rag-feedback/recent",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            items = response.json()
            
            if not items:
                st.info("최근 RAG 평가 코멘트가 없습니다.")
            else:
                for item in items:
                    with st.expander(
                        f"{item['subject']} / material_id={item['material_id']} / {item['created_at']}"
                    ):
                        st.write("질문")
                        st.write(item["question"])
                        
                        st.write("점수")
                        st.write(f"- 답변 정확도: {item['accuracy_score']}")
                        st.write(f"- 근거 충분성: {item['grounding_score']}")
                        st.write(f"- 출처 적합성: {item['source_relevance_score']}")
                        st.write(f"- 도움 여부: {item['helpfulness_score']}")
                        
                        if item["comment"]:
                            st.write("코멘트")
                            st.write(item["comment"])
        else:
            st.error("최근 RAG 평가를 불러오지 못했습니다.")
            st.write(response.text)