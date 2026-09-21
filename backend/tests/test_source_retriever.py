import hashlib

import httpx
import pytest

from app.integrations.source_retriever import (
    MAX_EXCERPT_LENGTH,
    MAX_REDIRECTS,
    MAX_RESPONSE_SIZE,
    HttpxSourceRetriever,
    RetrievalError,
    validate_destination,
)


def make_client(handler):
    return httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://172.16.0.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/",
        "http://[::1]/",
        "http://[fc00::1]/",
        "http://[fe80::1]/",
        "http://[::ffff:127.0.0.1]/",
    ],
)
def test_validate_destination_blocks_unsafe_ipv4_and_ipv6(url):
    with pytest.raises(RetrievalError) as error:
        validate_destination(url, resolve_hostname=False)

    assert error.value.category == "unsafe_destination"


def test_unsafe_destination_is_rejected_before_httpx_request(monkeypatch):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, text="should not be requested")

    retriever = HttpxSourceRetriever(make_client(handler))

    with pytest.raises(RetrievalError) as error:
        retriever.retrieve("http://127.0.0.1/")

    assert error.value.category == "unsafe_destination"
    assert calls == 0


def test_dns_resolution_to_private_address_is_rejected_before_httpx_request(monkeypatch):
    calls = 0

    def fake_getaddrinfo(*args, **kwargs):
        return [(None, None, None, None, ("10.0.0.1", 80))]

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, text="should not be requested")

    monkeypatch.setattr("app.integrations.source_retriever.socket.getaddrinfo", fake_getaddrinfo)

    with pytest.raises(RetrievalError) as error:
        HttpxSourceRetriever(make_client(handler)).retrieve("http://public.example/")

    assert error.value.category == "unsafe_destination"
    assert calls == 0


def test_safe_http_and_https_redirects_are_followed_and_revalidated():
    responses = {
        "http://93.184.216.34/": httpx.Response(302, headers={"location": "http://93.184.216.35/final"}),
        "http://93.184.216.35/final": httpx.Response(200, headers={"content-type": "text/plain"}, text="ok"),
    }

    def handler(request):
        return responses[str(request.url)]

    result = HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert result.final_url == "http://93.184.216.35/final"
    assert result.content == "ok"


def test_safe_https_redirect_is_followed():
    responses = {
        "https://93.184.216.34/": httpx.Response(301, headers={"location": "https://93.184.216.35/final"}),
        "https://93.184.216.35/final": httpx.Response(200, headers={"content-type": "text/plain"}, text="ok"),
    }

    result = HttpxSourceRetriever(make_client(lambda request: responses[str(request.url)])).retrieve(
        "https://93.184.216.34/"
    )

    assert result.final_url == "https://93.184.216.35/final"


@pytest.mark.parametrize(
    "location",
    [
        "http://127.0.0.1/",
        "http://10.0.0.1/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://169.254.169.254/",
        "file:///etc/passwd",
        "ftp://example.com/file",
    ],
)
def test_redirect_destination_is_revalidated(location):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(302, headers={"location": location})

    with pytest.raises(RetrievalError) as error:
        HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert error.value.category in {"unsafe_destination", "redirect_failure"}
    assert calls == 1


def test_maximum_redirect_count_is_enforced():
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(302, headers={"location": "http://93.184.216.34/"})

    with pytest.raises(RetrievalError) as error:
        HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert error.value.category == "redirect_failure"
    assert calls == MAX_REDIRECTS + 1


def test_response_size_limit_is_streamed_and_enforced():
    class OversizedStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"x" * (MAX_RESPONSE_SIZE + 1)

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            content=OversizedStream(),
        )

    with pytest.raises(RetrievalError) as error:
        HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert error.value.category == "response_too_large"


@pytest.mark.parametrize("content_type", ["application/pdf", "image/png", "video/mp4", "application/octet-stream"])
def test_unsupported_content_types_are_rejected(content_type):
    def handler(request):
        return httpx.Response(200, headers={"content-type": content_type}, content=b"binary")

    with pytest.raises(RetrievalError) as error:
        HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert error.value.category == "unsupported_content_type"


def test_html_extraction_normalizes_text_and_bounds_excerpt():
    html = b"<html><head><title> Title </title></head><body><h1>Heading</h1>  <p>First   paragraph</p><script>hidden</script></body></html>"

    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, content=html)

    result = HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert result.content == "Heading First paragraph"
    assert "<h1>" not in result.content
    assert "hidden" not in result.content
    assert result.source_title == "Title"
    assert len(result.content_excerpt) <= MAX_EXCERPT_LENGTH
    assert result.content_hash == hashlib.sha256(result.content.encode()).hexdigest()


def test_plain_text_extraction_normalizes_whitespace():
    def handler(request):
        return httpx.Response(200, headers={"content-type": "text/plain"}, text=" first\n\n second ")

    result = HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert result.content == "first second"
    assert result.content_hash == hashlib.sha256(b"first second").hexdigest()


@pytest.mark.parametrize(
    ("status_code", "expected_category"),
    [
        (404, "http_4xx"),
        (403, "http_4xx"),
        (500, "http_5xx"),
        (503, "http_5xx"),
    ],
)
def test_http_failures_are_categorized(status_code, expected_category):
    def handler(request):
        return httpx.Response(status_code)

    with pytest.raises(RetrievalError) as error:
        HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert error.value.category == expected_category
    assert error.value.http_status == status_code


def test_no_content_is_a_successful_empty_collection():
    def handler(request):
        return httpx.Response(204)

    result = HttpxSourceRetriever(make_client(handler)).retrieve("http://93.184.216.34/")

    assert result.http_status == 204
    assert result.content == ""
    assert result.content_hash == hashlib.sha256(b"").hexdigest()