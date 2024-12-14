import click
from pathlib import Path
import logging
import sys
import os
from rich.logging import RichHandler
from docs2md.converter import Converter

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Documentation converter tool."""
    pass

@cli.command()
@click.option(
    '--url',
    required=True,
    help='URL to convert'
)
@click.option(
    '--output-file',
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help='Path for the output MD file'
)
@click.option(
    '--max-depth',
    default=5,
    type=int,
    help='Maximum depth for crawling links'
)
@click.option(
    '--excluded-types',
    default='.pdf,.zip,.exe,.dmg',
    help='Comma-separated list of file extensions to exclude'
)
@click.option(
    '--max-workers',
    default=4,
    type=int,
    help='Number of parallel workers'
)
@click.option(
    '--follow-paths',
    help='Comma-separated list of paths to follow (e.g. /docs,/api)'
)
@click.option(
    '--show-progress/--no-progress',
    default=True,
    help='Show progress bars'
)
def url_convert(url: str, output_file: str, max_depth: int, excluded_types: str, 
                max_workers: int, follow_paths: str, show_progress: bool):
    """Convert documentation from URL to markdown."""
    try:
        converter = Converter(
            input_dir="temp",  # Geçici dizin
            output_file=output_file,
            max_depth=max_depth,
            excluded_types=set(excluded_types.split(',')),
            max_workers=max_workers,
            follow_paths=follow_paths.split(',') if follow_paths else None,
            show_progress=show_progress
        )
        
        converter.convert_url_to_markdown(url)
        logger.info("URL conversion completed successfully")
        
    except Exception as e:
        logger.error(f"URL conversion failed: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli() 