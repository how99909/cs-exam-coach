from api.client import ApiClient


def test_auth_header_is_added():
    client = ApiClient(
        access_token="test-token"
    )
    
    headers = client._headers()
    
    assert headers == {
        "Authorization": "Bearer test-token"
    }
    
    
def test_auth_header_is_not_added_without_token():
    client = ApiClient()
    
    assert client._headers() == {}
    
    
def test_existing_headers_are_preserved():
    client = ApiClient(
        access_token="test-token"
    )
    
    headers = client._headers(
        {
            "X-Test": "value",
        }
    )
    
    assert headers["X-Test"] == "value"
    
    assert headers["Authorization"] == "Bearer test-token"
    
    
def test_get_uses_expected_url(
    monkeypatch,
):
    captured = {}
    
    def fake_request(**kwargs):
        captured.update(kwargs)
        return object()
    
    monkeypatch.setattr(
        "api.client.requests.request",
        fake_request,
    )
    
    client = ApiClient(
        access_token="token"
    )
    
    client.get(
        "/test",
        params={"a": 1},
    )
    
    assert captured["method"] == "GET"
    assert captured["url"].endswith("/test")
    
    assert captured["headers"]["Authorization"] == "Bearer token"
    
    assert captured["params"] == {
        "a": 1
    }