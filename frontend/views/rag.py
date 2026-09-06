import streamlit as st

from api.client import ApiClient


def render_rag_qa(api):
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
            response = api.get(
                "/rag/documents",
                params={
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
                "subject": rag_subject,
                "question": rag_question,
                "top_k": top_k,
            }
            
            if search_scope == "특정 문서":
                if selected_material_id is None:
                    st.warning("특정 문서 검색을 선택했다면 문서를 먼저 선택하세요.")
                    st.stop()
                    
                payload["material_id"] = selected_material_id
            
            response = api.post(
                "/rag/ask",
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
            response = api.post(
                "/rag-feedback/answer",
                json={
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
    
    
def render_rag_documents(api):
    st.header("RAG 문서 관리")
    st.caption("현재 Chroma Vector DB에 인덱싱된 문서를 조회하고 삭제합니다.")
    
    manage_subject = st.selectbox(
        "조회할 과목",
        ["전체", "알고리즘", "마이크로프로세서", "수치해석", "시스템프로그래밍", "기타"],
        key="manage_subject",
    )
    
    params = {}
    
    if manage_subject != "전체":
        params["subject"] = manage_subject
        
    if st.button("내 RAG 문서 목록 불러오기"):
        response = api.get(
            "/rag/documents",
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
                        delete_response = api.delete(
                            "/rag/documents",
                            json={
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
    
    
def render_rag_questions(api):
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
            response = api.get(
                "/rag/documents",
                params={
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
            
        response = api.post(
            "/rag-questions/generate",
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
    
    
def render_weakness_rag_questions(api):
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
            response = api.get(
                "/rag/documents",
                params={
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
            
        response = api.post(
            "/weakness-rag-questions/generate",
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