from app import rag_service


class FakeCollection:
    def __init__(self):
        self.upsert_calls = []
        self.query_calls = []
        self.get_calls = []
        self.delete_calls = []
        
        self.query_result = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        
        self.get_result = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        
    def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)
        
    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return self.query_result
    
    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return self.get_result
    
    def delete(self, **kwargs):
        self.delete_calls.append(kwargs)
        
        
def test_index_document_stores_user_metadata(
    monkeypatch,
):
    collection = FakeCollection()
    
    monkeypatch.setattr(
        rag_service,
        "get_collection",
        lambda: collection,
    )
    
    monkeypatch.setattr(
        rag_service,
        "create_embedding",
        lambda text: [0.1, 0.2],
    )
    
    result = rag_service.index_document(
        user_name="user_a",
        subject="algorithms",
        material_id=10,
        content="BFS searches graph level by level."
    )
    
    assert result["success"] is True
    assert len(collection.upsert_calls) == 1
    
    call = collection.upsert_calls[0]
    
    metadata = call["metadatas"][0]
    
    assert metadata["user_name"] == "user_a"
    assert metadata["subject"] == "algorithms"
    assert metadata["material_id"] == 10
    
    
def test_retrieve_chunks_scopes_query_to_user(
    monkeypatch,
):
    collection = FakeCollection()
    
    collection.query_result = {
        "documents": [["BFS content"]],
        "metadatas": [[
            {
                "user_name": "user_a",
                "subject": "algorithms",
                "material_id": 10,
                "chunk_index": 0,
            }
        ]],
        "distances": [[0.1]],
    }
    
    monkeypatch.setattr(
        rag_service,
        "get_collection",
        lambda: collection,
    )
    
    monkeypatch.setattr(
        rag_service,
        "create_embedding",
        lambda text: [0.1, 0.2],
    )
    
    result = rag_service.retrieve_chunks(
        user_name="user_a",
        subject="algorithms",
        question="What is BFS?",
        material_id=10,
    )
    
    assert len(result) == 1
    
    call = collection.query_calls[0]
    
    assert call["where"] == {
        "$and": [
            {"user_name": {"$eq": "user_a"}},
            {"subject": {"$eq": "algorithms"}},
            {"material_id": {"$eq": 10}},
        ]
    }
    
    
def test_retrieve_chunks_without_material_still_scopes_user(
    monkeypatch,
):
    collection = FakeCollection()
    
    monkeypatch.setattr(
        rag_service,
        "get_collection",
        lambda: collection,
    )
    
    monkeypatch.setattr(
        rag_service,
        "create_embedding",
        lambda text: [0.1],
    )
    
    rag_service.retrieve_chunks(
        user_name="user_a",
        subject="os",
        question="virtual memory",
    )
    
    call = collection.query_calls[0]
    
    assert call["where"] == {
        "$and": [
            {"user_name": {"$eq": "user_a"}},
            {"subject": {"$eq": "os"}},
        ]
    }
    
    
def test_list_documents_scopes_to_user(
    monkeypatch,
):
    collection = FakeCollection()
    
    collection.get_result = {
        "ids": ["chunk-1"],
        "metadata": [
            {
                "user_name": "user_a",
                "subject": "algorithms",
                "material_id": 10,
                "chunk_index": 0,
            }
        ],
    }
    
    monkeypatch.setattr(
        rag_service,
        "get_collection",
        lambda: collection,
    )
    
    result = rag_service.list_indexed_documents(
        user_name="user_a",
    )
    
    call = collection.get_calls[0]
    
    assert call["where"] == {
        "user_name": {
            "$eq": "user_a",
        }
    }
    
    assert result["document_count"] == 1
    assert result["documents"][0]["material_id"] == 10
    
    
def test_delete_document_scopes_to_user(
    monkeypatch,
):
    collection = FakeCollection()
    
    collection.get_result = {
        "ids": ["chunk-1", "chunk-2"],
        "metadatas": [
            {},
            {},
        ],
    }
    
    monkeypatch.setattr(
        rag_service,
        "get_collection",
        lambda: collection,
    )
    
    result = rag_service.delete_indexed_document(
        user_name="user_a",
        subject="algorithms",
        material_id=10,
    )
    
    assert result["success"] is True
    assert result["deleted_count"] == 2
    
    get_call = collection.get_calls[0]
    
    assert get_call["where"] == {
        "$and": [
            {"user_name": {"$eq": "user_a"}},
            {"subject": {"$eq": "algorithms"}},
            {"material_id": {"$eq": 10}},
        ]
    }
    
    assert collection.delete_calls[0] == {
        "ids": ["chunk-1", "chunk-2"],
    }
    
    
def test_index_document_pages_stores_page_metadata(
    monkeypatch,
):
    collection = FakeCollection()
    
    monkeypatch.setattr(
        rag_service,
        "get_collection",
        lambda: collection,
    )
    
    monkeypatch.setattr(
        rag_service,
        "create_embedding",
        lambda text: [0.1],
    )
    
    result = rag_service.index_document_pages(
        user_name="user_a",
        subject="os",
        material_id=20,
        pages=[
            {
                "page": 3,
                "text": "Virtual memory and paging.",
            }
        ],
    )
    
    assert result["success"] is True
    
    metadata = (
        collection.upsert_calls[0]["metadatas"][0]
    )
    
    assert metadata["user_name"] == "user_a"
    assert metadata["material_id"] == 20
    assert metadata["page_number"] == 3
    assert metadata["chunk_index"] == 0