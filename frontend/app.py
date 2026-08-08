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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14 = st.tabs(
    [
        "문제 생성", 
        "PDF 업로드", 
        "RAG 질의응답", 
        "RAG 문서 관리", 
        "RAG 문제 생성",
        "약점 RAG 문제",
        "시험지 생성",
        "응시 모드",
        "복습 추천", 
        "학습 기록", 
        "시험 계획", 
        "문제 평가", 
        "관리자 대시보드",
        "RAG 평가",
    ]
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
                        "concept_tag": question.get("concept"),
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
    
    search_scope = st.radio(
        "검색 범위",
        ["과목 전체 문서", "특정 문서"],
        key="rag_search_scope",
    )
    
    selected_material_id = None
    
    if search_scope == "특정 문서":
        if st.button("질문 가능한 문서 목록 불러오기"):
            response = requests.get(
                f"{API_BASE_URL}/rag/documents",
                params={
                    "user_name": st.session_state.user_name,
                    "subject": rag_subject,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.rag_question_documents = result.get("documents", [])
                
                if not st.session_state.rag_question_documents:
                    st.info("인덱싱된 문서가 없습니다. 먼저 PDF를 인덱싱하세요.")
            else:
                st.error("문서 목록을 불러오지 못햇습니다.")
                st.write(response.text)
                
        if "rag_question_documents" not in st.session_state:
            st.session_state.rag_question_documents = []
            
        if st.session_state.rag_question_documents:
            material_options ={
                f"material_id={doc['material_id']} / pages={doc['pages']} / chunks={doc['chunk_count']}":doc[
                    "material_id"
                ]
                for doc in st.session_state.rag_question_documents
            }
            
            selected_label = st.selectbox(
                "질문할 문서 선택",
                list(material_options.keys()),
                key="rag_selected_material_label",
            )
            
            selected_material_id = material_options[selected_label]
    
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
            payload = {
                "user_name": st.session_state.user_name,
                "subject": rag_subject,
                "question": rag_question,
                "top_k": top_k,
            }
            
            if search_scope == "특정 문서":
                if selected_material_id is None:
                    st.warning("특정 문서 검색을 선택했다면 문서를 먼저 선택하세요.")
                    st.stop()
                    
                payload["material_id"] = selected_material_id
            
            response = requests.post(
                f"{API_BASE_URL}/rag/ask",
                json=payload,
                timeout=180,
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.subheader("답변")
                    st.caption(f"검색 범위: {result.get('search_scope', '알 수 없음')}")
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
                            
                    st.session_state.last_rag_question = rag_question
                    st.session_state.last_rag_answer = result["answer"]
                    st.session_state.last_rag_subject = rag_subject
                    st.session_state.last_rag_material_id = result.get("material_id")
                else:
                    st.error(result.get("message", "답변 생성에 실패했습니다."))
            else:
                st.error("RAG 질의응답 요청에 실패했습니다.")
                st.write(response.text)
                
    st.divider()
    st.subheader("RAG 답변 평가")
    
    if "last_rag_answer" not in st.session_state:
        st.info("먼저 RAG 답변을 생성하세요.")
    else:
        accuracy_score = st.slider(
            "답변 정확도",
            min_value=1,
            max_value=5,
            value=3,
            key="rag_accuracy_score",
        )
        
        grounding_score = st.slider(
            "근거 충분성",
            min_value=1,
            max_value=5,
            value=3,
            key="rag_grounding_score",
        )
        
        source_relevance_score = st.slider(
            "출처 적합성",
            min_value=1,
            max_value=5,
            value=3,
            key="rag_source_relevance_score",
        )
        
        helpfulness_score = st.slider(
            "도움 여부",
            min_value=1,
            max_value=5,
            value=3,
            key="rag_helpfulness_score",
        )
        
        rag_feedback_comment = st.text_area(
            "RAG 답변 평가 코멘트",
            key="rag_feedback_comment",
            placeholder="답변이 문서 근거에 충실했는지, 출처가 적절했는지 적어주세요.",
        )
        
        if st.button("RAG 답변 평가 저장"):
            response = requests.post(
                f"{API_BASE_URL}/rag-feedback/answer",
                json={
                    "user_name": st.session_state.user_name,
                    "subject": st.session_state.subject,
                    "material_id": st.session_state.material_id,
                    "question": st.session_state.question,
                    "answer": st.session_state.answer,
                    "accuracy_score": accuracy_score,
                    "grounding_score": grounding_score,
                    "source_relevance_score": source_relevance_score,
                    "helpfulness_score": helpfulness_score,
                    "comment": rag_feedback_comment,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                saved = response.json()
                if saved.get("success"):
                    st.success("RAG 답변 평가가 저장되었습니다.")
                else:
                    st.error(saved.get("message", "RAG 답변 평가 저장에 실패했습니다."))
            else:
                st.error("RAG 답변 평가 요청에 실패했습니다.")
                st.write(response.text)

with tab4:
    st.header("RAG 문서 관리")
    st.caption("현재 Chroma Vector DB에 인덱싱된 문서를 조회하고 삭제합니다.")
    
    manage_subject = st.selectbox(
        "조회할 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="manage_subject",
    )
    
    params = {
        "user_name": st.session_state.user_name,
    }
    
    if manage_subject != "전체":
        params["subject"] = manage_subject
        
    if st.button("내 RAG 문서 목록 불러오기"):
        response = requests.get(
            f"{API_BASE_URL}/rag/documents",
            params=params,
            timeout=30,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if not result.get("documents"):
                st.info("인덱싱된 문서가 없습니다.")
            else:
                st.success(f"{result['document_count']}개 문서를 찾았습니다.")
                
                st.session_state.rag_documents = result["documents"]
        else:
            st.error("RAG 문서 목록을 불러오지 못했습니다.")
            st.write(response.text)
    
    if "rag_documents" not in st.session_state:
        st.session_state.rag_documents = []
        
    if st.session_state.rag_documents:
        st.subheader("인덱싱된 문서 목록")
        
        for document in st.session_state.rag_documents:
            with st.expander(
                f"{document['subject']} / material_id={document['material_id']}"
            ):
                st.write(f"사용자: {document['user_name']}")
                st.write(f"과목: {document['subject']}")
                st.write(f"material_id: {document['material_id']}")
                st.write(f"chunk 수: {document['chunk_count']}")
                st.write(f"페이지 수: {document['page_count']}")
                st.write(f"페이지 목록: {document['pages']}")
                
                delete_confirm = st.checkbox(
                    f"이 문서를 삭제하겠습니다. material_id={document['material_id']}",
                    key=f"delete_confirm_{document['material_id']}"
                )
                
                if st.button(
                    f"문서 삭제 material_id={document['material_id']}",
                    key=f"delete_button_{document['material_id']}",
                ):
                    if not delete_confirm:
                        st.warning("삭제하려면 먼저 확인 체크박스를 선택하세요.")
                    else:
                        delete_response = requests.delete(
                            f"{API_BASE_URL}/rag/documents",
                            json={
                                "user_name": st.session_state.user_name,
                                "subject": document["subject"],
                                "material_id": document["material_id"],
                            },
                            timeout=30,
                        )
                        
                        if delete_response.status_code == 200:
                            delete_result = delete_response.json()
                            
                            if delete_result.get("success"):
                                st.success(
                                    f"삭제 완료: {delete_result['deleted_count']}개 chunk 삭제"
                                )
                                st.session_state.rag_documents = [
                                    item
                                    for item in st.session_state.rag_documents
                                    if item["material_id"] != document["material_id"]
                                ]
                            else:
                                st.error(delete_result.get("message", "삭제 실패"))
                        else:
                            st.error("삭제 요청에 실패했습니다.")
                            st.write(delete_response.text)

with tab5:
    st.header("RAG 기반 예상문제 생성")
    st.caption("인덱싱된 PDF 문서 chunk를 기반으로 예상문제를 생성합니다.")
    
    rag_q_subject = st.selectbox(
        "문제 생성 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="rag_q_subject",
    )
    
    rag_q_scope = st.radio(
        "문제 생성 범위",
        ["과목 전체 문서", "특정 문서"],
        key="rag_q_scope",
    )
    
    selected_rag_q_material_id = None
    
    if rag_q_scope == "특정 문서":
        if st.button("문제 생성 가능한 문서 목록 불러오기"):
            response = requests.get(
                f"{API_BASE_URL}/rag/documents",
                params={
                    "user_name": st.session_state.user_name,
                    "subject": rag_q_subject,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.rag_q_documents = result.get("documents", [])
                
                if not st.session_state.rag_q_documents:
                    st.info("인덱싱된 문서가 없습니다. 먼저 PDF를 인덱싱하세요.")
            else:
                st.error("문서 목록을 불러오지 못했습니다.")
                st.write(response.text)
                
        if "rag_q_documents" not in st.session_state:
            st.session_state.rag_q_documents = []
            
        if st.session_state.rag_q_documents:
            material_options = {
                f"material_id={doc['material_id']} / pages={doc['pages']} / chunks={doc['chunk_count']}": doc[
                    "material_id"
                ]
                for doc in st.session_state.rag_q_documents
            }
            
            selected_label = st.selectbox(
                "문제 생성에 사용할 문서",
                list(material_options.keys()),
                key="rag_q_selected_material_label",
            )
            
            selected_rag_q_material_id = material_options[selected_label]
            
    rag_q_type = st.selectbox(
        "문제 유형",
        ["short_answer", "multiple_choice", "coding", "true_false", "fill_in_the_blank", "essay"],
        key="rag_q_type",
    )
    
    rag_q_difficulty = st.selectbox(
        "난이도",
        ["easy", "medium", "hard", "exam_like"],
        key="rag_q_difficulty",
    )
    
    rag_q_count = st.slider(
        "생성할 문제 수",
        min_value=1,
        max_value=10,
        value=5,
        key="rag_q_count",
    )
    
    rag_q_top_k = st.slider(
        "참고할 문서 chunk 수",
        min_value=3,
        max_value=20,
        value=8,
        key="rag_q_top_k",
    )
    
    if st.button("RAG 기반 예상문제 생성하기"):
        payload = {
            "user_name": st.session_state.user_name,
            "subject": rag_q_subject,
            "question_type": rag_q_type,
            "difficulty": rag_q_difficulty,
            "count": rag_q_count,
            "top_k": rag_q_top_k,
        }
        
        if rag_q_scope == "특정 문서":
            if selected_rag_q_material_id is None:
                st.warning("특정 문서를 선택하세요.")
                st.stop()
                
            payload["material_id"] = selected_rag_q_material_id
            
        response = requests.post(
            f"{API_BASE_URL}/rag-questions/generate",
            json=payload,
            timeout=180,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                st.success(f"{result['question_count']}개 문제가 생성되었습니다.")
                
                for question in result["questions"]:
                    source = question.get("source") or {}
                    
                    with st.expander(
                        f"Q{question['id']} / {question['concept']} "
                        f"/ Page {source.get('page_number', 'unknown')}"
                    ):
                        st.write("문제")
                        st.write(question["question"])
                        
                        st.write("정답")
                        st.write(question["answer"])
                        
                        st.write("해설")
                        st.write(question["explanation"])
                        
                        st.write("출처")
                        st.write(
                            f"material_id={source.get('material_id')}, "
                            f"page={source.get('page_number')}, "
                            f"chunk={source.get('chunk_index')}"
                        )
            else:
                st.error(result.get("message", "문제 생성 실패"))
        else:
            st.error("RAG 기반 문제 생성 요청에 실패했습니다.")
            st.write(response.text)

with tab6:
    st.header("약점 기반 RAG 복습 문제")
    st.caption("사용자의 오답 개념을 분석하고, 관련 문서 chunk를 찾아 복습 문제를 생성합니다.")
    
    weak_subject = st.selectbox(
        "약점 문제 생성 과목",
        ["알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="weak_rag_subject",
    )
    
    weak_scope = st.radio(
        "문제 생성 범위",
        ["과목 전체 문서", "특정 문서"],
        key="weak_rag_scope",
    )
    
    selected_weak_material_id = None
    
    if weak_scope == "특정 문서":
        if st.button("약점 문제용 문서 목록 불러오기"):
            response = requests.get(
                f"{API_BASE_URL}/rag/documents",
                params={
                    "user_name": st.session_state.user_name,
                    "subject": weak_subject,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.weak_rag_documents = result.get("documents", [])
                
                if not st.session_state.weak_rag_documents:
                    st.info("인덱싱된 문서가 없습니다. 먼저 PDF를 인덱싱하세요.")
            else:
                st.error("문서 목록을 불렁지 못했습니다.")
                st.write(response.text)
                
        if "weak_rag_documents" not in st.session_state:
            st.session_state.weak_rag_documents = []
            
        if st.session_state.weak_rag_documents:
            material_options = {
                f"material_id={doc['material_id']} / pages={doc['pages']} / chunks={doc['chunk_count']}": doc[
                    "material_id"
                ]
                for doc in st.session_state.weak_rag_documents
            }
            
            selected_label = st.selectbox(
                "약점 문제 생성에 사용할 문서",
                list(material_options.keys()),
                key="weak_selected_material_label",
            )
            
            selected_weak_material_id = material_options[selected_label]
            
    weakness_count = st.slider(
        "분석할 약점 개념 수",
        min_value=1,
        max_value=5,
        value=3,
        key="weakness_count",
    )
    
    weak_question_count =st.slider(
        "생성할 복습 문제 수",
        min_value=1,
        max_value=10,
        value=5,
        key="weak_question_count",
    )
    
    weak_question_type = st.selectbox(
        "문제 유형",
        ["short_answer", "multiple_choice", "coding", "true_false", "fill_in_the_blank", "essay"],
        key="weak_question_type",
    )
    
    weak_difficulty = st.selectbox(
        "난이도",
        ["easy", "medium", "hard", "exam_like"],
        index=3,
        key="weak_difficulty",
    )
    
    top_k_per_concept = st.slider(
        "약점 개념별 검색 chunk 수",
        min_value=1,
        max_value=5,
        value=3,
        key="top_k_per_concept",
    )
    
    if st.button("약점 기반 RAG 문제 생성하기"):
        payload = {
            "user_name": st.session_state.user_name,
            "subject": weak_subject,
            "weakness_count": weakness_count,
            "question_count": weak_question_count,
            "question_type": weak_question_type,
            "difficulty": weak_difficulty,
            "top_k_per_concept": top_k_per_concept,
        }
        
        if weak_scope == "특정 문서":
            if selected_weak_material_id is None:
                st.warning("특정 문서를 선택하세요.")
                st.stop()
                
            payload["material_id"] = selected_weak_material_id
            
        response = requests.post(
            f"{API_BASE_URL}/weakness-rag-questions/generate",
            json=payload,
            timeout=180,
        )
        
        if response.status_code == 200:
            result = response.json()
            
            st.success(f"{result['question_count']}개 약점 복습 문제가 생성되었습니다.")
            
            st.subheader("분석된 약점 개념")
            for weakness in result["weakness_concepts"]:
                st.write(f"- {weakness['concept']}: 오답 {weakness['wrong_count']}회")
                
            st.caption(f"사용된 RAG chunk 수: {result['used_chunk_count']}")
            
            st.subheader("생성된 약점 복습 문제")
            
            for question in result["questions"]:
                source = question.get("source") or {}
                
                with st.expander(
                    f"Q{question['id']} / {question['concept']} "
                    f"/ Page {source.get('page_number', 'unknown')}"
                ):
                    st.write("문제")
                    st.write(question["question"])
                    
                    st.write("정답")
                    st.write(question["answer"])
                    
                    st.write("해설")
                    st.write(question["explanation"])
                    
                    st.write("출처")
                    st.write(
                        f"material_id={source.get('material_id')}, "
                        f"page={source.get('page_number')}, "
                        f"chunk={source.get('chunk_index')}"
                    )
        else:
            st.error("약점 기반 RAG 문제 생성 요청에 실패했습니다.")
            st.write(response.text)

with tab7:
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
        response = requests.get(
            f"{API_BASE_URL}/exam-papers/questions",
            params={
                "user_name": st.session_state.user_name,
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
                response = requests.post(
                    f"{API_BASE_URL}/exam-papers/generate",
                    json={
                        "user_name": st.session_state.user_name,
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

with tab8:
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
        response = requests.get(
            f"{API_BASE_URL}/exam-papers/questions",
            params={
                "user_name": st.session_state.user_name,
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
                response = requests.post(
                    f"{API_BASE_URL}/exam-attempts/submit",
                    json={
                        "user_name": st.session_state.user_name,
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
        response = requests.get(
            f"{API_BASE_URL}/exam-attempts/history",
            params={
                "user_name": st.session_state.user_name,
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

with tab9:
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

with tab10:
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
            
with tab11:
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
            
with tab12:
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
          
with tab13:
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
        
with tab14:
    st.header("RAG 답변 평가 요약")
    
    rag_feedback_subject = st.selectbox(
        "평가 요약 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="rag_feedback_subject",
    )
    
    params = {
        "user_name": st.session_state.user_name,
    }
    
    if rag_feedback_subject != "전체":
        params["subject"] = rag_feedback_subject
        
    if st.button("내 RAG 평가 요약 불러오기"):
        response = requests.get(
            f"{API_BASE_URL}/rag-feedback/summary",
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
        response = requests.get(
            f"{API_BASE_URL}/rag-feedback/recent",
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
