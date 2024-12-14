import pytest
from unittest.mock import Mock, AsyncMock
from src.web_scraping.url_processor import URLProcessor, ProcessingResult

@pytest.fixture
def mock_handlers():
    return {
        'browser_handler': Mock(get_page_content=AsyncMock(return_value="<html>Test</html>")),
        'captcha_handler': Mock(
            is_captcha_present=Mock(return_value=False),
            solve_captcha=AsyncMock()
        ),
        'link_extractor': Mock(extract_links=AsyncMock(return_value=["http://test.com"])),
        'html_converter': Mock(convert_to_markdown=AsyncMock(return_value="# Test"))
    }

@pytest.fixture
def url_processor(mock_handlers):
    return URLProcessor(
        browser_handler=mock_handlers['browser_handler'],
        captcha_handler=mock_handlers['captcha_handler'],
        link_extractor=mock_handlers['link_extractor'],
        html_converter=mock_handlers['html_converter']
    )

@pytest.mark.asyncio
async def test_process_valid_url(url_processor):
    result = await url_processor.process_url("http://example.com")
    assert result.success
    assert result.markdown_content == "# Test"
    assert result.extracted_links == ["http://test.com"]

@pytest.mark.asyncio
async def test_process_invalid_url(url_processor):
    result = await url_processor.process_url("invalid-url")
    assert not result.success
    assert "Invalid URL format" in result.error

@pytest.mark.asyncio
async def test_process_multiple_urls(url_processor):
    urls = ["http://example1.com", "http://example2.com"]
    results = await url_processor.process_urls(urls)
    assert len(results) == 2
    assert all(result.success for result in results)

@pytest.mark.asyncio
async def test_captcha_handling(mock_handlers, url_processor):
    mock_handlers['captcha_handler'].is_captcha_present.return_value = True
    mock_handlers['captcha_handler'].solve_captcha.return_value = "<html>Solved</html>"
    
    result = await url_processor.process_url("http://example.com")
    assert result.success
    assert mock_handlers['captcha_handler'].solve_captcha.called

@pytest.mark.asyncio
async def test_retry_mechanism(mock_handlers, url_processor):
    mock_handlers['browser_handler'].get_page_content.side_effect = [
        Exception("First attempt failed"),
        "<html>Success</html>"
    ]
    
    result = await url_processor.process_url("http://example.com")
    assert result.success
    assert mock_handlers['browser_handler'].get_page_content.call_count == 2 

@pytest.mark.asyncio
async def test_process_url_with_network_error(mock_handlers, url_processor):
    mock_handlers['browser_handler'].get_page_content.side_effect = ConnectionError("Network error")
    
    result = await url_processor.process_url("http://example.com")
    assert not result.success
    assert "Network error" in result.error

@pytest.mark.asyncio
async def test_process_url_with_max_retries_exceeded(mock_handlers, url_processor):
    mock_handlers['browser_handler'].get_page_content.side_effect = [
        Exception("Attempt 1"),
        Exception("Attempt 2"),
        Exception("Attempt 3"),
    ]
    
    result = await url_processor.process_url("http://example.com", max_retries=3)
    assert not result.success
    assert mock_handlers['browser_handler'].get_page_content.call_count == 3

@pytest.mark.asyncio
async def test_empty_url_list(url_processor):
    results = await url_processor.process_urls([])
    assert isinstance(results, list)
    assert len(results) == 0