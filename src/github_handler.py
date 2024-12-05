import os
import tempfile
from pathlib import Path
from typing import List, Dict
import logging
from github import Github
import requests
from rich.prompt import Confirm
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import Progress
from datetime import datetime
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.prompt import Prompt
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
import questionary
from rich.style import Style

# Load environment variables
load_dotenv()

class GitHubHandler:
    def __init__(self, repo_url: str):
        """Initialize GitHub handler with repository URL."""
        self.repo_url = repo_url
        self.token = os.getenv('GITHUB_TOKEN')
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        self.g = Github(self.token)
        self.console = Console()
        
        # Setup logging first
        self._setup_logging()
        
        # Create temp directory in current working directory
        current_dir = os.getcwd()
        self.temp_dir = os.path.join(current_dir, 'temp')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            self.logger.info(f"Created temporary directory: {self.temp_dir}")
        else:
            # Clean existing temp directory
            import shutil
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            self.logger.info(f"Cleaned and recreated temporary directory: {self.temp_dir}")
        
    def _setup_logging(self):
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        
    def get_repository_structure(self) -> Dict:
        """Fetch and return repository structure and README if exists."""
        try:
            self.logger.info(f"Fetching repository structure from: {self.repo_url}")
            repo_name = self.repo_url.split('/')[-2:]
            repo = self.g.get_repo('/'.join(repo_name))
            self.logger.info(f"Successfully connected to repository: {repo.full_name}")
            
            # Get README content if exists
            try:
                readme = repo.get_readme()
                readme_content = readme.decoded_content.decode('utf-8')
                self.console.print(Panel(
                    Markdown(readme_content),
                    title="📖 Repository README",
                    border_style="blue"
                ))
            except Exception as e:
                self.logger.debug(f"No README found: {str(e)}")
            
            # Get the default branch
            default_branch = repo.default_branch
            self.logger.info(f"Using default branch: {default_branch}")
            
            # Get the tree of the default branch
            tree = repo.get_git_tree(default_branch).tree
            
            # Filter directories (exclude hidden)
            directories = [
                item for item in tree 
                if item.type == 'tree' and not item.path.startswith('.')
            ]
            total_items = len(directories)
            
            self.logger.info(f"Found {total_items} top-level directories")
            
            structure = {}
            for idx, item in enumerate(directories, 1):
                self.logger.info(f"Processing directory ({idx}/{total_items}): {item.path}")
                structure[item.path] = {
                    'type': 'dir',
                    'path': item.path,
                    'sha': item.sha
                }
            
            self.logger.info("Repository structure fetched successfully")
            return structure
        
        except Exception as e:
            self.logger.error(f"Error fetching repository structure: {str(e)}")
            raise

    def _get_last_update(self, repo, path: str) -> str:
        """Get last update time for directory."""
        try:
            self.logger.debug(f"Fetching last update time for: {path}")
            commits = repo.get_commits(path=path)
            latest_commit = next(iter(commits), None)
            
            if latest_commit:
                commit_date = latest_commit.commit.author.date
                formatted_date = commit_date.strftime("%Y-%m-%d %H:%M:%S")
                self.logger.debug(f"Last update for {path}: {formatted_date}")
                return formatted_date
            return "unknown date"
        except Exception as e:
            self.logger.warning(f"Could not get last update for {path}: {str(e)}")
            return "unknown date"

    def _get_dir_size(self, repo, path: str) -> str:
        """Get directory size in human-readable format."""
        try:
            self.logger.debug(f"Calculating size for directory: {path}")
            total_size = self._get_dir_size_bytes(repo, path)
            size_str = self._format_size(total_size)
            self.logger.debug(f"Directory {path} size: {size_str}")
            return size_str
        except Exception as e:
            self.logger.warning(f"Could not get size for {path}: {str(e)}")
            return "unknown size"

    def _get_dir_size_bytes(self, repo, path: str) -> int:
        """Helper method to get directory size in bytes."""
        total_size = 0
        try:
            contents = repo.get_contents(path)
            for content in contents:
                if content.type == "file":
                    total_size += content.size
                elif content.type == "dir":
                    total_size += self._get_dir_size_bytes(repo, content.path)
        except Exception as e:
            self.logger.debug(f"Error getting size for {path}: {str(e)}")
        return total_size

    def _format_size(self, size: int) -> str:
        """Convert size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def show_interactive_selection(self, structure: Dict) -> List[str]:
        """Show interactive directory selection interface."""
        self.logger.info("Preparing interactive directory selection...")
        
        # Prepare directory list for selection
        directories = list(structure.keys())
        
        # Create checkbox prompt
        selected = questionary.checkbox(
            'Select directories to process:',
            choices=directories,
            instruction='(Use arrow keys to move, Space to select, Enter to confirm)',
            style=questionary.Style([
                ('selected', 'fg:green bold'),
                ('instruction', 'fg:yellow'),
                ('pointer', 'fg:cyan bold'),
                ('checkbox', 'fg:cyan'),
            ])
        ).ask()
        
        if not selected:
            return []
        
        self.logger.info(f"Selected directories: {', '.join(selected)}")
        return selected

    def _get_dialog_style(self):
        """Get style configuration for the dialog."""
        return {
            'dialog': 'bg:#333333',
            'dialog.body': 'bg:#333333 #ffffff',
            'dialog.border': 'bg:#333333 #00ff00',
            'button': 'bg:#666666',
            'button.focused': 'bg:#888888',
            'checkbox': '#00ff00',
            'checkbox.focused': 'bg:#888888 #00ff00',
        }

    def download_directories(self, selected_dirs: List[str]) -> str:
        """Download selected directories to temporary location."""
        self.logger.info("Initializing directory download...")
        self.temp_dir = tempfile.mkdtemp(prefix="github_docs_")
        self.logger.info(f"Created temporary directory: {self.temp_dir}")
        
        with Progress() as progress:
            task = progress.add_task("[green]Downloading...", total=len(selected_dirs))
            
            for dir_path in selected_dirs:
                try:
                    self.logger.info(f"Downloading directory: {dir_path}")
                    self._download_directory(dir_path)
                    self.logger.info(f"Successfully downloaded: {dir_path}")
                    progress.advance(task)
                except Exception as e:
                    self.logger.error(f"Error downloading {dir_path}: {str(e)}")
                    raise
        
        self.logger.info("All directories downloaded successfully")
        return self.temp_dir

    def cleanup(self):
        """Clean up temporary directory."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                self.logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
                import shutil
                shutil.rmtree(self.temp_dir)
                self.logger.info("Cleanup completed successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            # Don't raise the exception here, just log it
            # We don't want cleanup errors to mask the main operation's success/failure

    def _download_directory(self, dir_path: str):
        """Download a directory and its contents recursively."""
        try:
            self.logger.info(f"Starting download of directory: {dir_path}")
            repo_name = self.repo_url.split('/')[-2:]
            repo = self.g.get_repo('/'.join(repo_name))
            
            def download_content(content_path: str, local_path: str):
                """Recursively download directory contents."""
                contents = repo.get_contents(content_path)
                
                if not isinstance(contents, list):
                    contents = [contents]
                
                for content in contents:
                    current_local_path = os.path.join(local_path, content.name)
                    
                    if content.type == "dir":
                        os.makedirs(current_local_path, exist_ok=True)
                        self.logger.info(f"Created directory: {content.path}")
                        download_content(content.path, current_local_path)
                    else:
                        # Format file size
                        size = self._format_size(content.size)
                        self.logger.info(f"Downloading file: {content.path} ({size})")
                        
                        with open(current_local_path, 'wb') as f:
                            f.write(content.decoded_content)
            
            # Create target directory
            target_dir = os.path.join(self.temp_dir, dir_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Start recursive download
            download_content(dir_path, target_dir)
            
            self.logger.info(f"Successfully downloaded directory: {dir_path}")
            
        except Exception as e:
            self.logger.error(f"Error downloading directory {dir_path}: {str(e)}")
            raise