"""
HTML to Markdown converter module.
"""

import logging
import html2text
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)

class HTMLConverter:
    """Converts HTML content to Markdown format."""
    
    def __init__(self):
        """Initialize the HTML converter."""
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = False
        self.converter.ignore_emphasis = False
        self.converter.body_width = 0  # No wrapping
        
    async def convert_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to Markdown.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            Converted Markdown content
        """
        try:
            # Clean HTML first
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'iframe', 'noscript']):
                element.decompose()
            
            # Convert to markdown
            markdown = self.converter.handle(str(soup))
            
            # Clean up markdown
            markdown = self._clean_markdown(markdown)
            
            return markdown
            
        except Exception as e:
            logger.error(f"Failed to convert HTML to Markdown: {str(e)}")
            raise
            
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up converted markdown content.
        
        Args:
            markdown: Raw markdown content
            
        Returns:
            Cleaned markdown content
        """
        # Remove multiple blank lines
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if not line.strip():
                if not prev_empty:
                    cleaned_lines.append(line)
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        # Join lines and ensure single newline at end
        cleaned = '\n'.join(cleaned_lines).strip() + '\n'
        
        # Remove unnecessary escaping
        cleaned = cleaned.replace('\\_', '_')
        cleaned = cleaned.replace('\\*', '*')
        cleaned = cleaned.replace('\\#', '#')
        
        return cleaned 