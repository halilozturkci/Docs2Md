from pathlib import Path
from typing import List, Dict
import logging
import re
from src.file_handler import FileHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Converter:
    def __init__(self, input_dir: str, output_file: str):
        """Initialize Converter with input directory and output file path.
        
        Args:
            input_dir (str): Path to the directory containing MDX files
            output_file (str): Path where the output MD file will be saved
        """
        self.file_handler = FileHandler(input_dir)
        self.output_file = Path(output_file)
        self.toc_entries = []

    def _adjust_image_paths(self, content: str, file_path: Path) -> str:
        """Adjust image paths in the content to be relative to the output file.
        
        Args:
            content (str): The MDX content
            file_path (Path): Path to the current MDX file
            
        Returns:
            str: Content with adjusted image paths
        """
        def replace_image_path(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            
            # Handle URLs
            if image_path.startswith(('http://', 'https://')):
                return f'![{alt_text}]({image_path})'
            
            try:
                # If path starts with '/', treat it as relative to input directory
                if image_path.startswith('/'):
                    image_path = image_path.lstrip('/')
                    abs_image_path = (self.file_handler.input_dir / image_path).resolve()
                else:
                    # Otherwise, treat it as relative to the MDX file's location
                    abs_image_path = (file_path.parent / image_path).resolve()
                
                # Get the relative path from input directory
                try:
                    rel_path = abs_image_path.relative_to(self.file_handler.input_dir)
                    return f'![{alt_text}]({rel_path})'
                except ValueError:
                    # If the image is outside the input directory, keep the original path
                    logger.warning(f"Image path {image_path} is outside the documentation directory")
                    return f'![{alt_text}]({image_path})'
                    
            except Exception as e:
                logger.warning(f"Error processing image path {image_path}: {str(e)}")
                return f'![{alt_text}]({image_path})'

        # Replace image markdown syntax
        content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_image_path, content)
        return content

    def _process_content(self, content: str, file_path: Path) -> str:
        """Process the MDX content to convert it to MD format.
        
        Args:
            content (str): The MDX content
            file_path (Path): Path to the current MDX file
            
        Returns:
            str: Processed content in MD format
        """
        # Add file path as heading
        heading = self.file_handler.create_heading_from_path(file_path)
        self.toc_entries.append((heading.count('#'), heading.lstrip('#').strip()))
        
        # Adjust image paths
        content = self._adjust_image_paths(content, file_path)
        
        # Add heading and content with proper spacing
        return f"{heading}\n\n{content}\n\n"

    def _generate_toc(self) -> str:
        """Generate table of contents from collected entries.
        
        Returns:
            str: Table of contents in MD format
        """
        toc = "# Table of Contents\n\n"
        for depth, title in self.toc_entries:
            indent = "  " * (depth - 1)
            link = title.lower().replace(' ', '-')
            toc += f"{indent}- [{title}](#{link})\n"
        return toc + "\n"

    def convert(self) -> None:
        """Convert all MDX files to a single MD file."""
        try:
            mdx_files = self.file_handler.find_mdx_files()
            
            with open(self.output_file, 'w', encoding='utf-8') as out_file:
                # Process each MDX file
                content_blocks = []
                for file_path in mdx_files:
                    logger.info(f"Processing {file_path}")
                    metadata, content = self.file_handler.read_mdx_file(file_path)
                    processed_content = self._process_content(content, file_path)
                    content_blocks.append(processed_content)
                
                # Generate and write table of contents
                toc = self._generate_toc()
                out_file.write(toc)
                
                # Write all content blocks
                out_file.write('\n'.join(content_blocks))
                
            logger.info(f"Successfully created {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            raise