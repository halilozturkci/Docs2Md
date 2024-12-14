"""
Command-line interface for the Docs2Md application.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    FileSizeColumn,
    TotalFileSizeColumn,
    DownloadColumn,
    TransferSpeedColumn
)
from rich.traceback import install as install_rich_traceback
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from datetime import datetime
from time import time
import humanize

from .config import AppConfig
from .web_scraping.url_processor import URLProcessor, ProcessingResult
from .web_scraping.browser_handler import BrowserHandler
from .web_scraping.captcha_handler import CaptchaHandler
from .web_scraping.link_extractor import LinkExtractor
from .web_scraping.html_converter import HTMLConverter
from .github_handler import GitHubHandler
from .converter import Converter

# Set up rich console and traceback handling
console = Console()
install_rich_traceback()

def setup_logging(config: AppConfig) -> None:
    """Configure logging with rich handler."""
    logging.basicConfig(
        level=config.logging.level,
        format=config.logging.format,
        handlers=[
            RichHandler(console=console, rich_tracebacks=True),
            logging.FileHandler(config.logging.file) if config.logging.file else logging.NullHandler()
        ]
    )

def validate_urls(urls: List[str]) -> List[str]:
    """Validate list of URLs."""
    valid_urls = []
    for url in urls:
        try:
            result = urlparse(url)
            if all([
                result.scheme,
                result.netloc,
                result.scheme.lower() in ['http', 'https']  # Only allow HTTP(S)
            ]):
                valid_urls.append(url)
            else:
                console.print(f"[yellow]Warning:[/yellow] Invalid URL format: {url}")
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to parse URL {url}: {str(e)}")
    return valid_urls

async def process_urls_with_progress(
    processor: URLProcessor,
    urls: List[str],
    output_dir: str,
    concurrent_limit: int = 5
) -> List[ProcessingResult]:
    """Process URLs with enhanced progress feedback."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    start_time = time()
    
    # Initialize stats
    stats = {
        'success': 0,
        'failed': 0,
        'total_size': 0,
        'start_time': datetime.now(),
        'largest_file': ('', 0),
        'smallest_file': ('', float('inf')),
        'avg_processing_time': 0,
        'total_processing_time': 0,
        'links_extracted': 0
    }
    
    def create_summary_table() -> Table:
        """Create a summary table with current stats."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        elapsed = time() - start_time
        avg_time = stats['total_processing_time'] / max(stats['success'] + stats['failed'], 1)
        
        table.add_row("Success Rate", f"{stats['success']}/{len(urls)} ({stats['success']/len(urls)*100:.1f}%)")
        table.add_row("Total Content", humanize.naturalsize(stats['total_size']))
        table.add_row("Elapsed Time", humanize.naturaltime(elapsed).replace(" ago", ""))
        table.add_row("Avg Processing Time", f"{avg_time:.2f}s")
        table.add_row("Links Extracted", str(stats['links_extracted']))
        
        if stats['success'] > 0:
            table.add_row(
                "Largest File",
                f"{stats['largest_file'][0]} ({humanize.naturalsize(stats['largest_file'][1])})"
            )
            table.add_row(
                "Smallest File",
                f"{stats['smallest_file'][0]} ({humanize.naturalsize(stats['smallest_file'][1])})"
            )
        
        return table
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        FileSizeColumn(),
        TextColumn("•"),
        TotalFileSizeColumn(),
        TextColumn("•"),
        DownloadColumn(),
        TextColumn("•"),
        TransferSpeedColumn(),
        console=console,
        expand=True
    ) as progress:
        # Overall progress
        overall_task = progress.add_task(
            "[cyan]Processing URLs...[/cyan]",
            total=len(urls),
            start=True
        )
        
        results = []
        
        # Create task group for individual URLs
        url_tasks = progress.add_task(
            "[yellow]Current URL Progress[/yellow]",
            total=len(urls),
            start=False
        )
        
        for idx, url in enumerate(urls, 1):
            url_start_time = time()
            try:
                # Update task description with current URL
                progress.update(
                    url_tasks,
                    description=f"[bold yellow]Processing ({idx}/{len(urls)})[/bold yellow] [blue]{url}[/blue]",
                    start=True
                )
                
                # Process URL
                result = await processor.process_url(url)
                results.append(result)
                
                # Calculate processing time
                processing_time = time() - url_start_time
                stats['total_processing_time'] += processing_time
                
                if result.success:
                    # Save markdown content
                    output_file = Path(output_dir) / f"{urlparse(url).netloc}.md"
                    content = result.markdown_content
                    output_file.write_text(content)
                    
                    # Update stats
                    content_size = len(content)
                    stats['success'] += 1
                    stats['total_size'] += content_size
                    stats['links_extracted'] += len(result.extracted_links)
                    
                    # Update file size records
                    if content_size > stats['largest_file'][1]:
                        stats['largest_file'] = (url, content_size)
                    if content_size < stats['smallest_file'][1]:
                        stats['smallest_file'] = (url, content_size)
                    
                    # Success message with detailed metrics
                    progress.console.print(Panel(
                        f"[green]✓[/green] Successfully processed [blue]{url}[/blue]\n"
                        f"• Content Size: [green]{humanize.naturalsize(content_size)}[/green]\n"
                        f"• Processing Time: [yellow]{processing_time:.2f}s[/yellow]\n"
                        f"• Links Found: [cyan]{len(result.extracted_links)}[/cyan]",
                        title="Success",
                        border_style="green"
                    ))
                else:
                    # Failure message
                    stats['failed'] += 1
                    progress.console.print(Panel(
                        f"[red]✗[/red] Failed to process [blue]{url}[/blue]\n"
                        f"• Error: [red]{result.error}[/red]\n"
                        f"• Processing Time: [yellow]{processing_time:.2f}s[/yellow]",
                        title="Error",
                        border_style="red"
                    ))
                
            except Exception as e:
                # Handle unexpected errors
                processing_time = time() - url_start_time
                stats['failed'] += 1
                stats['total_processing_time'] += processing_time
                
                progress.console.print(Panel(
                    f"[red]Error:[/red] Failed to process [blue]{url}[/blue]\n"
                    f"• Error: [red]{str(e)}[/red]\n"
                    f"• Processing Time: [yellow]{processing_time:.2f}s[/yellow]",
                    title="Error",
                    border_style="red"
                ))
                
                results.append(ProcessingResult(
                    url=url,
                    markdown_content="",
                    extracted_links=[],
                    success=False,
                    error=str(e)
                ))
            
            # Update progress
            progress.update(url_tasks, advance=1)
            progress.update(overall_task, advance=1)
            
            # Show current summary table
            progress.console.print(Panel(
                create_summary_table(),
                title="Current Progress",
                border_style="blue"
            ))
    
    # Final summary with detailed statistics
    total_time = time() - start_time
    success_rate = (stats['success'] / len(urls)) * 100
    
    # Create final summary table
    final_table = Table(show_header=True, header_style="bold magenta", title="Final Results")
    final_table.add_column("Metric", style="cyan")
    final_table.add_column("Value", style="green")
    
    final_table.add_row("Total URLs Processed", str(len(urls)))
    final_table.add_row("Successful", f"{stats['success']} ({success_rate:.1f}%)")
    final_table.add_row("Failed", f"{stats['failed']} ({100-success_rate:.1f}%)")
    final_table.add_row("Total Content Size", humanize.naturalsize(stats['total_size']))
    final_table.add_row("Total Processing Time", f"{total_time:.2f}s")
    final_table.add_row("Average Processing Time", f"{stats['total_processing_time']/len(urls):.2f}s")
    final_table.add_row("Total Links Extracted", str(stats['links_extracted']))
    final_table.add_row("Processing Speed", f"{len(urls)/total_time:.2f} URLs/s")
    
    if stats['success'] > 0:
        final_table.add_row(
            "Largest File",
            f"{stats['largest_file'][0]} ({humanize.naturalsize(stats['largest_file'][1])})"
        )
        final_table.add_row(
            "Smallest File",
            f"{stats['smallest_file'][0]} ({humanize.naturalsize(stats['smallest_file'][1])})"
        )
        final_table.add_row(
            "Average File Size",
            humanize.naturalsize(stats['total_size'] / stats['success'])
        )
    
    console.print("\n")
    console.print(Panel(final_table, title="[bold]Final Summary[/bold]", border_style="green"))
    
    # Show failed URLs in a separate table if any
    if stats['failed'] > 0:
        failed_table = Table(show_header=True, header_style="bold red", title="Failed URLs")
        failed_table.add_column("URL", style="blue")
        failed_table.add_column("Error", style="red")
        
        for result in results:
            if not result.success:
                failed_table.add_row(result.url, result.error)
        
        console.print("\n")
        console.print(Panel(failed_table, title="[bold red]Failed URLs[/bold red]", border_style="red"))
    
    return results

@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str]) -> None:
    """Docs2Md - Convert web documentation to markdown."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = AppConfig.load(config)
    setup_logging(ctx.obj['config'])

@cli.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--output', '-o', default='output', help='Output directory for markdown files')
@click.option('--follow-links/--no-follow-links', default=False, help='Follow and process linked pages')
@click.option('--max-depth', default=1, help='Maximum depth for link following')
@click.option('--wait-for-js/--no-wait-for-js', default=False, help='Wait for JavaScript execution')
@click.option('--timeout', default=30, help='Page load timeout in seconds')
@click.option('--concurrent-limit', default=5, help='Maximum number of concurrent pages to process')
@click.pass_context
def convert(
    ctx: click.Context,
    urls: List[str],
    output: str,
    follow_links: bool,
    max_depth: int,
    wait_for_js: bool,
    timeout: int,
    concurrent_limit: int
) -> None:
    """Convert web pages to markdown format."""
    config = ctx.obj['config']
    
    # Update config with CLI options
    config.scraping.follow_links = follow_links
    config.scraping.max_depth = max_depth
    config.output_dir = output
    config.browser.timeout = timeout
    config.browser.wait_for_js = wait_for_js
    config.scraping.concurrent_limit = concurrent_limit
    
    # Validate URLs
    valid_urls = validate_urls(urls)
    if not valid_urls:
        console.print("[red]Error:[/red] No valid URLs provided")
        sys.exit(1)
    
    # Initialize components
    processor = URLProcessor(
        browser_handler=BrowserHandler(
            headless=config.browser.headless,
            timeout=config.browser.timeout,
            wait_for_js=config.browser.wait_for_js
        ),
        captcha_handler=CaptchaHandler(api_key=config.captcha.api_key),
        link_extractor=LinkExtractor(),
        html_converter=HTMLConverter()
    )
    
    # Process URLs
    try:
        results = asyncio.run(process_urls_with_progress(
            processor,
            valid_urls,
            output,
            concurrent_limit=config.scraping.concurrent_limit
        ))
        
        # Print summary
        success_count = sum(1 for r in results if r.success)
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"✓ Successfully processed: {success_count}/{len(results)}")
        console.print(f"✗ Failed: {len(results) - success_count}/{len(results)}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Path to save configuration')
@click.pass_context
def config(ctx: click.Context, output: Optional[str]) -> None:
    """Save current configuration to file."""
    try:
        ctx.obj['config'].save(output)
        console.print(f"[green]Configuration saved to {output or '~/.docs2md/config.yaml'}[/green]")
    except Exception as e:
        console.print(f"[red]Error saving configuration:[/red] {str(e)}")
        sys.exit(1)

@cli.command()
@click.option(
    '--github-repo',
    required=True,
    help='GitHub repository URL'
)
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Enable/disable interactive directory selection'
)
@click.option(
    '--dirs',
    help='Comma-separated list of directories to process'
)
@click.option(
    '--output-file',
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help='Path for the output MD file'
)
def github(github_repo: str, interactive: bool, dirs: str, output_file: str):
    """Process GitHub repository documentation."""
    try:
        handler = GitHubHandler(github_repo)
        try:
            structure = handler.get_repository_structure()
            
            if interactive:
                selected_dirs = handler.show_interactive_selection(structure)
            else:
                selected_dirs = dirs.split(',') if dirs else []
            
            if not selected_dirs:
                raise click.ClickException("No directories selected for processing")
            
            temp_dir = handler.download_directories(selected_dirs)
            
            # Process the downloaded files using the local Converter
            converter = Converter(temp_dir, output_file)
            converter.convert()
            
        finally:
            handler.cleanup()
            
        console.print("[green]Conversion completed successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Conversion failed: {str(e)}[/red]")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli(obj={}) 