"""
Tests for the CAPTCHA handler module.
"""

import pytest
import pytest_asyncio
import asyncio
import base64
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from playwright.async_api import Page, Error as PlaywrightError
from src.web_scraping.captcha_handler import (
    CaptchaHandler,
    CaptchaType,
    StealthMode,
    CaptchaConfig
)

@pytest.fixture
def api_key():
    """2captcha API key for testing."""
    return "test_api_key"

@pytest.fixture
def mock_solver():
    """Mock 2captcha solver."""
    with patch('twocaptcha.TwoCaptcha') as mock:
        solver = mock.return_value
        
        # Mock successful responses
        solver.recaptcha.return_value = {'code': 'test_recaptcha_token'}
        solver.hcaptcha.return_value = {'code': 'test_hcaptcha_token'}
        solver.normal.return_value = {'code': 'test_image_solution'}
        solver.text.return_value = {'code': 'test_text_solution'}
        
        # Configure solver properties
        solver.timeout = 120
        solver.proxy = None
        
        yield solver

@pytest_asyncio.fixture
async def mock_page():
    """Mock Playwright page."""
    page = MagicMock()
    page.evaluate = AsyncMock()
    return page

@pytest.mark.asyncio
async def test_initialization(api_key):
    """Test CAPTCHA handler initialization."""
    handler = CaptchaHandler(
        api_key=api_key,
        stealth_mode=StealthMode.BASIC,
        proxy={'http': 'http://proxy:8080'},
        timeout=60
    )
    
    assert handler.solver is not None
    assert handler.stealth_mode == StealthMode.BASIC
    assert handler.proxy == {'http': 'http://proxy:8080'}
    assert handler.timeout == 60

@pytest.mark.asyncio
async def test_solve_recaptcha_v2(api_key, mock_solver, mock_page):
    """Test solving reCAPTCHA v2."""
    handler = CaptchaHandler(api_key)
    handler.solver = mock_solver
    
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.RECAPTCHA_V2,
        site_key="test_site_key",
        site_url="https://example.com"
    )
    
    solution = await handler.solve_captcha(config)
    assert solution == "test_recaptcha_token"
    
    mock_solver.recaptcha.assert_called_once_with(
        sitekey="test_site_key",
        url="https://example.com"
    )

@pytest.mark.asyncio
async def test_solve_recaptcha_v3(api_key, mock_solver, mock_page):
    """Test solving reCAPTCHA v3."""
    handler = CaptchaHandler(api_key)
    handler.solver = mock_solver
    
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.RECAPTCHA_V3,
        site_key="test_site_key",
        site_url="https://example.com",
        extra_params={
            'action': 'login',
            'min_score': 0.9
        }
    )
    
    solution = await handler.solve_captcha(config)
    assert solution == "test_recaptcha_token"
    
    mock_solver.recaptcha.assert_called_once_with(
        sitekey="test_site_key",
        url="https://example.com",
        version='v3',
        action='login',
        score=0.9
    )

@pytest.mark.asyncio
async def test_solve_hcaptcha(api_key, mock_solver, mock_page):
    """Test solving hCaptcha."""
    handler = CaptchaHandler(api_key)
    handler.solver = mock_solver
    
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.HCAPTCHA,
        site_key="test_site_key",
        site_url="https://example.com"
    )
    
    solution = await handler.solve_captcha(config)
    assert solution == "test_hcaptcha_token"
    
    mock_solver.hcaptcha.assert_called_once_with(
        sitekey="test_site_key",
        url="https://example.com"
    )

@pytest.mark.asyncio
async def test_solve_image_captcha(api_key, mock_solver):
    """Test solving image CAPTCHA."""
    handler = CaptchaHandler(api_key)
    handler.solver = mock_solver
    
    # Create base64 image data
    image_data = base64.b64encode(b"test_image_data").decode()
    
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.IMAGE_CAPTCHA,
        extra_params={'image': image_data}
    )
    
    solution = await handler.solve_captcha(config)
    assert solution == "test_image_solution"
    
    mock_solver.normal.assert_called_once_with(
        image=image_data
    )

@pytest.mark.asyncio
async def test_solve_text_captcha(api_key, mock_solver):
    """Test solving text CAPTCHA."""
    handler = CaptchaHandler(api_key)
    handler.solver = mock_solver
    
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.TEXT_CAPTCHA,
        extra_params={'text': "What is 2+2?"}
    )
    
    solution = await handler.solve_captcha(config)
    assert solution == "test_text_solution"
    
    mock_solver.text.assert_called_once_with(
        text="What is 2+2?"
    )

@pytest.mark.asyncio
async def test_invalid_captcha_type(api_key):
    """Test handling invalid CAPTCHA type."""
    handler = CaptchaHandler(api_key)
    
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=None
    )
    
    with pytest.raises(ValueError, match="CAPTCHA type must be specified"):
        await handler.solve_captcha(config)

@pytest.mark.asyncio
async def test_missing_parameters(api_key):
    """Test handling missing required parameters."""
    handler = CaptchaHandler(api_key)
    
    # Test missing image data
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.IMAGE_CAPTCHA
    )
    
    with pytest.raises(ValueError, match="Image data required"):
        await handler.solve_captcha(config)
    
    # Test missing text
    config = CaptchaConfig(
        api_key=api_key,
        captcha_type=CaptchaType.TEXT_CAPTCHA
    )
    
    with pytest.raises(ValueError, match="Text required"):
        await handler.solve_captcha(config)

@pytest.mark.asyncio
async def test_stealth_mode_basic(api_key, mock_page):
    """Test basic stealth mode features."""
    handler = CaptchaHandler(api_key, stealth_mode=StealthMode.BASIC)
    await handler.apply_stealth_mode(mock_page)
    
    # Verify that evaluate was called with stealth scripts
    assert mock_page.evaluate.call_count >= 2

@pytest.mark.asyncio
async def test_stealth_mode_medium(api_key, mock_page):
    """Test medium stealth mode features."""
    handler = CaptchaHandler(api_key, stealth_mode=StealthMode.MEDIUM)
    await handler.apply_stealth_mode(mock_page)
    
    # Verify that evaluate was called with additional stealth scripts
    assert mock_page.evaluate.call_count >= 3

@pytest.mark.asyncio
async def test_stealth_mode_aggressive(api_key, mock_page):
    """Test aggressive stealth mode features."""
    handler = CaptchaHandler(api_key, stealth_mode=StealthMode.AGGRESSIVE)
    await handler.apply_stealth_mode(mock_page)
    
    # Verify that evaluate was called with maximum stealth scripts
    assert mock_page.evaluate.call_count >= 3

@pytest.mark.asyncio
async def test_stealth_mode_error(api_key, mock_page):
    """Test error handling in stealth mode."""
    handler = CaptchaHandler(api_key)
    
    # Mock page.evaluate to raise an error
    mock_page.evaluate.side_effect = Exception("Stealth mode error")
    
    with pytest.raises(PlaywrightError, match="Failed to apply stealth mode"):
        await handler.apply_stealth_mode(mock_page)