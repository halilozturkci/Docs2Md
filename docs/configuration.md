# Configuration Guide

This guide explains all configuration options available in Docs2Md and how to use them effectively.

## Table of Contents

- [Configuration File](#configuration-file)
- [Browser Settings](#browser-settings)
- [CAPTCHA Settings](#captcha-settings)
- [Scraping Settings](#scraping-settings)
- [Logging Settings](#logging-settings)
- [Advanced Configuration](#advanced-configuration)

## Configuration File

### Location

The configuration file can be placed in:
1. Default location: `~/.docs2md/config.yaml`
2. Custom location: Specified with `--config` option

### Format

The configuration uses YAML format:

```yaml
browser:
  headless: true
  timeout: 30
  user_agent: "Mozilla/5.0 ..."
  viewport_size:
    width: 1920
    height: 1080

captcha:
  api_key: "your-2captcha-key"
  service: "2captcha"
  timeout: 120

scraping:
  max_retries: 3
  retry_delay: 5
  concurrent_limit: 5
  follow_links: false
  max_depth: 1

logging:
  level: "INFO"
  file: "docs2md.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

output_dir: "output"
```

### Managing Configuration

1. Create default configuration:
   ```bash
   python -m docs2md config
   ```

2. Save to custom location:
   ```bash
   python -m docs2md config --output my_config.yaml
   ```

3. View current configuration:
   ```bash
   python -m docs2md config --show
   ```

## Browser Settings

### Headless Mode

```yaml
browser:
  headless: true  # Run browser in headless mode
```

Options:
- `true`: No visible browser (default)
- `false`: Show browser window

### Timeout Settings

```yaml
browser:
  timeout: 30  # Page load timeout in seconds
```

Recommended values:
- Static pages: 30 seconds
- Dynamic content: 60 seconds
- Heavy applications: 120 seconds

### User Agent

```yaml
browser:
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

Common user agents:
- Chrome Windows
- Chrome macOS
- Firefox Windows
- Safari macOS

### Viewport Size

```yaml
browser:
  viewport_size:
    width: 1920
    height: 1080
```

Common resolutions:
- Desktop: 1920x1080
- Laptop: 1366x768
- Tablet: 1024x768
- Mobile: 375x812

## CAPTCHA Settings

### 2captcha Integration

```yaml
captcha:
  api_key: "your-2captcha-key"  # Required for CAPTCHA solving
  service: "2captcha"           # CAPTCHA service provider
  timeout: 120                  # Solving timeout in seconds
```

### Timeout Configuration

Recommended timeouts:
- Simple CAPTCHAs: 60 seconds
- reCAPTCHA v2: 120 seconds
- reCAPTCHA v3: 180 seconds
- hCaptcha: 150 seconds

## Scraping Settings

### Retry Configuration

```yaml
scraping:
  max_retries: 3     # Maximum retry attempts
  retry_delay: 5     # Delay between retries (seconds)
```

Recommended values:
- Stable sites: 3 retries, 5s delay
- Unstable sites: 5 retries, 10s delay
- Rate-limited sites: 3 retries, 30s delay

### Concurrent Processing

```yaml
scraping:
  concurrent_limit: 5  # Maximum concurrent pages
```

Guidelines:
- Small sites: 3-5 concurrent
- Medium sites: 5-10 concurrent
- Large sites: 10-20 concurrent

### Link Following

```yaml
scraping:
  follow_links: false  # Whether to follow links
  max_depth: 1        # Maximum link depth
```

Depth guidelines:
- Documentation: 2-3 levels
- Blogs: 1-2 levels
- Knowledge bases: 3-4 levels

## Logging Settings

### Log Levels

```yaml
logging:
  level: "INFO"  # Logging level
```

Available levels:
- `DEBUG`: Detailed debugging
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical issues

### Log File

```yaml
logging:
  file: "docs2md.log"  # Log file path
```

Options:
- Absolute path: `/path/to/logs/docs2md.log`
- Relative path: `logs/docs2md.log`
- Disabled: `null`

### Log Format

```yaml
logging:
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

Format placeholders:
- `%(asctime)s`: Timestamp
- `%(name)s`: Logger name
- `%(levelname)s`: Log level
- `%(message)s`: Log message
- `%(filename)s`: Source file
- `%(lineno)d`: Line number

## Advanced Configuration

### Environment Variables

Override configuration with environment variables:

```bash
export DOCS2MD_BROWSER_HEADLESS=false
export DOCS2MD_CAPTCHA_API_KEY=your_key
export DOCS2MD_SCRAPING_MAX_RETRIES=5
```

### Command Line Overrides

Command line options override configuration file:

```bash
python -m docs2md convert url \
  --headless false \
  --timeout 60 \
  --concurrent-limit 10
```

### Configuration Profiles

Create multiple configuration files for different scenarios:

```yaml
# development.yaml
browser:
  headless: false
  timeout: 60

# production.yaml
browser:
  headless: true
  timeout: 30
```

Use with:
```bash
python -m docs2md convert url --config production.yaml
```

### Best Practices

1. Security:
   - Keep API keys secure
   - Use environment variables
   - Restrict log file permissions

2. Performance:
   - Adjust timeouts based on site
   - Balance concurrent processing
   - Monitor resource usage

3. Maintenance:
   - Regular configuration review
   - Log rotation
   - Backup configurations
 