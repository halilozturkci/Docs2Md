# Usage Guide

This guide provides detailed information about using Docs2Md to convert web documentation to Markdown format.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Command Reference](#command-reference)
- [Output Format](#output-format)
- [Best Practices](#best-practices)

## Basic Usage

### Converting a Single Page

```bash
python -m docs2md convert https://example.com/docs/page
```

This will:
1. Download the page content
2. Process dynamic content
3. Handle any CAPTCHAs
4. Convert HTML to Markdown
5. Save the result in the output directory

### Processing Multiple Pages

```bash
python -m docs2md convert https://docs1.com https://docs2.com --output docs/
```

- Each page is processed concurrently
- Results are saved in separate files
- Progress is displayed in real-time

### Following Links

```bash
python -m docs2md convert https://example.com/docs --follow-links --max-depth 2
```

This will:
- Process the initial page
- Extract all links
- Follow and process linked pages
- Continue until max depth is reached

## Advanced Features

### CAPTCHA Handling

1. Configure 2captcha:
   ```bash
   python -m docs2md config
   ```
   Add your API key to the configuration:
   ```yaml
   captcha:
     api_key: "your-2captcha-key"
     service: "2captcha"
     timeout: 120
   ```

2. Process protected pages:
   ```bash
   python -m docs2md convert https://protected-site.com/docs
   ```

### Dynamic Content

For pages with JavaScript-rendered content:

```bash
python -m docs2md convert https://dynamic-site.com --wait-for-js
```

Options:
- `--wait-for-js`: Wait for JavaScript execution
- `--timeout`: Adjust page load timeout
- `--selector`: Wait for specific element

### Concurrent Processing

Control concurrent processing:

```bash
python -m docs2md convert urls.txt --concurrent-limit 5
```

Options:
- `--concurrent-limit`: Maximum concurrent pages
- `--retry-delay`: Delay between retries
- `--max-retries`: Maximum retry attempts

## Command Reference

### Convert Command

```bash
python -m docs2md convert [OPTIONS] URLS...
```

Options:
- `--output, -o`: Output directory
- `--config, -c`: Configuration file
- `--follow-links`: Follow and process links
- `--max-depth`: Maximum link depth
- `--wait-for-js`: Wait for JavaScript
- `--timeout`: Page load timeout
- `--concurrent-limit`: Concurrent pages
- `--retry-delay`: Retry delay
- `--max-retries`: Maximum retries

### Config Command

```bash
python -m docs2md config [OPTIONS]
```

Options:
- `--output, -o`: Save configuration file
- `--show`: Display current configuration

## Output Format

### Directory Structure

```
output/
├── example.com.md
├── docs1.com.md
└── docs2.com.md
```

### File Format

```markdown
# Page Title

[TOC]

## Section 1
Content...

## Section 2
Content...

### Subsection
Content...
```

### Metadata

Each file includes:
- Original URL
- Processing timestamp
- Success status
- Processing statistics

## Best Practices

### URL Selection

1. Start with main documentation pages
2. Use `--follow-links` for related content
3. Adjust `--max-depth` based on structure

### Performance Optimization

1. Adjust concurrent processing:
   ```bash
   python -m docs2md convert urls.txt --concurrent-limit 10
   ```

2. Configure timeouts:
   ```bash
   python -m docs2md convert url --timeout 60
   ```

3. Use selective link following:
   ```bash
   python -m docs2md convert url --follow-links --max-depth 1
   ```

### Error Handling

1. Enable detailed logging:
   ```yaml
   logging:
     level: "DEBUG"
     file: "docs2md.log"
   ```

2. Use retries for unstable sites:
   ```bash
   python -m docs2md convert url --max-retries 5 --retry-delay 10
   ```

3. Monitor progress:
   - Watch real-time progress
   - Check log files
   - Review error reports

### Resource Management

1. Control memory usage:
   - Limit concurrent processing
   - Process in batches
   - Monitor system resources

2. Manage disk space:
   - Regular cleanup
   - Compress old files
   - Archive completed projects
  </rewritten_file> 