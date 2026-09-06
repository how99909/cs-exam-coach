import streamlit as st

from api.client import ApiClient


def render_materials(
    api: ApiClient,
) -> None:
    st.header("PDF 자료 업로드")
        
    subject = st.selectbox(
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
            response = api.post(
                "/materials/extract-pdf",
                data={
                    "subject": subject,
                    "start_page": start_page,
                    "end_page": end_page,
                },
                files={
                    "file": (
                        uploaded_file.name, 
                        uploaded_file.getvalue(), 
                        "application/pdf"
                    )
                },
                timeout=180,
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
        elif st.session_state.pdf_material_id is None:
            st.warning("material_id가 없습니다. PDF를 다시 추출하세요.")
        else:
            payload = {
                "subject": subject,
                "material_id": st.session_state.pdf_material_id,
            }
            
            if st.session_state.pdf_pages:
                payload["pages"] = st.session_state.pdf_pages
            else:
                payload["content"] = st.session_state.pdf_extracted_text
            
            response = api.post(
                "/rag/index",
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
            response = api.post(
                "/questions/generate", 
                json={
                    "subject": subject,
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