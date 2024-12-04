import click
from pathlib import Path
import logging
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.converter import Converter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    '--input-dir',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Directory containing MDX files'
)
@click.option(
    '--output-file',
    required=True,
    type=click.Path(file_okay=True, dir_okay=False),
    help='Path for the output MD file'
)
def main(input_dir: str, output_file: str):
    """Convert MDX documentation files to a single MD file."""
    try:
        logger.info(f"Starting conversion from {input_dir} to {output_file}")
        converter = Converter(input_dir, output_file)
        converter.convert()
        logger.info("Conversion completed successfully")
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    main() 