import click
from pathlib import Path
import logging
import sys
import os
from rich.logging import RichHandler

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.converter import Converter
from src.github_handler import GitHubHandler

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

@click.command()
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
def main(github_repo: str, interactive: bool, dirs: str, output_file: str):
    """Convert MDX documentation files to a single MD file."""
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
            
            # Process the downloaded files
            converter = Converter(temp_dir, output_file)
            converter.convert()
            
        finally:
            handler.cleanup()
            
        logger.info("Conversion completed successfully")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    main() 