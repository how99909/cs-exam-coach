import requests
import streamlit as st
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="CS Exam Coach", 
    page_icon="📚", 
    layout="wide",
)

st.title("📚 CS Exam Coach")
st.write("컴소 전공 시험 대비 AI 문제 생성 및 오답 복습 서비스")

if "user_name" not in st.session_state:
    st.session_state.user_name = "default_user"
    
user_name = st.text_input(
    "사용자 이름", 
    value=st.session_state.user_name,
    help="사용자 이름은 학습 기록과 오답 복습 추천에 사용됩니다.",
)

st.session_state.user_name = user_name.strip() or "default_user"

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ["문제 생성", "PDF 업로드", "RAG 질의응답",  "복습 추천", "학습 기록", "시험 계획", "문제 평가", "관리자 대시보드"]
)

with tab1:
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
        if not content.strip():
            st.warning("공부 내용을 입력해주세요.")
        else:
            response = requests.post(
                f"{API_BASE_URL}/questions/generate", 
                json={
                    "user_name": st.session_state.user_name,
                    "subject": subject,
                    "content": content,
                    "question_type": question_type,
                    "count": count,
                    "difficulty": difficulty,
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
                question_id = question.get("question_id", question.get("id"))

                if question_id is None:
                    st.error("문제 ID를 찾을 수 없습니다. 문제를 다시 생성해 주세요.")
                    st.stop()

                response = requests.post(
                    f"{API_BASE_URL}/grading/grade",
                    json={
                        "user_name": st.session_state.user_name,
                        "question_id": question_id,
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
                response = requests.post(
                    f"{API_BASE_URL}/feedback/question",
                    json={
                        "user_name": st.session_state.user_name,
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
    
with tab2:
    st.header("PDF 자료 업로드")
    
    pdf_subject = st.selectbox(
        "PDF 자료의 과목을 선택하세요",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍"],
        key="pdf_subject",
    )
    
    uploaded_file = st.file_uploader(
        "PDF 강의자료를 업로드하세요",
        type=["pdf"],
    )
    
    start_page = st.number_input(
        "시작 페이지 (선택 사항)",
        min_value=1,
        value=1,
        step=1,
        key="pdf_start_page",
    )
    
    end_page = st.number_input(
        "끝 페이지 (선택 사항)",
        min_value=1,
        value=1,
        step=1,
        key="pdf_end_page",
    )
    
    if "pdf_extracted_text" not in st.session_state:
        st.session_state.pdf_extracted_text = ""
        
    if "pdf_material_id" not in st.session_state:
        st.session_state.pdf_material_id = None
        
    if "pdf_pages" not in st.session_state:
        st.session_state.pdf_pages = []
        
    if st.button("PDF 텍스트 추출하기"):
        if uploaded_file is None:
            st.warning("PDF 파일을 업로드해주세요.")
        else:
            files = {
                "file": (
                    uploaded_file.name, 
                    uploaded_file.getvalue(), 
                    "application/pdf"
                )
            }
            
            data = {
                "user_name": st.session_state.user_name,
                "subject": pdf_subject,
                "start_page": int(start_page),
                "end_page": int(end_page),
            }
            
            response = requests.post(
                f"{API_BASE_URL}/materials/extract-pdf",
                data=data,
                files=files,
                timeout=120,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.success("PDF 텍스트 추출이 완료되었습니다.")
                    st.session_state.pdf_extracted_text = result["content"]
                    st.session_state.pdf_material_id = result["material_id"]
                    st.session_state.pdf_pages = result.get("pages", [])
                    
                    st.write(f"전체 페이지 수: {result['page_count']}")
                    st.write(
                        f"선택된 페이지 범위: {result['selected_start_page']} ~ "
                        f"{result['selected_end_page']} "
                        f"({result['selected_page_count']}페이지)"
                    )
                    st.write(f"추출된 텍스트 길이: {result['text_length']}자")
                    
                    st.subheader("미리보기")
                    st.text_area(
                        "추출 텍스트", 
                        value=result["preview"],
                        height=300,
                    )
                else:
                    st.error(result.get("message", "PDF 텍스트 추출에 실패했습니다."))
            else:
                st.error("PDF 업로드 요청에 실패했습니다.")
                st.write(response.text)
                            
    st.divider()
    
    st.subheader("RAG 문서 인덱싱")
    
    if st.button("추출된 PDF를 RAG 문서로 인덱싱하기"):
        if not st.session_state.pdf_extracted_text.strip():
            st.button("먼저 PDF 텍스트를 추출하세요.")
        elif st.session_state.pdf_material_id in None:
            st.warning("material_id가 없습니다. PDF를 다시 추출하세요.")
        else:
            payload = {
                "user_name": st.session_state.user_name,
                "subject": pdf_subject,
                "material_id": st.session_state.pdf_extracted_text
            }
            
            if st.session_state.pdf_pages:
                payload["pages"] = st.session_state.pdf_pages
            else:
                payload["content"] = st.session_state.pdf_extracted_text
            
            response = requests.post(
                f"{API_BASE_URL}/rag/index",
                json=payload,
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.success(f"RAG 인덱싱 완료: {result['chunk_count']}개 chunk 저장")
                else:
                    st.error(result.get("message", "RAG 인덱싱에 실패했습니다."))
            else:
                st.error("RAG 인덱싱 요청에 실패했습니다.")
                st.write(response.text)
                
    st.divider()
    
    st.subheader("PDF 기반 문제 생성")
    
    pdf_question_type = st.selectbox(
        "문제 유형을 선택하세요",
        ["short_answer", "multiple_choice", "coding", "true_false", "fill_in_the_blank", "essay"],
        key="pdf_question_type",
    )
    
    pdf_difficulty = st.selectbox(
        "난이도를 선택하세요",
        ["easy", "medium", "hard", "exam_like"],
        key="pdf_difficulty",
    )
    
    pdf_count = st.slider(
        "생성할 문제 수", 
        min_value=1, 
        max_value=10, 
        value=5,
        key="pdf_count",
    )
    
    if st.button("PDF 내용으로 문제 생성하기"):
        if not st.session_state.pdf_extracted_text.strip():
            st.warning("먼저 PDF 텍스트를 추출해주세요.")
        else:
            response = requests.post(
                f"{API_BASE_URL}/questions/generate", 
                json={
                    "user_name": st.session_state.user_name,
                    "subject": pdf_subject,
                    "content": st.session_state.pdf_extracted_text,
                    "question_type": pdf_question_type,
                    "count": pdf_count,
                    "difficulty": pdf_difficulty,
                },
                timeout=120,
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.questions = data["questions"]
                st.success("PDF 기반 문제가 생성되었습니다.")
                st.info("문제 생성 탭에서 생성된 문제를 확인하고 답안을 제출할 수 있습니다.")
            else:
                st.error("PDF 기반 문제 생성에 실패했습니다.")
                st.write(response.text)

with tab3:
    st.header("RAG 문서 질의응답")
    st.caption("인덱싱된 PDF 자료를 기반으로 질문에 답합니다.")
    
    rag_subject = st.selectbox(
        "질문할 과목을 선택하세요",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="rag_subject",
    )
    
    rag_question = st.text_area(
        "질문을 입력하세요",
        height=120,
        placeholder="예: BFS와 DFS의 차이를 설명해줘.",
    )
    
    top_k = st.slider(
        "검색할 문서 조각 수",
        min_value=1,
        max_value=10,
        value=5,
        key="rag_top_k",
    )
    
    if st.button("문서 기반 답변 생성하기"):
        if not rag_question.strip():
            st.warning("질문을 입력하세요.")
        else:
            response = requests.post(
                f"{API_BASE_URL}/rag/ask",
                json={
                    "user_name": st.session_state.user_name,
                    "subject": rag_subject,
                    "question": rag_question,
                    "top_k": top_k,
                },
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.subheader("답변")
                    st.write(result["answer"])
                    
                    st.subheader("참고한 문서 조각")
                    
                    for source in result["sources"]:
                        page_label = source.get("page_number") or "unknown"
                        
                        with st.expander(
                            f"Source {source['source_number']} "
                            f"/ material_id={source['material_id']} "
                            f"/ Page {page_label}"
                            f"/ chunk={source['chunk_index']}"
                        ):
                            st.write(f"distance: {source['distance']}")
                            st.write(source["preview"])
                else:
                    st.error(result.get("message", "답변 생성에 실패했습니다."))
            else:
                st.error("RAG 질의응답 요청에 실패했습니다.")
                st.write(response.text)

with tab4:
    st.header("복습 추천")

    if st.button("오답 복습 추천 받기"):
        response = requests.get(
            f"{API_BASE_URL}/review/recommendations", 
            params={"user_name": st.session_state.user_name},
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

with tab5:
    st.header("학습 기록")
    
    if st.button("최근 생성 문제 불러오기"):
        response = requests.get(
            f"{API_BASE_URL}/history/questions", 
            params={"user_name": st.session_state.user_name},
            timeout=30,
        )
        
        if response.status_code == 200:
            questions = response.json()
            
            if not questions:
                st.info("최근 생성된 문제가 없습니다.")
            else:
                for question in questions:
                    with st.expander(f"[{question['question_type']}] {question['concept_tag']}"):
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
        response = requests.get(
            f"{API_BASE_URL}/history/wrong-answers", 
            params={"user_name": st.session_state.user_name},
            timeout=30,
        )
        
        if response.status_code == 200:
            wrong_answers = response.json()
            
            if not wrong_answers:
                st.info("최근 오답 기록이 없습니다.")
            else:
                for wrong_answer in wrong_answers:
                    with st.expander(f"{wrong_answer['concept_tag']} - 오답 기록"):
                        st.write("**내 답안**")
                        st.write(wrong_answer["user_answer"])
                        
                        st.write("**정답**")
                        st.write(wrong_answer["correct_answer"])
                        
                        st.write("**피드백**")
                        st.write(wrong_answer["feedback"])
                        
                        st.caption(f"오답 기록 시간: {wrong_answer['created_at']}")
        else:
            st.error("최근 오답 기록을 가져오는데 실패했습니다.")
            
with tab6:
    st.header("시험 D-Day 계획")
    
    exam_date = st.date_input(
        "시험 날짜를 선택하세요",
        help="시험 날짜를 선택하면 남은 일수와 학습 계획을 확인할 수 있습니다.",
    )
    
    if st.button("복습 계획 생성하기"):
        response = requests.get(
            f"{API_BASE_URL}/review/study-plan", 
            params={
                "user_name": st.session_state.user_name,
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
                            f"- **{concept['concept_tag']}**: "
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
            
with tab7:
    st.header("문제 평가 요약")
    
    if st.button("내 평가 요약 불러오기"):
        response = requests.get(
            f"{API_BASE_URL}/feedback/summary", 
            params={"user_name": st.session_state.user_name},
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
            
with tab8:
    st.header("관리자용 문제 품질 대시보드")
    st.caption("전체 사용자 평가를 기반으로 AI 생성 문제의 품질을 확인합니다.")
    
    response = None
    if st.button("관리자 대시보드 불러오기"):
        response = requests.get(
            f"{API_BASE_URL}/feedback/admin-dashboard",
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
        
