"""
Tests for the URL crawler module.
"""

import pytest
from src.web_scraping.url_crawler import URLCrawler

def test_url_validation():
    crawler = URLCrawler()
    
    # Test valid URLs
    assert crawler.validate_url("https://example.com")
    assert crawler.validate_url("http://test.com/path?param=value")
    
    # Test invalid URLs
    assert not crawler.validate_url("not_a_url")
    assert not crawler.validate_url("ftp://invalid")
    assert not crawler.validate_url("")

def test_url_fetch():
    crawler = URLCrawler()
    
    # Test successful fetch
    content = crawler.fetch_url("https://example.com")
    assert content is not None
    assert isinstance(content, str)
    
    # Test invalid URL fetch
    content = crawler.fetch_url("https://invalid.example.com")
    assert content is None

def test_retry_mechanism():
    crawler = URLCrawler(max_retries=2)
    
    # Test with non-existent domain
    content = crawler.fetch_url("https://this-domain-does-not-exist-123.com")
    assert content is None

def test_custom_user_agent():
    custom_ua = "CustomBot/1.0"
    crawler = URLCrawler(user_agent=custom_ua)
    
    # Test default User-Agent
    content = crawler.fetch_url("https://httpbin.org/user-agent")
    assert custom_ua in content
    
    # Test override User-Agent
    override_ua = "OverrideBot/1.0"
    content = crawler.fetch_url("https://httpbin.org/user-agent", override_user_agent=override_ua)
    assert override_ua in content

def test_proxy_configuration():
    # Note: This test requires a working proxy server
    # For testing purposes, you might want to use a mock or skip this test
    proxy_config = {
        "http://": "http://localhost:8080",
        "https://": "http://localhost:8080"
    }
    crawler = URLCrawler(proxy=proxy_config)
    
    # Test proxy update
    new_proxy = {
        "http://": "http://localhost:8081",
        "https://": "http://localhost:8081"
    }
    crawler.update_proxy(new_proxy)
    assert crawler.proxy == new_proxy

def test_ssl_verification():
    # Test with SSL verification enabled (default)
    crawler = URLCrawler()
    assert crawler.verify_ssl is True
    
    # Test with SSL verification disabled
    crawler = URLCrawler(verify_ssl=False)
    assert crawler.verify_ssl is False
    
    # Test SSL verification update
    crawler.update_ssl_verification(True)
    assert crawler.verify_ssl is True