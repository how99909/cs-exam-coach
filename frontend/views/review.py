import streamlit as st

from api.client import ApiClient


def render_review_recommendations(
    api: ApiClient,
) -> None:
    st.header("복습 추천")
    
    if st.button("오답 복습 추천 받기"):
        response = api.get(
            "/review/recommendations",
            timeout=30,
        )
        
        if response.status_code == 200:
            recommendations = response.json()
            
            if not recommendations:
                st.info("아직 오답 기록이 없습니다.")
            else:
                for item in recommendations:
                    st.write(
                        f"- **{item['concept']}**: "
                        f"{item['wrong_count']}회 오답 → {item['recommendation']}"
                    )
        else:
            st.error("복습 추천 문제를 가져오는데 실패했습니다.")
            
            
def render_learning_history(
    api: ApiClient,
) -> None:
    st.header("학습 기록")
        
    if st.button("최근 생성 문제 불러오기"):
        response = api.get(
            "/history/questions",
            timeout=30,
        )
        
        if response.status_code == 200:
            questions = response.json()
            
            if not questions:
                st.info("최근 생성된 문제가 없습니다.")
            else:
                for question in questions:
                    with st.expander(f"[{question['question_type']}] {question['concept']}"):
                        st.write("**문제**")
                        st.write(question["question_text"])
                        
                        st.write("**정답**")
                        st.write(question["answer"])
                        
                        st.write("**해설**")
                        st.write(question["explanation"])
                        
                        st.caption(f"생성 시간: {question['created_at']}")
        else:
            st.error("최근 생성 문제를 가져오는데 실패했습니다.")
            
    if st.button("최근 오답 기록 불러오기"):
        response = api.get(
            "/history/wrong-answers",
            timeout=30,
        )
        
        if response.status_code == 200:
            wrong_answers = response.json()
            
            if not wrong_answers:
                st.info("최근 오답 기록이 없습니다.")
            else:
                for wrong_answer in wrong_answers:
                    with st.expander(f"{wrong_answer['concept']} - 오답 기록"):
                        st.write("**내 답안**")
                        st.write(wrong_answer["user_answer"])
                        
                        st.write("**정답**")
                        st.write(wrong_answer["correct_answer"])
                        
                        st.write("**피드백**")
                        st.write(wrong_answer["feedback"])
                        
                        st.caption(f"오답 기록 시간: {wrong_answer['created_at']}")
        else:
            st.error("최근 오답 기록을 가져오는데 실패했습니다.")
            
            
def render_study_plan(
    api: ApiClient,
) -> None:
    st.header("시험 D-Day 계획")
        
    exam_date = st.date_input(
        "시험 날짜를 선택하세요",
        help="시험 날짜를 선택하면 남은 일수와 학습 계획을 확인할 수 있습니다.",
    )
    
    if st.button("복습 계획 생성하기"):
        response = api.get(
            "/review/study-plan", 
            params={
                "exam_date": exam_date.strftime("%Y-%m-%d"),
            },
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if not result.get("success"):
                st.error(result.get("message", "복습 계획 생성에 실패했습니다."))
            else:
                st.success(
                    f"시험까지 {result['days_left']}일 남았습니다."
                )
                
                if not result.get("plan"):
                    st.info(result.get("message", "아직 복습 계획이 없습니다."))
                else:
                    st.subheader("약점 개념")
                    
                    for concept in result["weak_concepts"]:
                        st.write(
                            f"- **{concept['concept']}**: "
                            f"{concept['wrong_count']}회 오답"
                        )
                        
                    st.subheader("추천 복습 계획")
                    
                    for item in result["plan"]:
                        with st.expander(item["day"]):
                            st.write(item["task"])
                            
                            if item["concepts"]:
                                st.write("복습 개념")
                                for concept in item["concepts"]:
                                    st.write(f"- {concept}")
        else:
            st.error("복습 계획 요청에 실패했습니다.")
            st.write(response.text)