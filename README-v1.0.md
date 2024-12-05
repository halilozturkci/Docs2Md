# MDX to MD Documentation Converter v1.0

A robust Python utility for converting and consolidating MDX documentation files into a single, well-structured Markdown file.

## 🎯 Overview

This tool is specifically designed to transform documentation from multiple MDX files into a unified MD format, making it particularly useful for applications like Cursor that require consolidated documentation access.

## ✨ Key Features

- **Directory Traversal**: Recursively processes all MDX files in specified directories and subdirectories
- **Hierarchy Preservation**: Maintains original directory structure through heading levels
- **Smart Content Merging**: Preserves formatting and special syntax during consolidation
- **Command-line Interface**: Easy-to-use CLI with input/output path specification
- **Automated Table of Contents**: Generates structured ToC for the consolidated content
- **Path Resolution**: Automatically adjusts resource paths (images, links) for consolidated format
- **Robust Error Handling**: Comprehensive logging and user-friendly error messages
- **Encoding Support**: Handles various file encodings and character sets

## 🛠️ Technical Architecture

```
.
├── main.py                 # CLI entry point
├── src/
│   ├── __init__.py        # Package initialization
│   ├── converter.py       # Core conversion logic
│   └── file_handler.py    # File operations handler
└── tests/
    ├── __init__.py
    └── test_file_handler.py
```

## 📋 Requirements

- Python 3.7+
- click
- pathlib
- logging

## 💻 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Usage

Basic command structure:

```bash
python main.py --input-dir <source_directory> --output-file <target_file.md>
```

Example:

```bash
python main.py --input-dir ./docs --output-file ./consolidated_docs.md
```

## 🔍 Input/Output Specifications

### Input
- Accepts a directory containing `.mdx` files
- Processes all subdirectories recursively
- Ignores non-MDX files
- Supports various file encodings

### Output
- Single consolidated `.md` file
- Structured with directory-based headings
- Automated table of contents
- Preserved formatting and syntax
- Adjusted resource paths

## 🔧 Configuration

The tool uses Python's logging module with the following configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## ⚙️ Core Components

### Converter Class
- Manages the overall conversion process
- Handles directory traversal and file consolidation
- Implements content transformation logic

### File Handler
- Manages file operations
- Handles encoding detection
- Processes file paths and hierarchies

## 🎯 Processing Flow

1. **Initialization**
   - Validate input directory and output file path
   - Set up logging

2. **File Discovery**
   - Recursively scan input directory
   - Identify MDX files
   - Build file hierarchy

3. **Content Processing**
   - Read MDX files
   - Transform content
   - Adjust resource paths
   - Generate table of contents

4. **Output Generation**
   - Consolidate transformed content
   - Write to output file
   - Verify output integrity

## 🔐 Error Handling

The tool implements comprehensive error handling for:
- Invalid input/output paths
- File access issues
- Encoding problems
- Content transformation errors

Example error handling:

```python
try:
    converter.convert()
except Exception as e:
    logger.error(f"Conversion failed: {str(e)}")
    raise click.ClickException(str(e))
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

[MIT License](LICENSE)

## 🔍 Version History

### v1.0
- Initial release
- Basic MDX to MD conversion
- Directory hierarchy preservation
- Command-line interface
- Logging implementation
- Error handling 