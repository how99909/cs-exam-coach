from typing import Any

import chromadb
from openai import OpenAI

from app.core.config import settings

client = OpenAI(api_key=settings.OpenAI_API_KEY) if settings.OpenAI_API_KEY else None

chroma_client = chromadb.HttpClient(
    host=settings.CHROMA_HOST,
    port=settings.CHROMA_PORT,
)

COLLECTION_NAME = "cs_exam_coach_documents"


def get_collection():
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "CS Exam Coach RAG document chunks"},
    )
    
    
def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    cleaned_text = text.strip()
    
    if not cleaned_text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(cleaned_text):
        end = start + chunk_size
        chunk = cleaned_text[start:end].strip()
        
        if chunk:
            chunks.append(chunk)
            
        start = end - overlap
        
        if start < 0:
            start = 0
            
        if start >= len(cleaned_text):
            break
        
    return chunks


def create_embedding(text: str) -> list[float]:
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set")
    
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text,
    )
    
    return response.data[0].embedding


def index_document(
    user_name: str,
    subject: str,
    material_id: int,
    content: str,
) -> dict[str, Any]:
    collection = get_collection()
    
    chunks = split_text_into_chunks(content)
    
    if not chunks:
        return {
            "success": False,
            "message": "인덱싱할 텍스트가 없습니다.",
        }
        
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for index, chunk in enumerate(chunks):
        chunk_id = f"{user_name}-{subject}-{material_id}-{index}"
        
        embedding = create_embedding(chunk)
        
        ids.append(chunk_id)
        documents.append(chunk)
        embeddings.append(embedding)
        metadatas.append(
            {
                "user_name": user_name,
                "subject": subject,
                "material_id": material_id,
                "chunk_index": index,
            }
        )
        
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    
    return {
        "success": True,
        "message": "문서 인덱싱이 완료되었습니다.",
        "chunk_count": len(chunks),
        "material_id": material_id,
    }
    
    
def retrieve_chunks(
    user_name: str,
    subject: str,
    question: str,
    top_k: int = 5,
    material_id: int | None = None,
) -> list[dict[str, Any]]:
    collection = get_collection()
    query_embedding = create_embedding(question)
    
    where_conditions = [
        {"user_name": {"$eq": user_name}},
        {"subject": {"$eq": subject}},
    ]
    
    if material_id is not None:
        where_conditions.append({"material_id": {"$eq": material_id}})
        
    where_filter = {"$and": where_conditions}
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )
    
    retrieved = []
    
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    for document, metadata, distance in zip(documents, metadatas, distances):
        retrieved.append(
            {
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
        )
        
    return retrieved


def answer_with_context(
    user_name: str,
    subject: str,
    question: str,
    top_k: int = 5,
    material_id: int | None = None,
) -> dict[str, Any]:
    if client is None:
        return {
            "success": False,
            "message": "OPENAI_API_KEY가 설정되어 있지 않습니다.",
        }
        
    retrieved_chunks = retrieve_chunks(
        user_name=user_name,
        subject=subject,
        question=question,
        top_k=top_k,
        material_id=material_id,
    )
    
    if not retrieved_chunks:
        return {
            "success": False,
            "message": "관련 문서 조각을 찾지 못했습니다. 먼저 문서를 인덱싱하세요.",
        }
        
    context_text = "\n\n".join(
        [
            (
                f"[Source {index + 1} | "
                f"material_id={item['metadata'].get('material_id')} | "
                f"page={item['metadata'].get('page_number', 'unknown')} |"
                f"chunk={item['metadata'].get('chunk_index')}]\n"
                f"{item['content']}"
            )
            for index, item in enumerate(retrieved_chunks)
        ]
    )
    
    search_scope = (
        f"material_id={material_id} 문서"
        if material_id is not None
        else f"{subject} 과목 전체 인덱싱 문서"
    )
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 학습을 돕는 RAG 기반 튜터다.

검색 범위: {search_scope}

아래 제공된 문서 근거만 사용해서 질문에 답하라.
문서에 없는 내용은 추측하지 말고 "제공된 자료만으로는 확인하기 어렵습니다"라고 말하라.
답변 마지막에는 어떤 Source를 참고했는지 표시하라.

과목: {subject}

문서 근거:
{context_text}

질문:
{question}
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "너는 제공된 문서 근거에 기반해 답변하는 컴퓨터소프트웨어학 전공 튜터다.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )
    
    answer = response.choices[0].message.content
    
    return {
        "success": True,
        "search_scope": search_scope,
        "material_id": material_id,
        "answer": answer,
        "sources": [
            {
                "source_number": index + 1,
                "material_id": item["metadata"].get("material_id"),
                "page_number": item["metadata"].get("page_number"),
                "chunk_index": item["metadata"].get("chunk_index"),
                "distance": item["distance"],
                "preview": item["content"][:500],
            }
            for index, item in enumerate(retrieved_chunks)
        ],
    }
    
    
def index_document_pages(
    user_name: str,
    subject: str,
    material_id: int,
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    collection = get_collection()
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    total_chunk_count = 0
    
    for page_item in pages:
        page_number = page_item.get("page")
        page_text = page_item.get("text", "")
        
        chunks = split_text_into_chunks(page_text)
        
        for chunk_index, chunk in enumerate(chunks):
            chunk_id = f"{user_name}-{subject}-{material_id}-p{page_number}-c{chunk_index}"
            
            embedding = create_embedding(chunk)
            
            ids.append(chunk_id)
            documents.append(chunk)
            embeddings.append(embedding)
            metadatas.append(
                {
                    "user_name": user_name,
                    "subject": subject,
                    "material_id": material_id,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                }
            )
            
            total_chunk_count += 1
            
    if not documents:
        return {
            "success": False,
            "message": "인덱싱할 페이지 텍스트가 없습니다.",
        }
        
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    return {
        "success": True,
        "message": "페이지 단위 문서 인덱싱이 완료되었습니다.",
        "chunk_count": total_chunk_count,
        "material_id": material_id,
    }
    
    
def list_indexed_documents(
    user_name: str | None = None,
    subject: str | None = None,
) -> dict[str, Any]:
    collection = get_collection()
    
    where_conditions = []
    
    if user_name:
        where_conditions.append({"user_name": {"$eq": user_name}})
        
    if subject:
        where_conditions.append({"subject": {"$eq": subject}})
        
    where_filter = None
    
    if len(where_conditions) == 1:
        where_filter = where_conditions[0]
    elif len(where_conditions) > 1:
        where_filter = {"$and": where_conditions}
        
    if where_filter:
        results = collection.get(
            where=where_filter,
            include=["metadatas"],
        )
    else:
        results = collection.get(
            include=["metadatas"],
        )
        
    metadatas = results.get("metadatas", [])
    
    document_map = {}
    
    for metadata in metadatas:
        material_id = metadata.get("material_id")
        doc_user_name = metadata.get("user_name")
        doc_subject = metadata.get("subject")
        
        key = f"{doc_user_name}-{doc_subject}-{material_id}"
        
        if key not in document_map:
            document_map[key] = {
                "user_name": doc_user_name,
                "subject": doc_subject,
                "material_id": material_id,
                "chunk_count": 0,
                "pages": set(),
            }
            
        document_map[key]["chunk_count"] += 1
        
        page_number = metadata.get("page_number")
        if page_number is not None:
            document_map[key]["pages"].add(page_number)
            
    documents = []
    
    for item in document_map.values():
        pages = sorted(list(item["pages"]))
        
        documents.append(
            {
                "user_name": item["user_name"],
                "subject": item["subject"],
                "material_id": item["material_id"],
                "chunk_count": item["chunk_count"],
                "pages": pages,
                "page_count": len(pages),
            }
        )
        
    documents.sort(
        key=lambda item: (
            item["user_name"] or "",
            item["subject"] or "",
            item["material_id"] or 0,
        )
    )
    
    return {
        "success": True,
        "document_count": len(documents),
        "documents": documents,
    }
    
    
def delete_indexed_document(
    user_name: str,
    subject: str,
    material_id: int,
) -> dict[str, Any]:
    collection = get_collection()
    
    where_filter = {
        "$and": [
            {"user_name": {"$eq": user_name}},
            {"subject": {"$eq": subject}},
            {"material_id": {"$eq": material_id}},
        ]
    }
    
    existing = collection.get(
        where=where_filter,
        include=["metadatas"],
    )
    
    ids = existing.get("ids", [])
    
    if not ids:
        return {
            "success": False,
            "message": "삭제할 인덱싱 문서를 찾지 못했습니다.",
            "deleted_count": 0,
        }
        
    collection.delete(ids=ids)
    
    return {
        "success": True,
        "message": "인덱싱 문서가 삭제되었습니다.",
        "deleted_count": len(ids),
        "material_id": material_id,
    }