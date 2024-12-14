"""
Test server helper module for browser handler tests.
"""

import asyncio
from aiohttp import web
import logging
from typing import Optional, Dict, Any
import socket
from contextlib import closing

logger = logging.getLogger(__name__)

def find_free_port() -> int:
    """Find a free port to use for the test server."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

class TestServer:
    """Simple HTTP server for testing browser interactions."""
    
    def __init__(self, host: str = 'localhost', port: Optional[int] = None):
        """
        Initialize the test server.
        
        Args:
            host (str): Host to bind to
            port (Optional[int]): Port to bind to (if None, finds a free port)
        """
        self.host = host
        self.port = port or find_free_port()
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self._content_store: Dict[str, str] = {}
    
    @property
    def base_url(self) -> str:
        """Get the base URL of the test server."""
        return f"http://{self.host}:{self.port}"
    
    def add_page(self, path: str, content: str) -> str:
        """
        Add a page to the test server.
        
        Args:
            path (str): URL path for the page
            content (str): HTML content of the page
            
        Returns:
            str: Full URL of the page
        """
        # Normalize path
        if not path.startswith('/'):
            path = f"/{path}"
        
        # Store content
        self._content_store[path] = content
        
        return f"{self.base_url}{path}"
    
    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming HTTP requests."""
        try:
            # Get content for the path
            content = self._content_store.get(request.path)
            
            if content is None:
                return web.Response(
                    status=404,
                    text="Not Found"
                )
            
            return web.Response(
                status=200,
                body=content,
                content_type='text/html'
            )
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return web.Response(
                status=500,
                text="Internal Server Error"
            )
    
    async def start(self) -> None:
        """Start the test server."""
        try:
            # Set up request handler
            self.app.router.add_get('/{tail:.*}', self._handle_request)
            
            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            site = web.TCPSite(self.runner, self.host, self.port)
            await site.start()
            
            logger.info(f"Test server started at {self.base_url}")
            
        except Exception as e:
            logger.error(f"Error starting test server: {str(e)}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """Stop the test server."""
        try:
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
            logger.info("Test server stopped")
        except Exception as e:
            logger.error(f"Error stopping test server: {str(e)}")
            raise

class TestServerContext:
    """Context manager for test server."""
    
    def __init__(self, content: Dict[str, str]):
        """
        Initialize the test server context.
        
        Args:
            content (Dict[str, str]): Dictionary of path -> content mappings
        """
        self.server = TestServer()
        self.content = content
        self.urls: Dict[str, str] = {}
    
    async def __aenter__(self) -> Dict[str, str]:
        """Start server and add content."""
        await self.server.start()
        
        # Add all pages
        for path, content in self.content.items():
            self.urls[path] = self.server.add_page(path, content)
        
        return self.urls
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop server."""
        await self.server.stop() 