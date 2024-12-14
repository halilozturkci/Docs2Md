"""
CAPTCHA handler module for solving CAPTCHAs and bypassing bot protection.

This module provides functionality to:
1. Solve various types of CAPTCHAs using 2captcha service
2. Bypass common bot protection mechanisms
3. Implement stealth mode features to avoid detection
"""

import logging
import asyncio
import json
import base64
from enum import Enum, auto
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from twocaptcha import TwoCaptcha
from playwright.async_api import Page, Error as PlaywrightError
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CaptchaType(Enum):
    """Types of CAPTCHAs that can be handled."""
    RECAPTCHA_V2 = auto()
    RECAPTCHA_V3 = auto()
    HCAPTCHA = auto()
    IMAGE_CAPTCHA = auto()
    TEXT_CAPTCHA = auto()

class StealthMode(Enum):
    """Different stealth modes for bot detection avoidance."""
    BASIC = auto()  # Basic evasion techniques
    MEDIUM = auto()  # More sophisticated evasion
    AGGRESSIVE = auto()  # Maximum stealth (might affect performance)

@dataclass
class CaptchaConfig:
    """Configuration for CAPTCHA solving."""
    api_key: str
    captcha_type: CaptchaType
    site_key: Optional[str] = None
    site_url: Optional[str] = None
    proxy: Optional[Dict[str, str]] = None
    extra_params: Optional[Dict[str, Any]] = None

class CaptchaHandler:
    """Handles CAPTCHA solving and bot protection bypassing."""
    
    def __init__(
        self,
        api_key: str,
        stealth_mode: StealthMode = StealthMode.BASIC,
        proxy: Optional[Dict[str, str]] = None,
        timeout: int = 120
    ):
        """Initialize CAPTCHA handler.
        
        Args:
            api_key: 2captcha API key
            stealth_mode: Level of stealth for bot detection avoidance
            proxy: Proxy configuration for CAPTCHA solving
            timeout: Timeout for CAPTCHA solving in seconds
        """
        self.solver = TwoCaptcha(api_key)
        self.stealth_mode = stealth_mode
        self.proxy = proxy
        self.timeout = timeout
        
        # Configure solver
        self.solver.timeout = timeout
        if proxy:
            self.solver.proxy = proxy
    
    async def solve_captcha(self, config: CaptchaConfig) -> str:
        """Solve a CAPTCHA using 2captcha service.
        
        Args:
            config: CAPTCHA configuration
            
        Returns:
            str: Solution token or text
            
        Raises:
            ValueError: If invalid configuration
            RuntimeError: If CAPTCHA solving fails
        """
        if not config.captcha_type:
            raise ValueError("CAPTCHA type must be specified")
            
        try:
            # Prepare solver parameters
            params = {
                'url': config.site_url,
                'sitekey': config.site_key,
                **(config.extra_params or {})
            }
            
            # Handle different CAPTCHA types
            if config.captcha_type == CaptchaType.RECAPTCHA_V2:
                result = await self._solve_recaptcha_v2(params)
            elif config.captcha_type == CaptchaType.RECAPTCHA_V3:
                result = await self._solve_recaptcha_v3(params)
            elif config.captcha_type == CaptchaType.HCAPTCHA:
                result = await self._solve_hcaptcha(params)
            elif config.captcha_type == CaptchaType.IMAGE_CAPTCHA:
                result = await self._solve_image_captcha(params)
            elif config.captcha_type == CaptchaType.TEXT_CAPTCHA:
                result = await self._solve_text_captcha(params)
            else:
                raise ValueError(f"Unsupported CAPTCHA type: {config.captcha_type}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to solve CAPTCHA: {e}")
    
    async def apply_stealth_mode(self, page: Page) -> None:
        """Apply stealth mode features to avoid bot detection.
        
        Args:
            page: Playwright page instance
            
        Raises:
            PlaywrightError: If stealth mode application fails
        """
        try:
            # Basic stealth features
            await self._apply_basic_stealth(page)
            
            # Additional features based on stealth mode
            if self.stealth_mode == StealthMode.MEDIUM:
                await self._apply_medium_stealth(page)
            elif self.stealth_mode == StealthMode.AGGRESSIVE:
                await self._apply_aggressive_stealth(page)
                
        except Exception as e:
            logger.error(f"Error applying stealth mode: {e}")
            raise PlaywrightError(f"Failed to apply stealth mode: {e}")
    
    async def _solve_recaptcha_v2(self, params: Dict[str, Any]) -> str:
        """Solve reCAPTCHA v2."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.solver.recaptcha(
                sitekey=params['sitekey'],
                url=params['url']
            )
        )
        return result['code']
    
    async def _solve_recaptcha_v3(self, params: Dict[str, Any]) -> str:
        """Solve reCAPTCHA v3."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.solver.recaptcha(
                sitekey=params['sitekey'],
                url=params['url'],
                version='v3',
                action=params.get('action', 'verify'),
                score=params.get('min_score', 0.7)
            )
        )
        return result['code']
    
    async def _solve_hcaptcha(self, params: Dict[str, Any]) -> str:
        """Solve hCaptcha."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.solver.hcaptcha(
                sitekey=params['sitekey'],
                url=params['url']
            )
        )
        return result['code']
    
    async def _solve_image_captcha(self, params: Dict[str, Any]) -> str:
        """Solve image-based CAPTCHA."""
        if 'image' not in params:
            raise ValueError("Image data required for image CAPTCHA")
            
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.solver.normal(
                image=params['image']
            )
        )
        return result['code']
    
    async def _solve_text_captcha(self, params: Dict[str, Any]) -> str:
        """Solve text-based CAPTCHA."""
        if 'text' not in params:
            raise ValueError("Text required for text CAPTCHA")
            
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.solver.text(
                text=params['text']
            )
        )
        return result['code']
    
    async def _apply_basic_stealth(self, page: Page) -> None:
        """Apply basic stealth features."""
        # Modify navigator properties
        await page.evaluate("""
            () => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            }
        """)
        
        # Add basic browser features
        await page.evaluate("""
            () => {
                window.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {
                                type: "application/x-google-chrome-pdf",
                                suffixes: "pdf",
                                description: "Portable Document Format",
                                enabledPlugin: true
                            },
                            description: "Chrome PDF Plugin",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        }
                    ]
                });
            }
        """)
    
    async def _apply_medium_stealth(self, page: Page) -> None:
        """Apply medium level stealth features."""
        # Add more sophisticated browser fingerprinting evasion
        await page.evaluate("""
            () => {
                // Mock permissions API
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Mock WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Open Source Technology Center';
                    }
                    if (parameter === 37446) {
                        return 'Mesa DRI Intel(R) HD Graphics (SKL GT2)';
                    }
                    return getParameter.apply(this, arguments);
                };
            }
        """)
    
    async def _apply_aggressive_stealth(self, page: Page) -> None:
        """Apply aggressive stealth features."""
        # Add maximum stealth features
        await page.evaluate("""
            () => {
                // Mock audio context
                const audioContext = window.AudioContext;
                window.AudioContext = class extends audioContext {
                    constructor() {
                        super();
                        const random = Math.random() * 10;
                        Object.defineProperty(this, 'baseLatency', {
                            get: () => random
                        });
                    }
                };
                
                // Mock canvas fingerprinting
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function() {
                    const context = originalGetContext.apply(this, arguments);
                    if (context && context.toString() === '[object CanvasRenderingContext2D]') {
                        const originalFillText = context.fillText;
                        context.fillText = function() {
                            arguments[0] = arguments[0].replace(/./g, '*');
                            return originalFillText.apply(this, arguments);
                        };
                    }
                    return context;
                };
            }
        """)
    
    def is_captcha_present(self, html_content: str) -> bool:
        """Check if CAPTCHA is present in the page.
        
        Args:
            html_content: HTML content to check
            
        Returns:
            True if CAPTCHA is detected, False otherwise
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Common CAPTCHA indicators
        captcha_indicators = [
            # reCAPTCHA
            'g-recaptcha',
            'recaptcha',
            # hCaptcha
            'h-captcha',
            'hcaptcha',
            # Common text indicators
            'captcha',
            'robot-verification',
            'bot-verification',
            'human-verification'
        ]
        
        # Check for CAPTCHA elements
        for indicator in captcha_indicators:
            # Check class names
            if soup.find(class_=lambda x: x and indicator.lower() in x.lower()):
                return True
            
            # Check IDs
            if soup.find(id=lambda x: x and indicator.lower() in x.lower()):
                return True
            
            # Check for frames (common in reCAPTCHA)
            if soup.find('iframe', src=lambda x: x and indicator.lower() in x.lower()):
                return True
        
        return False
        
    async def solve_captcha(self, url: str, browser_handler) -> str:
        """Solve CAPTCHA and return the updated page content.
        
        Args:
            url: The URL where CAPTCHA was encountered
            browser_handler: BrowserHandler instance for page interaction
            
        Returns:
            Updated page content after solving CAPTCHA
            
        Raises:
            ValueError: If no API key is configured
            Exception: If CAPTCHA solving fails
        """
        if not self.api_key:
            raise ValueError("2captcha API key is required for CAPTCHA solving")
            
        try:
            # Get the current page
            page = browser_handler.page
            if not page:
                raise ValueError("No active page in browser handler")
                
            # Find reCAPTCHA
            site_key = await page.evaluate("""() => {
                const element = document.querySelector('.g-recaptcha');
                return element ? element.getAttribute('data-sitekey') : null;
            }""")
            
            if not site_key:
                logger.warning("Could not find reCAPTCHA site key")
                return await page.content()
                
            # Solve CAPTCHA
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=url
            )
            
            # Submit solution
            await page.evaluate(f"""(response) => {{
                document.getElementById('g-recaptcha-response').innerHTML = response;
                document.querySelector('form').submit();
            }}""", result['code'])
            
            # Wait for navigation
            await page.wait_for_load_state('networkidle')
            
            # Return updated content
            return await page.content()
            
        except Exception as e:
            logger.error(f"Failed to solve CAPTCHA: {str(e)}")
            raise 