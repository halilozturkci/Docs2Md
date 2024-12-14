# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using Docs2Md.

## Table of Contents

- [Common Issues](#common-issues)
- [Error Messages](#error-messages)
- [Performance Problems](#performance-problems)
- [Quality Issues](#quality-issues)
- [Advanced Debugging](#advanced-debugging)

## Common Issues

### CAPTCHA Detection

#### Symptoms
- Frequent CAPTCHA challenges
- Failed page loads
- Access denied messages

#### Solutions

1. Configure 2captcha:
   ```yaml
   captcha:
     api_key: "your-2captcha-key"
     service: "2captcha"
     timeout: 120
   ```

2. Use stealth mode:
   - Rotate user agents
   - Add delays between requests
   - Use proxy servers

3. Adjust browser settings:
   ```yaml
   browser:
     headless: false  # Try with visible browser
     user_agent: "..."  # Use realistic user agent
   ```

### Dynamic Content Not Loading

#### Symptoms
- Missing content
- Incomplete pages
- JavaScript errors

#### Solutions

1. Increase timeout:
   ```yaml
   browser:
     timeout: 60  # Increase page load timeout
   ```

2. Wait for JavaScript:
   ```bash
   python -m docs2md convert url --wait-for-js
   ```

3. Use specific selectors:
   ```bash
   python -m docs2md convert url --selector "#content"
   ```

### Rate Limiting

#### Symptoms
- HTTP 429 errors
- Connection refused
- Temporary blocks

#### Solutions

1. Adjust retry settings:
   ```yaml
   scraping:
     max_retries: 5
     retry_delay: 30
   ```

2. Reduce concurrent requests:
   ```yaml
   scraping:
     concurrent_limit: 3
   ```

3. Use proxy rotation:
   ```yaml
   browser:
     proxy: "http://proxy:port"
   ```

## Error Messages

### Connection Errors

#### "Failed to establish connection"
```
Error: Failed to establish connection to example.com
```

Solutions:
1. Check internet connection
2. Verify URL accessibility
3. Try with different DNS
4. Check proxy settings

#### "SSL/TLS Error"
```
Error: SSL certificate verification failed
```

Solutions:
1. Update SSL certificates
2. Check system time
3. Use `--ignore-ssl-errors`

### CAPTCHA Errors

#### "CAPTCHA solving failed"
```
Error: Failed to solve CAPTCHA: Invalid API key
```

Solutions:
1. Verify API key
2. Check account balance
3. Increase timeout
4. Try different CAPTCHA type

#### "CAPTCHA timeout"
```
Error: CAPTCHA solving timeout after 120s
```

Solutions:
1. Increase timeout
2. Check service status
3. Verify CAPTCHA type
4. Use backup service

### Content Errors

#### "Failed to extract content"
```
Error: No content found matching selector
```

Solutions:
1. Check selector
2. Wait for content load
3. Verify page structure
4. Use browser inspection

## Performance Problems

### High Memory Usage

#### Symptoms
- Increasing memory consumption
- System slowdown
- Out of memory errors

#### Solutions

1. Limit concurrent processing:
   ```yaml
   scraping:
     concurrent_limit: 5
   ```

2. Process in batches:
   ```bash
   python -m docs2md convert urls.txt --batch-size 10
   ```

3. Enable garbage collection:
   ```yaml
   browser:
     gc_interval: 10
   ```

### Slow Processing

#### Symptoms
- Long processing times
- Timeouts
- Queue buildup

#### Solutions

1. Optimize settings:
   ```yaml
   browser:
     headless: true
     images: false
     javascript: minimal
   ```

2. Increase resources:
   - Add more CPU cores
   - Increase memory
   - Use faster storage

3. Adjust timeouts:
   ```yaml
   browser:
     timeout: 30
     wait_until: "domcontentloaded"
   ```

## Quality Issues

### Formatting Problems

#### Symptoms
- Missing styles
- Broken layouts
- Incorrect headings

#### Solutions

1. Adjust conversion settings:
   ```yaml
   converter:
     preserve_tables: true
     keep_images: true
     fix_links: true
   ```

2. Use custom selectors:
   ```yaml
   converter:
     content_selector: "article"
     exclude_selectors: [".ads", ".comments"]
   ```

3. Post-process content:
   ```yaml
   converter:
     post_processors:
       - fix_headings
       - clean_whitespace
       - normalize_links
   ```

### Missing Content

#### Symptoms
- Incomplete sections
- Missing images
- Broken links

#### Solutions

1. Enable deep extraction:
   ```yaml
   scraping:
     extract_frames: true
     follow_redirects: true
     load_resources: true
   ```

2. Verify selectors:
   ```yaml
   converter:
     verify_content: true
     report_missing: true
   ```

3. Use content validation:
   ```yaml
   converter:
     validate_output: true
     min_content_length: 1000
   ```

## Advanced Debugging

### Enable Debug Logging

```yaml
logging:
  level: "DEBUG"
  file: "debug.log"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Use Browser Developer Tools

1. Disable headless mode:
   ```yaml
   browser:
     headless: false
     devtools: true
   ```

2. Enable network logging:
   ```yaml
   logging:
     network: true
     requests: true
   ```

### Profile Performance

1. Enable profiling:
   ```yaml
   debug:
     profile: true
     trace: true
     memory_tracking: true
   ```

2. Generate reports:
   ```bash
   python -m docs2md convert url --profile --report
   ```

### Common Debug Commands

```bash
# Test single URL with debugging
python -m docs2md convert url --debug

# Generate HAR file
python -m docs2md convert url --har-file debug.har

# Profile memory usage
python -m docs2md convert url --memory-profile

# Network debugging
python -m docs2md convert url --network-debug
```

### Best Practices

1. Systematic Debugging:
   - Start with simple cases
   - Isolate problems
   - Test incrementally
   - Document findings

2. Performance Monitoring:
   - Track resource usage
   - Monitor response times
   - Log error patterns
   - Analyze bottlenecks

3. Quality Assurance:
   - Validate output
   - Compare with source
   - Check formatting
   - Verify links 