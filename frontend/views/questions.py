import streamlit as st

from api.client import ApiClient


def render_questions(
    api: ApiClient,
) -> None:
    st.header("문제 생성")
    
    subject = st.selectbox(
        "과목을 선택하세요",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍"],
    )

    question_type = st.selectbox(
        "문제 유형을 선택하세요",
        ["short_answer", "multiple_choice", "coding", "true_false", "fill_in_the_blank", "essay"],
    )
    
    difficulty = st.selectbox(
        "난이도를 선택하세요",
        ["easy", "medium", "hard", "exam_like"],
    )

    count = st.slider("생성할 문제 수", min_value=1, max_value=10, value=5)

    content = st.text_area(
        "공부 내용을 입력하세요", 
        height=250,
        placeholder="강의자료, 필기, 교재 요약 내용을 붙여넣으세요.",
    )

    if "questions" not in st.session_state:
        st.session_state.questions = []
        
    if st.button("문제 생성하기"):
        _generate_questions(
            api=api,
            subject=subject,
            content=content,
            question_type=question_type,
            count=count,
            difficulty=difficulty,
        )
        
    _render_generated_questions(api)
    
    
def _generate_questions(
    api,
    *,
    subject,
    content,
    question_type,
    count,
    difficulty,
):
    if not content.strip():
        st.warning("공부 내용을 입력해주세요.")
        return
    
    response = api.post(
        "/questions/generate", 
        json={
            "subject": subject,
            "content": content,
            "question_type": question_type,
            "count": count,
            "difficulty": difficulty,
        },
        timeout=60,
    )
    
    if response.status_code == 200:
        st.session_state.questions = response.json()["questions"]
        st.success("문제가 생성되었습니다.")
        return
        
    st.error("문제 생성에 실패했습니다.")
    st.write(response.text)
    
    st.divider()
    
    
def _render_generated_questions(api):
    if st.session_state.questions:
        st.header("생성된 문제")
        
        for idx, question in enumerate(st.session_state.questions, start=1):
            st.subheader(f"문제 {idx}")
            st.write(question["question_text"])
            
            user_answer = st.text_area(
                f"문제 {idx}에 대한 답변을 입력하세요", 
                key=f"user_answer_{idx}",
            )
            
            with st.expander("모범 답안 보기"):
                st.write(question["answer"])
                st.write(question["explanation"])
            
            if st.button(f"답안 제출하기 (문제 {idx})"):
                question_id = question.get("question_id", question.get("id"))

                if question_id is None:
                    st.error("문제 ID를 찾을 수 없습니다. 문제를 다시 생성해 주세요.")
                    st.stop()

                response = api.post(
                    "/grading/grade",
                    json={
                        "question_id": question_id,
                        "user_answer": user_answer,
                    },
                    timeout=60,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["is_correct"]:
                        st.success("정답입니다!")
                    else:
                        st.error("오답입니다.")
                    
                    st.write(result["feedback"])
                else:
                    st.error("채점에 실패했습니다.")
                    st.write(response.text)
                    
            st.markdown("### 문제 평가")
            
            quality_score = st.slider(
                f"문제 {idx}의 문제 품질 점수 (1~5)", 
                min_value=1, 
                max_value=5, 
                value=3,
                key=f"quality_score_{idx}",
            )
            
            explanation_score = st.slider(
                f"문제 {idx}의 해설 품질 점수 (1~5)", 
                min_value=1,
                max_value=5,
                value=3,
                key=f"explanation_score_{idx}",
            )
            
            exam_relevance_score = st.slider(
                f"문제 {idx}의 시험 적합성 점수 (1~5)",
                min_value=1,
                max_value=5,
                value=3,
                key=f"exam_relevance_score_{idx}",
            )
            
            difficulty_match_score = st.slider(
                f"문제 {idx}의 난이도 적합성 점수 (1~5)",
                min_value=1,
                max_value=5,
                value=3,
                key=f"difficulty_match_score_{idx}",
            )
            
            comment = st.text_area(
                f"문제 {idx}에 대한 평가 코멘트",
                key=f"feedback_comment_{idx}",
                placeholder="문제 품질, 해설, 시험 적합성, 난이도 적합성 등에 대한 코멘트를 작성하세요.",
            )
            
            if st.button(f"문제 평가 제출하기 (문제 {idx})"):
                response = api.post(
                    "/feedback/question",
                    json={
                        "question_id": question["question_id"],
                        "quality_score": quality_score,
                        "explanation_score": explanation_score,
                        "exam_relevance_score": exam_relevance_score,
                        "difficulty_match_score": difficulty_match_score,
                        "comment": comment,
                    },
                    timeout=30,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        st.success("문제 평가가 저장되었습니다.")
                    else:
                        st.error(result.get("message", "문제 평가 저장에 실패했습니다."))
                else:
                    st.error("문제 평가 요청에 실패했습니다.")
                    st.write(response.text)
                    
    st.divider()