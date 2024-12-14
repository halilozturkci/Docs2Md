"""
Tests for the browser handler module.
"""

import pytest
import pytest_asyncio
import asyncio
from playwright.async_api import (
    Error as PlaywrightError,
    TimeoutError,
    Page,
    Browser
)
from src.web_scraping.browser_handler import (
    BrowserHandler,
    BrowserType,
    InteractionType,
    PageInteraction,
    PageState
)
from .test_server import TestServerContext

@pytest_asyncio.fixture(scope='function')
async def browser():
    """Create a browser instance for testing."""
    handler = BrowserHandler(
        browser_type=BrowserType.CHROMIUM,
        headless=True,
        viewport={'width': 1024, 'height': 768}
    )
    await handler.start()
    yield handler
    try:
        await handler.stop()
    except PlaywrightError:
        pass  # Ignore errors during cleanup

@pytest.fixture
def test_page_content():
    """HTML content for testing dynamic interactions."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <style>
            .hidden { display: none; }
            .visible { display: block; }
        </style>
    </head>
    <body>
        <h1>Dynamic Content Test</h1>
        
        <!-- Click test -->
        <button id="showContent">Show Content</button>
        <div id="hiddenContent" class="hidden">
            Hidden content revealed!
        </div>
        
        <!-- Type test -->
        <input type="text" id="textInput" placeholder="Type here...">
        <div id="textOutput"></div>
        
        <!-- Scroll test -->
        <div style="height: 2000px;">
            <div id="bottomContent" style="margin-top: 1900px;">
                Bottom content
            </div>
        </div>
        
        <script>
            // Click handler
            document.getElementById('showContent').addEventListener('click', () => {
                const content = document.getElementById('hiddenContent');
                content.className = content.className === 'hidden' ? 'visible' : 'hidden';
            });
            
            // Input handler
            document.getElementById('textInput').addEventListener('input', (e) => {
                document.getElementById('textOutput').textContent = e.target.value;
            });
        </script>
    </body>
    </html>
    """

@pytest.mark.asyncio
async def test_browser_initialization(browser):
    """Test browser initialization and cleanup."""
    assert browser._browser is not None
    assert browser._context is not None
    assert browser._page is not None

@pytest.mark.asyncio
async def test_navigation(browser, test_page_content):
    """Test page navigation and state capture."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        # Navigate to test page
        state = await browser.navigate(urls['test.html'])
        
        # Verify navigation result
        assert state.url == urls['test.html']
        assert state.title == "Test Page"
        assert state.content is not None
        assert state.cookies is not None

@pytest.mark.asyncio
async def test_click_interaction(browser, test_page_content):
    """Test click interaction and content visibility."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Create click interaction
        click = PageInteraction(
            type=InteractionType.CLICK,
            selector="#showContent"
        )
        
        # Perform click
        state = await browser.interact(click)
        
        # Verify content visibility
        assert 'visible' in state.content
        assert 'Hidden content revealed!' in state.content

@pytest.mark.asyncio
async def test_type_interaction(browser, test_page_content):
    """Test typing interaction and content update."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Create type interaction
        text_input = PageInteraction(
            type=InteractionType.TYPE,
            selector="#textInput",
            value="Test input"
        )
        
        # Perform typing
        state = await browser.interact(text_input)
        
        # Verify input reflection
        assert 'Test input' in state.content

@pytest.mark.asyncio
async def test_scroll_interaction(browser, test_page_content):
    """Test scroll interaction and viewport position."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Create scroll interaction
        scroll = PageInteraction(
            type=InteractionType.SCROLL,
            selector="window.scrollTo",
            value=2000
        )
        
        # Perform scroll and wait for it to complete
        state = await browser.interact([
            scroll,
            PageInteraction(
                type=InteractionType.WAIT,
                selector="#bottomContent",
                value="#bottomContent",
                timeout=5000
            )
        ])
        
        # Verify bottom content is in viewport
        assert 'Bottom content' in state.content

@pytest.mark.asyncio
async def test_wait_interaction(browser, test_page_content):
    """Test wait interaction and element visibility."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Create interactions sequence
        interactions = [
            PageInteraction(
                type=InteractionType.CLICK,
                selector="#showContent"
            ),
            PageInteraction(
                type=InteractionType.WAIT,
                selector="#hiddenContent.visible",
                value="#hiddenContent.visible",
                timeout=5000
            )
        ]
        
        # Perform interactions
        state = await browser.interact(interactions)
        
        # Verify element visibility
        assert 'visible' in state.content

@pytest.mark.asyncio
async def test_custom_interaction(browser, test_page_content):
    """Test custom JavaScript interaction."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Create custom interaction
        custom = PageInteraction(
            type=InteractionType.CUSTOM,
            selector="() => document.querySelector('#hiddenContent').className = 'visible'",
        )
        
        # Perform custom interaction
        state = await browser.interact(custom)
        
        # Verify result
        assert 'visible' in state.content

@pytest.mark.asyncio
async def test_screenshot_capture(browser, test_page_content):
    """Test screenshot capture functionality."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Perform interaction with screenshot
        state = await browser.interact(
            PageInteraction(
                type=InteractionType.CLICK,
                selector="#showContent"
            ),
            capture_screenshot=True
        )
        
        # Verify screenshot
        assert state.screenshot is not None
        assert len(state.screenshot) > 0

@pytest.mark.asyncio
async def test_error_handling(browser):
    """Test error handling for various scenarios."""
    
    # Test invalid navigation
    with pytest.raises(PlaywrightError):
        await browser.navigate("invalid://url")
    
    # Test invalid selector
    async with TestServerContext({'test.html': '<html><body>Test</body></html>'}) as urls:
        await browser.navigate(urls['test.html'])
        
        with pytest.raises(PlaywrightError):
            await browser.interact(
                PageInteraction(
                    type=InteractionType.CLICK,
                    selector="#nonexistent",
                    timeout=1000
                )
            )
        
        # Test timeout error
        with pytest.raises(PlaywrightError) as exc_info:
            await browser.interact(
                PageInteraction(
                    type=InteractionType.WAIT,
                    selector="#nonexistent",
                    value="#nonexistent",
                    timeout=1
                )
            )
        assert "Timeout" in str(exc_info.value)
        assert "1ms exceeded" in str(exc_info.value)

@pytest.mark.asyncio
async def test_multiple_interactions(browser, test_page_content):
    """Test multiple sequential interactions."""
    async with TestServerContext({'test.html': test_page_content}) as urls:
        await browser.navigate(urls['test.html'])
        
        # Create interaction sequence
        interactions = [
            PageInteraction(
                type=InteractionType.CLICK,
                selector="#showContent",
                timeout=5000
            ),
            PageInteraction(
                type=InteractionType.TYPE,
                selector="#textInput",
                value="Test input",
                timeout=5000
            ),
            PageInteraction(
                type=InteractionType.SCROLL,
                selector="window.scrollTo",
                value=1000
            )
        ]
        
        # Perform interactions
        state = await browser.interact(interactions)
        
        # Verify results
        assert 'visible' in state.content
        assert 'Test input' in state.content
  