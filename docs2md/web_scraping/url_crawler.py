"""
URL Crawler module for fetching and validating URLs.
"""

import httpx
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class URLCrawler:
    """Handles URL crawling and validation operations."""
    
    VALID_SCHEMES = {'http', 'https'}
    DEFAULT_USER_AGENT = 'Docs2Md-Crawler/1.0'
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        proxy: Optional[Dict[str, str]] = None,
        user_agent: Optional[str] = None,
        verify_ssl: bool = True
    ):
        """
        Initialize the URL crawler.
        
        Args:
            timeout (int): Request timeout in seconds
            max_retries (int): Maximum number of retry attempts
            proxy (Optional[Dict[str, str]]): Proxy configuration (e.g., {'http': 'http://proxy:8080', 'https': 'http://proxy:8080'})
            user_agent (Optional[str]): Custom User-Agent string
            verify_ssl (bool): Whether to verify SSL certificates
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy = proxy
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.verify_ssl = verify_ssl
        
        # Configure client with proxy and SSL settings
        client_config = {
            'timeout': timeout,
            'follow_redirects': True,
            'verify': verify_ssl
        }
        
        if proxy:
            client_config['proxies'] = proxy
            
        self.client = httpx.Client(**client_config)
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if the given URL is properly formatted and uses an allowed protocol.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid and uses HTTP/HTTPS, False otherwise
        """
        try:
            result = urlparse(url)
            return bool(result.scheme in self.VALID_SCHEMES and result.netloc)
        except Exception as e:
            logger.error(f"URL validation error for {url}: {str(e)}")
            return False
    
    def fetch_url(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        override_user_agent: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch content from the given URL with retry mechanism.
        
        Args:
            url (str): URL to fetch
            headers (Optional[Dict[str, str]]): Optional request headers
            override_user_agent (Optional[str]): Temporarily override the default User-Agent for this request
            
        Returns:
            Optional[str]: Page content if successful, None otherwise
        """
        if not self.validate_url(url):
            logger.error(f"Invalid URL format: {url}")
            return None
        
        # Prepare headers with User-Agent
        request_headers = headers or {}
        if 'User-Agent' not in request_headers:
            request_headers['User-Agent'] = override_user_agent or self.user_agent
            
        for attempt in range(self.max_retries):
            try:
                response = self.client.get(url, headers=request_headers)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries reached for {url}")
                    return None
    
    def update_proxy(self, proxy: Optional[Dict[str, str]]) -> None:
        """
        Update proxy configuration and reinitialize the client.
        
        Args:
            proxy (Optional[Dict[str, str]]): New proxy configuration
        """
        self.proxy = proxy
        self.client.close()
        client_config = {
            'timeout': self.timeout,
            'follow_redirects': True,
            'verify': self.verify_ssl
        }
        if proxy:
            client_config['proxies'] = proxy
        self.client = httpx.Client(**client_config)
    
    def update_ssl_verification(self, verify_ssl: bool) -> None:
        """
        Update SSL verification setting and reinitialize the client.
        
        Args:
            verify_ssl (bool): Whether to verify SSL certificates
        """
        self.verify_ssl = verify_ssl
        self.client.close()
        client_config = {
            'timeout': self.timeout,
            'follow_redirects': True,
            'verify': verify_ssl
        }
        if self.proxy:
            client_config['proxies'] = self.proxy
        self.client = httpx.Client(**client_config)
    
    def __del__(self):
        """Cleanup method to close the HTTP client."""
        self.client.close() 