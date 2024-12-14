import os
from pathlib import Path
from typing import List, Tuple
import frontmatter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, input_dir: str):
        """Initialize FileHandler with input directory path.
        
        Args:
            input_dir (str): Path to the directory containing MDX/MD files
        """
        self.input_dir = Path(input_dir)
        if not self.input_dir.exists():
            raise ValueError(f"Input directory {input_dir} does not exist")

    def find_markdown_files(self) -> List[Path]:
        """Find all MDX and MD files in the input directory recursively.
        
        Returns:
            List[Path]: List of paths to MDX and MD files
        """
        markdown_files = []
        try:
            # Find both .mdx and .md files
            for extension in ["*.mdx", "*.md"]:
                for path in self.input_dir.rglob(extension):
                    if path.is_file():
                        markdown_files.append(path)
            
            logger.info(f"Found {len(markdown_files)} Markdown files")
            return sorted(markdown_files)
        except Exception as e:
            logger.error(f"Error finding Markdown files: {str(e)}")
            raise

    def read_markdown_file(self, file_path: Path) -> Tuple[dict, str]:
        """Read and parse an MDX/MD file.
        
        Args:
            file_path (Path): Path to the Markdown file
            
        Returns:
            Tuple[dict, str]: Tuple containing frontmatter metadata and content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                return post.metadata, post.content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise

    def get_relative_path(self, file_path: Path) -> str:
        """Get the relative path of a file from the input directory.
        
        Args:
            file_path (Path): Path to the file
            
        Returns:
            str: Relative path as string
        """
        return str(file_path.relative_to(self.input_dir))

    def create_heading_from_path(self, file_path: Path) -> str:
        """Create a heading from the file path.
        
        Args:
            file_path (Path): Path to the file
            
        Returns:
            str: Heading string based on file path
        """
        rel_path = self.get_relative_path(file_path)
        parts = Path(rel_path).parts
        
        # Remove file extension (.md or .mdx) and create heading
        heading = parts[-1].replace('.mdx', '').replace('.md', '')
        depth = len(parts) - 1
        
        # Create markdown heading with appropriate level
        return f"{'#' * (depth + 1)} {heading}" 