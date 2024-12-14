"""
Configuration handler for the application.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
import yaml
import os
from pathlib import Path

@dataclass
class BrowserConfig:
    """Browser-specific configuration."""
    headless: bool = True
    timeout: int = 30
    wait_for_js: bool = False
    user_agent: Optional[str] = None
    viewport_size: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})

@dataclass
class CaptchaConfig:
    """CAPTCHA handling configuration."""
    api_key: Optional[str] = None
    service: str = "2captcha"
    timeout: int = 120

@dataclass
class ScrapingConfig:
    """Web scraping configuration."""
    max_retries: int = 3
    retry_delay: int = 5
    concurrent_limit: int = 5
    follow_links: bool = False
    max_depth: int = 1

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[str] = "docs2md.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

@dataclass
class AppConfig:
    """Main application configuration."""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    captcha: CaptchaConfig = field(default_factory=CaptchaConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    output_dir: str = "output"
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'AppConfig':
        """Load configuration from YAML file."""
        if not config_path:
            config_path = os.path.join(str(Path.home()), ".docs2md", "config.yaml")
            
        if not os.path.exists(config_path):
            return cls()
            
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
            
        return cls(
            browser=BrowserConfig(**config_dict.get('browser', {})),
            captcha=CaptchaConfig(**config_dict.get('captcha', {})),
            scraping=ScrapingConfig(**config_dict.get('scraping', {})),
            logging=LoggingConfig(**config_dict.get('logging', {})),
            output_dir=config_dict.get('output_dir', 'output')
        )
    
    def save(self, config_path: Optional[str] = None) -> None:
        """Save configuration to YAML file."""
        if not config_path:
            config_path = os.path.join(str(Path.home()), ".docs2md", "config.yaml")
            
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        config_dict = {
            'browser': {
                'headless': self.browser.headless,
                'timeout': self.browser.timeout,
                'wait_for_js': self.browser.wait_for_js,
                'user_agent': self.browser.user_agent,
                'viewport_size': self.browser.viewport_size
            },
            'captcha': {
                'api_key': self.captcha.api_key,
                'service': self.captcha.service,
                'timeout': self.captcha.timeout
            },
            'scraping': {
                'max_retries': self.scraping.max_retries,
                'retry_delay': self.scraping.retry_delay,
                'concurrent_limit': self.scraping.concurrent_limit,
                'follow_links': self.scraping.follow_links,
                'max_depth': self.scraping.max_depth
            },
            'logging': {
                'level': self.logging.level,
                'file': self.logging.file,
                'format': self.logging.format
            },
            'output_dir': self.output_dir
        }
        
        with open(config_path, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False) 