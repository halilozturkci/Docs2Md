"""
Link extractor module for discovering, validating, and categorizing links in HTML content.
"""

import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class LinkExtractor:
    """Handles link extraction and validation from HTML content."""
    
    def __init__(self):
        """Initialize the link extractor."""
        self.logger = logging.getLogger(__name__)
        
    async def extract_links(self, html_content: str, base_url: Optional[str] = None) -> List[str]:
        """Extract and validate links from HTML content.
        
        Args:
            html_content: HTML content to extract links from
            base_url: Base URL for resolving relative links
            
        Returns:
            List of validated and processed links
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract all links
            links = set()
            
            # Find all elements with href or src attributes
            for tag in soup.find_all(['a', 'link', 'img', 'script', 'iframe']):
                href = tag.get('href') or tag.get('src')
                if href:
                    # Clean and validate the link
                    clean_link = self._clean_link(href, base_url)
                    if clean_link:
                        links.add(clean_link)
            
            return sorted(list(links))
            
        except Exception as e:
            self.logger.error(f"Failed to extract links: {str(e)}")
            return []
            
    def _clean_link(self, link: str, base_url: Optional[str] = None) -> Optional[str]:
        """Clean and validate a link.
        
        Args:
            link: Raw link to clean
            base_url: Base URL for resolving relative links
            
        Returns:
            Cleaned and validated link, or None if invalid
        """
        try:
            # Remove whitespace
            link = link.strip()
            
            # Skip empty links
            if not link:
                return None
                
            # Skip javascript: links
            if link.startswith('javascript:'):
                return None
                
            # Skip mailto: links
            if link.startswith('mailto:'):
                return None
                
            # Skip tel: links
            if link.startswith('tel:'):
                return None
                
            # Skip anchor links
            if link.startswith('#'):
                return None
                
            # Resolve relative links if base_url is provided
            if base_url and not urlparse(link).netloc:
                link = urljoin(base_url, link)
                
            # Validate URL format
            parsed = urlparse(link)
            if not all([parsed.scheme, parsed.netloc]):
                return None
                
            # Only allow http(s) schemes
            if parsed.scheme.lower() not in ['http', 'https']:
                return None
                
            return link
            
        except Exception:
            return None