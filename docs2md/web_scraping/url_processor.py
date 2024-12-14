from typing import List, Optional, Dict
from urllib.parse import urlparse
import logging
import asyncio
from dataclasses import dataclass

from .browser_handler import BrowserHandler
from .captcha_handler import CaptchaHandler
from .link_extractor import LinkExtractor
from .html_converter import HTMLConverter

@dataclass
class ProcessingResult:
    url: str
    markdown_content: str
    extracted_links: List[str]
    success: bool
    error: Optional[str] = None

class URLProcessor:
    def __init__(
        self,
        browser_handler: Optional[BrowserHandler] = None,
        captcha_handler: Optional[CaptchaHandler] = None,
        link_extractor: Optional[LinkExtractor] = None,
        html_converter: Optional[HTMLConverter] = None
    ):
        self.browser_handler = browser_handler or BrowserHandler()
        self.captcha_handler = captcha_handler or CaptchaHandler()
        self.link_extractor = link_extractor or LinkExtractor()
        self.html_converter = html_converter or HTMLConverter()
        self.logger = logging.getLogger(__name__)

    async def process_url(self, url: str, max_retries: int = 3) -> ProcessingResult:
        """
        Process a single URL through the entire pipeline.
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid URL format: {url}")

            # Initialize result
            result = ProcessingResult(
                url=url,
                markdown_content="",
                extracted_links=[],
                success=False
            )

            # Process with retries
            for attempt in range(max_retries):
                try:
                    # Get page content
                    page_content = await self.browser_handler.get_page_content(url)

                    # Handle CAPTCHA if present
                    if self.captcha_handler.is_captcha_present(page_content):
                        page_content = await self.captcha_handler.solve_captcha(
                            url, 
                            self.browser_handler
                        )

                    # Extract links
                    result.extracted_links = await self.link_extractor.extract_links(
                        page_content,
                        base_url=url
                    )

                    # Convert to markdown
                    result.markdown_content = await self.html_converter.convert_to_markdown(
                        page_content
                    )

                    result.success = True
                    break

                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {url}. Retrying... Error: {str(e)}"
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            return result

        except Exception as e:
            self.logger.error(f"Failed to process URL {url}: {str(e)}")
            return ProcessingResult(
                url=url,
                markdown_content="",
                extracted_links=[],
                success=False,
                error=str(e)
            )

    async def process_urls(self, urls: List[str]) -> List[ProcessingResult]:
        """
        Process multiple URLs concurrently.
        """
        tasks = [self.process_url(url) for url in urls]
        return await asyncio.gather(*tasks)

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False 