import streamlit as st
import pandas as pd

from api.client import ApiClient


def render_exam_paper(
    api: ApiClient,
) -> None:
    st.header("시험지 생성")
    st.caption("생성된 문제를 선택해 Markdown 시험지를 만듭니다.")
    
    exam_subject = st.selectbox(
        "시험지 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="exam_subject",
    )
    
    exam_limit = st.slider(
        "불러올 최근 문제 수",
        min_value=10,
        max_value=100,
        value=50,
        key="exam_limit",
    )
    
    if "exam_questions" not in st.session_state:
        st.session_state.exam_questions = []
        
    if st.button("시험제용 문제 목록 불러오기"):
        response = api.get(
            "/exam-papers/questions",
            params={
                "subject": exam_subject,
                "limit": exam_limit,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.exam_questions = result.get("questions", [])
            
            if not st.session_state.exam_questions:
                st.info("불러올 문제가 없습니다. 먼저 문제를 생성하세요.")
            else:
                st.success(f"{result['question_count']}개 문제를 불러왔습니다.")
        else:
            st.error("문제 목록을 불러오지 못했습니다.")
            st.write(response.text)
            
    if st.session_state.exam_questions:
        st.subheader("시험지에 넣을 문제 선택")
        
        selected_question_ids = []
        
        for question in st.session_state.exam_questions:
            label = (
                f"Q{question['id']} / {question['concept']} "
                f"/ {question['question_type']} / {question['difficulty']}"
            )
            
            checked = st.checkbox(
                label,
                key=f"exam_question_{question['id']}",
            )
            
            with st.expander(f"문제 미리보기 Q{question['id']}"):
                st.write(question["question"])
                st.caption(f"개념: {question['concept']}")
                
            if checked:
                selected_question_ids.append(question["id"])
                
        st.divider()
        
        exam_title = st.text_input(
            "시험지 제목",
            value=f"{exam_subject} 연습 시험지",
            key="exam_title",
        )
        
        include_answers = st.checkbox(
            "정답 포함",
            value=False,
            key="include_answers",
        )
        
        include_explanations = st.checkbox(
            "해설 포함",
            value=False,
            key="include_explanations",
        )
        
        if st.button("시험지 생성하기"):
            if not selected_question_ids:
                st.warning("시험지에 포함할 문제를 선택하세요.")
            else:
                response = api.post(
                    "/exam-papers/generate",
                    json={
                        "subject": exam_subject,
                        "question_ids": selected_question_ids,
                        "title": exam_title,
                        "include_answers": include_answers,
                        "include_explanations": include_explanations,
                    },
                    timeout=60,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        st.success("시험지가 생성되었습니다.")
                        
                        st.subheader("시험지 미리보기")
                        st.markdown(result["markdown"])
                        
                        st.download_button(
                            label="Markdown 시험지 다운로드",
                            data=result["markdown"],
                            file_name=f"{exam_title}.md",
                            mime="text/markdown",
                        )
                    else:
                        st.error(result.get("message", "시험지 생성 실패"))
                else:
                    st.error("시험지 생성 요청에 실패했습니다.")
                    st.write(response.text)
                    
                    
def render_exam_attempt(
    api: ApiClient,
) -> None:
    st.header("응시 모드")
    st.caption("생성된 문제를 실제 시험처럼 풀고 자동 채점합니다.")
    
    attempt_subject = st.selectbox(
        "응시 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="attempt_subject",
    )
    
    attempt_limit = st.slider(
        "불러올 최근 문제 수",
        min_value=5,
        max_value=50,
        value=20,
        key="attempt_limit",
    )
    
    if "attempt_questions" not in st.session_state:
        st.session_state.attempt_questions = []
        
    if st.button("응시할 문제 목록 불러오기"):
        response = api.get(
            "/exam-papers/questions",
            params={
                "subject": attempt_subject,
                "limit": attempt_limit,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.attempt_questions = result.get("questions", [])
            
            if not st.session_state.attempt_questions:
                st.info("응시할 문제가 없습니다. 먼저 문제를 생성하세요.")
            else:
                st.success(f"{result['question_count']}개 문제를 불러왔습니다.")
        else:
            st.error("문제 목록을 불러오지 못했습니다.")
            st.write(response.text)
        
    if st.session_state.attempt_questions:
        st.subheader("응시할 문제 선택")
        
        selected_attempt_questions = []
        
        for question in st.session_state.attempt_questions:
            checked = st.checkbox(
                f"Q{question['id']} / {question['concept']} / {question['difficulty']}",
                key=f"attempt_select_{question['id']}"
            )
            
            if checked:
                selected_attempt_questions.append(question)
                
        attempt_title = st.text_input(
            "응시 제목",
            value=f"{attempt_subject} 연습 응시",
            key="attempt_title",
        )
        
        st.divider()
        st.subheader("답안 입력")
        
        answer_payload = []
        
        for question in selected_attempt_questions:
            with st.expander(
                f"문제 Q{question['id']} / {question['concept']}",
                expanded=True,
            ):
                st.write(question["question"])
                
                user_answer = st.text_area(
                    "내 답안",
                    key=f"attempt_answer_{question['id']}",
                    height=120,
                )
                
                answer_payload.append(
                    {
                        "question_id": question["id"],
                        "user_answer": user_answer,
                    }
                )
                
        if st.button("응시 제출 및 자동 채점"):
            if not selected_attempt_questions:
                st.warning("응시할 문제를 선택하세요.")
            elif any(not item["user_answer"].strip() for item in answer_payload):
                st.warning("선택한 모든 문제의 답안을 입력하세요.")
            else:
                response = api.post(
                    "/exam-attempts/submit",
                    json={
                        "subject": attempt_subject,
                        "title": attempt_title,
                        "answers": answer_payload,
                    },
                    timeout=240,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("응시 결과가 저장되었습니다.")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("총 문항", result["total_questions"])
                    with col2:
                        st.metric("정답 수", result["correct_count"])
                    with col3:
                        st.metric("점수", result["score"])
                        
                    st.subheader("문항별 채점 결과")
                    
                    for item in result["results"]:
                        status = "정답" if item["is_correct"] else "오답"
                        
                        with st.expander(
                            f"Q{item['question_id']} / {status} / {item['concept']}"
                        ):
                            st.write("문제")
                            st.write(item["question"])
                            
                            st.write("내 답안")
                            st.write(item["user_answer"])
                            
                            st.write("모범답안")
                            st.write(item["correct_answer"])
                            
                            st.write("피드백")
                            st.write(item["feedback"])
                else:
                    st.error("응시 제출에 실패했습니다.")
                    st.write(response.text)
                    
    st.divider()
    st.subheader("최근 응시 기록")
    
    if st.button("내 응시 기록 불러오기"):
        response = api.get(
            "/exam-attempts/history",
            params={
                "subject": attempt_subject,
                "limit": 20,
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if not result.get("attempts"):
                st.info("응시 기록이 없습니다.")
            else:
                for attempt in result["attempts"]:
                    with st.expander(
                        f"{attempt['title']} / {attempt['score']}점 / {attempt['created_at']}"
                    ):
                        st.write(f"과목: {attempt['subject']}")
                        st.write(f"총 문항: {attempt['total_questions']}")
                        st.write(f"정답 수: {attempt['correct_count']}")
                        st.write(f"점수: {attempt['score']}")
        else:
            st.error("응시 기록을 불러오지 못했습니다.")
            st.write(response.text)
            
            
def render_exam_analytics(
    api: ApiClient,
) -> None:
    st.header("응시 결과 분석")
    st.caption("누적된 응시 기록을 기반으로 점수 변화와 취약 개념을 분석합니다.")
    
    analytics_subject = st.selectbox(
        "분석할 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="analytics_subject",
    )
    
    analytics_limit = st.slider(
        "분석할 최근 응시 기록 수",
        min_value=
        5,
        max_value=50,
        value=20,
        key="analytics_limit",
    )
    
    if st.button("응시 분석 불러오기"):
        params = {
            "limit": analytics_limit,
        }
        
        if analytics_subject != "전체":
            params["subject"] = analytics_subject
            
        response = api.get(
            "/exam-attempts/analytics",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("attempt_count", 0) == 0:
                st.info(result.get("message", "응시 기록이 없습니다."))
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("분석 응시 수", result["attempt_count"])
                with col2:
                    st.metric("평균 점수", result["average_score"])
                with col3:
                    st.metric("최근 점수", result["latest_score"])
                    
                st.subheader("최근 점수 변화")
                
                score_trend = result.get("score_trend", [])
                
                if score_trend:
                    trend_df = pd.DataFrame(score_trend)
                    st.line_chart(
                        trend_df,
                        x="created_at",
                        y="score",
                    )
                    
                    st.dataframe(
                        trend_df[
                            [
                                "attempt_id",
                                "title",
                                "subject",
                                "score",
                                "correct_count",
                                "total_questions",
                                "created_at",
                            ]
                        ],
                        use_container_width=True,
                    )
                    
                st.subheader("취약 개념 랭킹")
                
                weak_concepts = result.get("weak_concepts", [])
                
                if not weak_concepts:
                    st.info("최근 응시 기록에서 오답 개념이 없습니다.")
                else:
                    for index, item in enumerate(weak_concepts, start=1):
                        st.write(
                            f"{index}. {item['concept']} - 오답 {item['wrong_count']}회"
                        )
                        
                st.subheader("과목별 응시 요약")
                
                subject_summary = result.get("subject_summary", [])
                
                if subject_summary:
                    subject_df = pd.DataFrame(subject_summary)
                    st.dataframe(subject_df, use_container_width=True)
                else:
                    st.info("과목별 요약 데이터가 없습니다.")
        else:
            st.error("응시 분석을 불러오지 못했습니다.")
            st.write(response.text)