"""
Tests for the HTML converter module.
"""

import os
import pytest
from src.web_scraping.html_converter import HTMLConverter
from pathlib import Path

@pytest.fixture
def converter():
    return HTMLConverter()

@pytest.fixture
def sample_html():
    return """
    <html>
        <head>
            <title>Test Page</title>
            <style>
                body { color: black; }
            </style>
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is a <strong>test</strong> paragraph with <em>emphasis</em>.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <table>
                <tr>
                    <th>Header 1</th>
                    <th>Header 2</th>
                </tr>
                <tr>
                    <td>Cell 1</td>
                    <td>Cell 2</td>
                </tr>
            </table>
            <a href="https://example.com">Link</a>
            <img src="image.jpg" alt="Test Image">
            <script>
                console.log("This should be removed");
            </script>
            <!-- This is a comment that should be removed -->
        </body>
    </html>
    """

def test_html_cleaning(converter, sample_html):
    cleaned_html = converter.clean_html(sample_html)
    
    # Check if script and style tags are removed
    assert "<style>" not in cleaned_html
    assert "<script>" not in cleaned_html
    
    # Check if comments are removed
    assert "<!-- This is a comment that should be removed -->" not in cleaned_html
    
    # Check if main content is preserved
    assert "<h1>Main Title</h1>" in cleaned_html
    assert '<a href="https://example.com">Link</a>' in cleaned_html

def test_markdown_conversion(converter, sample_html):
    markdown = converter.convert_to_markdown(sample_html)
    
    # Check basic formatting
    assert "# Main Title" in markdown
    assert "**test**" in markdown
    assert "*emphasis*" in markdown
    
    # Check list conversion
    assert "* Item 1" in markdown
    assert "* Item 2" in markdown
    
    # Check table preservation (with flexible spacing)
    assert all(cell in markdown for cell in ["Header 1", "Header 2", "Cell 1", "Cell 2"])
    assert "|" in markdown  # Should contain table separators
    assert "---" in markdown  # Should contain header separator
    
    # Check link conversion (with flexible format)
    assert "Link" in markdown and "https://example.com" in markdown
    
    # Check image conversion
    assert "image.jpg" in markdown and "Test Image" in markdown

def test_markdown_formatting(converter):
    html = """
    <h1>Title</h1>
    <ul>
        <li>First item</li>
        <li>Second item</li>
    </ul>
    <p>Some text.</p>
    """
    
    markdown = converter.convert_to_markdown(html)
    lines = markdown.strip().split('\n')
    
    # Find the first list item
    list_items = [i for i, line in enumerate(lines) if '*' in line and 'First' in line]
    assert list_items, "List items not found in output"
    
    list_start_idx = list_items[0]
    # Check if there's proper spacing before the list
    assert list_start_idx > 0 and not lines[list_start_idx - 1].strip(), "Missing empty line before list"

def test_file_saving(converter, sample_html, tmp_path):
    # Convert HTML to markdown
    markdown = converter.convert_to_markdown(sample_html)
    
    # Save to temporary file
    test_file = tmp_path / "test_output.md"
    result = converter.save_markdown(markdown, str(test_file))
    
    # Check if save was successful
    assert result is True
    assert test_file.exists()
    
    # Check file contents
    content = test_file.read_text(encoding='utf-8')
    assert "Main Title" in content
    assert "**test**" in content

def test_convert_and_save(converter, sample_html, tmp_path):
    # Test the combined convert and save operation
    test_file = tmp_path / "nested" / "test_output.md"
    result = converter.convert_and_save(sample_html, str(test_file))
    
    # Check if operation was successful
    assert result is True
    assert test_file.exists()
    
    # Check if directories were created
    assert test_file.parent.exists()
    
    # Verify content
    content = test_file.read_text(encoding='utf-8')
    assert "Main Title" in content
    assert "**test**" in content

def test_error_handling(converter):
    # Test with invalid HTML
    result = converter.convert_to_markdown("<<<invalid>html>")
    assert result == ""
    
    # Test with empty content
    result = converter.convert_to_markdown("")
    assert result == ""
    
    # Test saving to invalid path
    result = converter.save_markdown("test content", "/invalid/path/file.md", create_dirs=False)
    assert result is False