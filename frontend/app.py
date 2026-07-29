import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="CS Exam Coach", 
    page_icon="📚", 
    layout="wide",
)

st.title("📚 CS Exam Coach")
st.write("컴소 전공 시험 대비 AI 문제 생성 및 오답 복습 서비스")

subject = st.selectbox(
    "과목을 선택하세요",
    ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍"],
)

question_type = st.selectbox(
    "문제 유형을 선택하세요",
    ["short_answer", "multiple_choice", "coding", "true_false", "fill_in_the_blank", "essay"],
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
    if not content.strip():
        st.warning("공부 내용을 입력해주세요.")
    else:
        response = requests.post(
            f"{API_BASE_URL}/questions/generate", 
            json={
                "subject": subject,
                "content": content,
                "question_type": question_type,
                "count": count,
            },
            timeout=60,
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.questions = data["questions"]
            st.success("문제가 생성되었습니다.")
        else:
            st.error("문제 생성에 실패했습니다.")
            st.write(response.text)
            
st.divider()

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
            response = requests.post(
                f"{API_BASE_URL}/grading/grade",
                json={
                    "question_text": question["question_text"],
                    "correct_answer": question["answer"],
                    "user_answer": user_answer,
                    "concept_tag": question.get("concept_tag"),
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
                
st.divider()

st.header("복습 추천")

if st.button("오답 복습 추천 받기"):
    response = requests.get(
        f"{API_BASE_URL}/review/recommendations", 
        timeout=30,
    )
    
    if response.status_code == 200:
        recommendations = response.json()
        
        if not recommendations:
            st.info("아직 오답 기록이 없습니다.")
        else:
            for item in recommendations:
                st.write(
                    f"- **{item['concept_tag']}**: "
                    f"{item['wrong_count']}회 오답 → {item['recommendation']}"
                )
    else:
        st.error("복습 추천 문제를 가져오는데 실패했습니다.")