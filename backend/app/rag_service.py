import os
from typing import Any

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OpenAI_API_KEY = os.getenv("OPEN_API_KEY")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))

client = OpenAI(api_key=OpenAI_API_KEY) if OpenAI_API_KEY else None

chroma_client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT
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
        model="text-embedding-3-small",
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
) -> list[dict[str, Any]]:
    collection = get_collection()
    query_embedding = create_embedding(question)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "$and": [
                {"user_name": {"$eq": user_name}},
                {"subject": {"$eq": subject}},
            ]
        },
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
    
    prompt = f"""
너는 컴퓨터소프트웨어학 전공 학습을 돕는 RAG 기반 튜터다.

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
        model="gpt-4.1-mini",
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