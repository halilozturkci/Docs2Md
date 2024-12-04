# Docs2Md

A Python utility to convert MDX documentation files into a single, well-structured Markdown file.

## Features

- Combines multiple MDX files into a single MD file
- Preserves directory hierarchy as headings
- Generates automatic table of contents
- Maintains formatting and special syntax
- Adjusts resource paths automatically
- Command-line interface for easy use

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py --input-dir /path/to/docs --output-file output.md
```

### Arguments

- `--input-dir`: Directory containing MDX files (required)
- `--output-file`: Path for the output MD file (required)

## Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python -m pytest tests/`

## License

MIT License 