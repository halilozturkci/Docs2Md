# MDX to MD Documentation Converter v2.0

A powerful Python utility designed to transform and consolidate MDX documentation files into a single, well-structured Markdown file, with enhanced GitHub integration and interactive features.

## 🎯 Overview

This tool is specifically engineered to transform documentation from multiple MDX files into a unified MD format, making it particularly useful for applications like Cursor that require consolidated documentation access. With the addition of GitHub integration and interactive directory selection, it now offers a more streamlined workflow for documentation management.

## ✨ Key Features

### Core Features
- **Directory Traversal**: Recursively processes all MDX files in specified directories and subdirectories
- **Hierarchy Preservation**: Maintains original directory structure through heading levels
- **Smart Content Merging**: Preserves formatting and special syntax during consolidation
- **Command-line Interface**: Enhanced CLI with multiple configuration options
- **Automated Table of Contents**: Generates structured ToC for the consolidated content
- **Path Resolution**: Automatically adjusts resource paths (images, links) for consolidated format
- **Robust Error Handling**: Comprehensive logging with rich tracebacks and user-friendly error messages
- **Encoding Support**: Handles various file encodings and character sets

### New Features in v2.0
- **GitHub Integration**: Direct repository access and processing
- **Interactive Mode**: User-friendly directory selection interface
- **Rich Logging**: Enhanced logging with colored output and better tracebacks
- **Flexible Directory Selection**: Process specific directories with comma-separated list
- **Frontmatter Support**: Proper handling of YAML frontmatter in MDX files
- **Image Path Resolution**: Smart handling of both relative and absolute image paths
- **Enhanced Error Recovery**: Graceful handling of malformed content

## 🛠️ Technical Architecture

```
.
├── main.py                 # Enhanced CLI entry point with GitHub support
├── src/
│   ├── __init__.py        # Package initialization
│   ├── converter.py       # Core conversion logic
│   ├── file_handler.py    # File operations handler
│   └── github_handler.py  # GitHub integration module
└── tests/
    ├── __init__.py
    └── test_file_handler.py
```

## 📋 Requirements

- Python 3.7+
- click>=8.1.7
- pathlib>=1.0.1
- markdown2>=2.4.10
- PyYAML>=6.0.1
- python-frontmatter>=1.0.0
- rich>=13.7.0
- PyGithub>=2.1.1  # GitHub API integration
- requests>=2.31.0 # HTTP requests for GitHub API

### GitHub Authentication
To use the GitHub integration features, you need to:
1. Create a GitHub Personal Access Token (PAT)
2. Set it as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```
   or provide it via the command line:
   ```bash
   python main.py --github-token your_token_here --github-repo <repository_url> --output-file <output.md>
   ```

## 💻 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Basic Usage

```bash
python main.py --github-repo <repository_url> --output-file <output.md>
```

### Advanced Options

```bash
# Interactive mode with specific directories
python main.py --github-repo <repository_url> --interactive --output-file <output.md>

# Non-interactive mode with specific directories
python main.py --github-repo <repository_url> --no-interactive --dirs "docs,api,guides" --output-file <output.md>
```

## 🔍 Input/Output Specifications

### Input
- Accepts GitHub repository URLs
- Processes specified directories within the repository
- Handles both .md and .mdx files
- Supports YAML frontmatter
- Processes various image path formats

### Output
- Single consolidated `.md` file
- Structured with directory-based headings
- Automated table of contents
- Preserved formatting and syntax
- Adjusted resource paths
- Maintained document hierarchy

## 🔧 Configuration

### Logging Configuration
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
```

### GitHub Integration
- Supports both public and private repositories (requires appropriate GitHub PAT permissions)
- Handles repository cloning and cleanup
- Maintains directory structure integrity
- Rate limit aware with automatic handling
- Supports organization repositories
- Requires GitHub Personal Access Token for private repositories

## ⚙️ Core Components

### Converter Class
- Manages the overall conversion process
- Handles directory traversal and file consolidation
- Implements content transformation logic
- Processes image paths and links
- Generates table of contents

### File Handler
- Manages file operations
- Handles encoding detection
- Processes file paths and hierarchies
- Supports frontmatter parsing
- Implements file discovery logic

### GitHub Handler
- Manages repository interactions
- Handles authentication
- Implements repository cloning
- Manages temporary storage

## 🎯 Processing Flow

1. **Repository Setup**
   - Clone GitHub repository
   - Validate repository structure
   - Set up working directory

2. **Directory Selection**
   - Interactive mode: User selects directories
   - Non-interactive mode: Process specified directories
   - Validate directory existence

3. **File Discovery**
   - Recursively scan selected directories
   - Identify MD/MDX files
   - Build file hierarchy
   - Validate file accessibility

4. **Content Processing**
   - Parse frontmatter
   - Transform MDX content
   - Adjust resource paths
   - Handle image references
   - Process internal links

5. **Output Generation**
   - Generate table of contents
   - Consolidate transformed content
   - Apply heading hierarchy
   - Write to output file
   - Verify output integrity

6. **Cleanup**
   - Remove temporary files
   - Clean up cloned repository
   - Log completion status

## 🔐 Error Handling

The tool implements comprehensive error handling for:
- Invalid repository URLs
- Authentication failures
- Directory access issues
- File parsing errors
- Encoding problems
- Content transformation errors
- Resource path resolution issues

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

### v2.0
- Added GitHub integration
- Implemented interactive mode
- Enhanced logging with rich output
- Added frontmatter support
- Improved image path handling
- Added flexible directory selection
- Enhanced error recovery

### v1.0
- Initial release
- Basic MDX to MD conversion
- Directory hierarchy preservation
- Command-line interface
- Basic logging implementation
- Error handling 