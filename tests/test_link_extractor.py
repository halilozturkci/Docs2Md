"""
Tests for the link extractor module.
"""

import pytest
from src.web_scraping.link_extractor import LinkExtractor, LinkType, Link

@pytest.fixture
def base_url():
    return "https://example.com"

@pytest.fixture
def extractor(base_url):
    return LinkExtractor(base_url)

@pytest.fixture
def sample_html():
    return """
    <html>
        <head>
            <title>Test Page</title>
            <link rel="stylesheet" href="/styles.css">
            <script src="/script.js"></script>
        </head>
        <body>
            <h1>Links Test</h1>
            
            <!-- Internal links -->
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            
            <!-- External links -->
            <a href="https://external.com">External Site</a>
            <a href="https://another.com/page">Another Site</a>
            
            <!-- Resource links -->
            <img src="/images/test.jpg" alt="Test Image">
            <a href="/files/document.pdf">Download PDF</a>
            
            <!-- Special links -->
            <a href="#section">Section Link</a>
            <a href="mailto:test@example.com">Email Us</a>
            
            <!-- Invalid links -->
            <a href="">Empty Link</a>
            <a href="javascript:void(0)">JavaScript Link</a>
        </body>
    </html>
    """

def test_link_extraction(extractor, sample_html):
    links = extractor.extract_links(sample_html)
    
    # Check if links were extracted
    assert links
    assert len(links) > 0
    
    # Verify that all returned objects are Link instances
    assert all(isinstance(link, Link) for link in links)

def test_internal_links(extractor, sample_html):
    links = extractor.extract_links(sample_html)
    internal_links = [link for link in links if link.type == LinkType.INTERNAL]
    
    # Check internal links
    assert any(link.url.endswith('/page1') for link in internal_links)
    assert any(link.url.endswith('/page2') for link in internal_links)

def test_external_links(extractor, sample_html):
    # Configure extractor to follow external links
    extractor.follow_external = True
    links = extractor.extract_links(sample_html)
    external_links = [link for link in links if link.type == LinkType.EXTERNAL]
    
    # Check external links
    assert any('external.com' in link.url for link in external_links)
    assert any('another.com' in link.url for link in external_links)

def test_resource_links(extractor, sample_html):
    links = extractor.extract_links(sample_html)
    resource_links = [link for link in links if link.type == LinkType.RESOURCE]
    
    # Check resource links
    assert any(link.url.endswith('.jpg') for link in resource_links)
    assert any(link.url.endswith('.pdf') for link in resource_links)
    assert any(link.url.endswith('.css') for link in resource_links)
    assert any(link.url.endswith('.js') for link in resource_links)

def test_special_links(extractor, sample_html):
    links = extractor.extract_links(sample_html)
    
    # Check anchor links
    anchor_links = [link for link in links if link.type == LinkType.ANCHOR]
    assert any(link.url.endswith('#section') for link in anchor_links)
    
    # Check mailto links (should be filtered out by default)
    mailto_links = [link for link in links if link.type == LinkType.MAIL]
    assert not mailto_links

def test_link_attributes(extractor, sample_html):
    links = extractor.extract_links(sample_html)
    
    # Check if attributes are preserved
    img_links = [link for link in links if link.element == 'img']
    assert any(link.attributes.get('alt') == 'Test Image' for link in img_links)

def test_link_depth(base_url):
    # Create extractor with max depth
    extractor = LinkExtractor(base_url, max_depth=2)
    
    # Create nested HTML with explicit depth indicators
    html = """
    <div class="depth-0">
        <a href="/depth0">Depth 0 Link</a>
        <div class="depth-1">
            <a href="/depth1">Depth 1 Link</a>
            <div class="depth-2">
                <a href="/depth2">Depth 2 Link</a>
            </div>
        </div>
    </div>
    """
    
    # Test depth 0
    links = extractor.extract_links(html, current_depth=0)
    assert len(links) == 1
    assert links[0].url.endswith('/depth0')
    
    # Test depth 1
    links = extractor.extract_links(html, current_depth=1)
    assert len(links) == 1
    assert links[0].url.endswith('/depth1')
    
    # Test depth 2
    links = extractor.extract_links(html, current_depth=2)
    assert len(links) == 1
    assert links[0].url.endswith('/depth2')

def test_url_normalization(extractor):
    # Test various URL formats
    urls = [
        ('http://example.com/page/', 'http://example.com/page'),
        ('http://example.com:80/page', 'http://example.com/page'),
        ('https://example.com:443/page', 'https://example.com/page'),
        ('/relative/path', 'https://example.com/relative/path'),
        ('page.html', 'https://example.com/page.html'),
        ('http://example.com/page#section', 'http://example.com/page'),
    ]
    
    for input_url, expected_url in urls:
        assert extractor._normalize_url(input_url) == expected_url

def test_link_statistics(extractor, sample_html):
    # Configure extractor to follow external links
    extractor.follow_external = True
    
    # Extract links and get statistics
    links = extractor.extract_links(sample_html)
    stats = extractor.get_link_statistics()
    
    # Check statistics
    assert len(links) > 0  # Should have extracted some links
    assert stats['total_processed'] > 0
    assert 'INTERNAL' in stats
    assert 'RESOURCE' in stats
    # External links should be present since follow_external is True
    assert any(link.type == LinkType.EXTERNAL for link in links)

def test_error_handling(extractor):
    # Test with invalid HTML
    links = extractor.extract_links("<<<invalid>html>")
    assert not links
    
    # Test with empty content
    links = extractor.extract_links("")
    assert not links
    
    # Test with None content
    links = extractor.extract_links(None)
    assert not links