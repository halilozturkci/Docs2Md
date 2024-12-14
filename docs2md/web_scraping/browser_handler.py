"""
Browser handler module for web scraping.
"""

import logging
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser, Error as PlaywrightError

logger = logging.getLogger(__name__)

class BrowserHandler:
    """Handles browser interactions for web scraping."""
    
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
        wait_for_js: bool = False,
        user_agent: Optional[str] = None
    ):
        """Initialize the browser handler.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Page load timeout in seconds
            wait_for_js: Whether to wait for JavaScript execution
            user_agent: Custom user agent string
        """
        self.headless = headless
        self.timeout = timeout * 1000  # Convert to milliseconds
        self.wait_for_js = wait_for_js
        self.user_agent = user_agent
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def get_page_content(self, url: str) -> str:
        """
        Get the content of a webpage.
        
        Args:
            url: The URL to fetch content from
            
        Returns:
            The page content as HTML string
            
        Raises:
            PlaywrightError: If there's an error during page load
        """
        try:
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(headless=self.headless)
                
                # Create new page
                self.page = await self.browser.new_page()
                
                # Set user agent if provided
                if self.user_agent:
                    await self.page.set_extra_http_headers({"User-Agent": self.user_agent})
                
                # Navigate to URL with timeout
                await self.page.goto(url, timeout=self.timeout)
                
                # Wait for JavaScript if enabled
                if self.wait_for_js:
                    await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
                    # Additional wait for dynamic content
                    await asyncio.sleep(2)
                
                # Get page content
                content = await self.page.content()
                
                return content
                
        except PlaywrightError as e:
            logger.error(f"Failed to get content from {url}: {str(e)}")
            raise
        
        finally:
            # Clean up
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
                
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    