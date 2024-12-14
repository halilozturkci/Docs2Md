"""
Tests for the command-line interface.
"""

import os
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.main import cli, validate_urls, process_urls_with_progress
from src.web_scraping.url_processor import ProcessingResult
from src.config import AppConfig, BrowserConfig, CaptchaConfig, ScrapingConfig, LoggingConfig

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return AppConfig(
        browser=BrowserConfig(headless=True),
        captcha=CaptchaConfig(api_key=None),
        scraping=ScrapingConfig(
            follow_links=False,
            max_depth=1
        ),
        logging=LoggingConfig(
            level='INFO',
            file=None
        ),
        output_dir='output'
    )

def test_validate_urls():
    """Test URL validation."""
    urls = [
        'http://example.com',
        'https://test.com',
        'invalid-url',
        'ftp://invalid-protocol.com'
    ]
    
    valid_urls = validate_urls(urls)
    assert len(valid_urls) == 2
    assert 'http://example.com' in valid_urls
    assert 'https://test.com' in valid_urls
    assert 'invalid-url' not in valid_urls
    assert 'ftp://invalid-protocol.com' not in valid_urls

@pytest.mark.asyncio
async def test_process_urls_with_progress(tmp_path):
    """Test URL processing with enhanced progress feedback."""
    # Mock URL processor
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(side_effect=[
        ProcessingResult(
            url='http://example1.com',
            markdown_content='# Test 1\nContent 1',
            extracted_links=[],
            success=True
        ),
        ProcessingResult(
            url='http://example2.com',
            markdown_content='# Test 2\nContent 2',
            extracted_links=[],
            success=True
        )
    ])
    
    # Process URLs
    urls = ['http://example1.com', 'http://example2.com']
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 2
    assert all(r.success for r in results)
    assert mock_processor.process_url.call_count == 2
    
    # Check output files and content
    output_files = list(tmp_path.glob('*.md'))
    assert len(output_files) == 2
    
    # Verify file contents
    content1 = (tmp_path / 'example1.com.md').read_text()
    content2 = (tmp_path / 'example2.com.md').read_text()
    assert content1 == '# Test 1\nContent 1'
    assert content2 == '# Test 2\nContent 2'

@pytest.mark.asyncio
async def test_process_urls_with_errors(tmp_path):
    """Test URL processing with errors."""
    # Mock URL processor with error
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(side_effect=Exception("Test error"))
    
    # Process URLs
    urls = ['http://example.com']
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 1
    assert not results[0].success
    assert "Test error" in results[0].error
    
    # Check no output files
    output_files = list(tmp_path.glob('*.md'))
    assert len(output_files) == 0

def test_cli_convert_command(runner, mock_config, tmp_path):
    """Test the convert command."""
    with patch('src.main.AppConfig.load', return_value=mock_config), \
         patch('src.main.URLProcessor') as mock_processor_cls, \
         patch('src.main.process_urls_with_progress', new_callable=AsyncMock) as mock_process:
        
        # Configure mock processor
        mock_processor = mock_processor_cls.return_value
        mock_process.return_value = [
            ProcessingResult(
                url='http://example.com',
                markdown_content='# Test',
                extracted_links=[],
                success=True
            )
        ]
        
        result = runner.invoke(cli, [
            'convert',
            'http://example.com',
            '--output', str(tmp_path),
            '--follow-links'
        ])
        
        assert result.exit_code == 0
        assert mock_process.called

def test_cli_config_command(runner, mock_config, tmp_path):
    """Test the config command."""
    config_file = tmp_path / 'config.yaml'
    
    with patch('src.main.AppConfig.load', return_value=mock_config):
        result = runner.invoke(cli, [
            'config',
            '--output', str(config_file)
        ])
        
        assert result.exit_code == 0
        assert config_file.exists()

def test_cli_invalid_urls(runner, mock_config):
    """Test CLI with invalid URLs."""
    with patch('src.main.AppConfig.load', return_value=mock_config):
        result = runner.invoke(cli, [
            'convert',
            'invalid-url'
        ])
        
        assert result.exit_code == 1
        assert "No valid URLs provided" in result.output

def test_cli_keyboard_interrupt(runner, mock_config):
    """Test CLI keyboard interrupt handling."""
    with patch('src.main.AppConfig.load', return_value=mock_config), \
         patch('src.main.process_urls_with_progress', side_effect=KeyboardInterrupt):
        
        result = runner.invoke(cli, [
            'convert',
            'http://example.com'
        ])
        
        assert result.exit_code == 1
        assert "interrupted by user" in result.output

@pytest.mark.asyncio
async def test_process_urls_with_mixed_results(tmp_path):
    """Test URL processing with both successful and failed results."""
    # Mock URL processor
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(side_effect=[
        ProcessingResult(
            url='http://success.com',
            markdown_content='# Success\nContent',
            extracted_links=[],
            success=True
        ),
        ProcessingResult(
            url='http://fail.com',
            markdown_content='',
            extracted_links=[],
            success=False,
            error='Failed to process'
        )
    ])
    
    # Process URLs
    urls = ['http://success.com', 'http://fail.com']
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 2
    assert results[0].success
    assert not results[1].success
    
    # Check output files
    output_files = list(tmp_path.glob('*.md'))
    assert len(output_files) == 1
    assert (tmp_path / 'success.com.md').exists()
    assert not (tmp_path / 'fail.com.md').exists()

@pytest.mark.asyncio
async def test_process_urls_with_large_content(tmp_path):
    """Test URL processing with large content for progress display."""
    # Create large content
    large_content = "# Large Content\n" + "Content line\n" * 1000
    
    # Mock URL processor
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(return_value=ProcessingResult(
        url='http://large.com',
        markdown_content=large_content,
        extracted_links=[],
        success=True
    ))
    
    # Process URLs
    urls = ['http://large.com']
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 1
    assert results[0].success
    
    # Check output file and content size
    output_file = tmp_path / 'large.com.md'
    assert output_file.exists()
    assert len(output_file.read_text()) > 10000  # Verify large content

@pytest.mark.asyncio
async def test_process_urls_with_detailed_metrics(tmp_path):
    """Test URL processing with detailed metrics tracking."""
    # Create test content with varying sizes
    contents = [
        "# Small Content\nTest",  # Small file
        "# Large Content\n" + "Content line\n" * 1000,  # Large file
        "# Medium Content\n" + "Content line\n" * 100,  # Medium file
    ]
    
    # Mock URL processor with varying processing times
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(side_effect=[
        ProcessingResult(
            url='http://small.com',
            markdown_content=contents[0],
            extracted_links=['link1', 'link2'],
            success=True
        ),
        ProcessingResult(
            url='http://large.com',
            markdown_content=contents[1],
            extracted_links=['link3', 'link4', 'link5'],
            success=True
        ),
        ProcessingResult(
            url='http://medium.com',
            markdown_content=contents[2],
            extracted_links=['link6'],
            success=True
        )
    ])
    
    # Process URLs
    urls = ['http://small.com', 'http://large.com', 'http://medium.com']
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 3
    assert all(r.success for r in results)
    
    # Verify file sizes
    files = {
        'small.com.md': len(contents[0]),
        'large.com.md': len(contents[1]),
        'medium.com.md': len(contents[2])
    }
    
    for filename, expected_size in files.items():
        file_path = tmp_path / filename
        assert file_path.exists()
        assert len(file_path.read_text()) == expected_size
    
    # Verify link extraction
    assert len(results[0].extracted_links) == 2  # small.com
    assert len(results[1].extracted_links) == 3  # large.com
    assert len(results[2].extracted_links) == 1  # medium.com

@pytest.mark.asyncio
async def test_process_urls_with_performance_metrics(tmp_path):
    """Test URL processing with performance metrics tracking."""
    import asyncio
    from time import sleep
    
    # Mock URL processor with varying processing times
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(side_effect=[
        # Fast processing
        ProcessingResult(
            url='http://fast.com',
            markdown_content='# Fast\nContent',
            extracted_links=[],
            success=True
        ),
        # Slow processing (simulate with sleep)
        ProcessingResult(
            url='http://slow.com',
            markdown_content='# Slow\nContent',
            extracted_links=[],
            success=True
        ),
        # Medium processing
        ProcessingResult(
            url='http://medium.com',
            markdown_content='# Medium\nContent',
            extracted_links=[],
            success=True
        )
    ])
    
    # Process URLs
    urls = ['http://fast.com', 'http://slow.com', 'http://medium.com']
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 3
    assert all(r.success for r in results)
    
    # Verify files were created
    for domain in ['fast.com', 'slow.com', 'medium.com']:
        assert (tmp_path / f"{domain}.md").exists()

@pytest.mark.asyncio
async def test_process_urls_with_error_reporting(tmp_path):
    """Test URL processing with detailed error reporting."""
    # Mock URL processor with various error scenarios
    mock_processor = Mock()
    mock_processor.process_url = AsyncMock(side_effect=[
        ProcessingResult(
            url='http://success.com',
            markdown_content='# Success\nContent',
            extracted_links=[],
            success=True
        ),
        ProcessingResult(
            url='http://timeout.com',
            markdown_content='',
            extracted_links=[],
            success=False,
            error='Connection timeout'
        ),
        Exception("Network error"),  # Simulate unexpected error
        ProcessingResult(
            url='http://invalid.com',
            markdown_content='',
            extracted_links=[],
            success=False,
            error='Invalid content'
        )
    ])
    
    # Process URLs
    urls = [
        'http://success.com',
        'http://timeout.com',
        'http://network.com',
        'http://invalid.com'
    ]
    results = await process_urls_with_progress(
        processor=mock_processor,
        urls=urls,
        output_dir=str(tmp_path)
    )
    
    # Verify results
    assert len(results) == 4
    assert sum(1 for r in results if r.success) == 1  # One success
    assert sum(1 for r in results if not r.success) == 3  # Three failures
    
    # Verify success file
    assert (tmp_path / "success.com.md").exists()
    
    # Verify error cases
    error_urls = [r.url for r in results if not r.success]
    assert 'http://timeout.com' in error_urls
    assert 'http://network.com' in error_urls
    assert 'http://invalid.com' in error_urls
    
    # Verify specific error messages
    error_dict = {r.url: r.error for r in results if not r.success}
    assert error_dict['http://timeout.com'] == 'Connection timeout'
    assert error_dict['http://network.com'] == 'Network error'
    assert error_dict['http://invalid.com'] == 'Invalid content'