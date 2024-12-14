from pathlib import Path
from typing import List, Dict, Set, Optional
import logging
import re
from .file_handler import FileHandler
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import mimetypes
import requests
from bs4 import BeautifulSoup
import html2text
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import urllib3
import warnings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG level
logger = logging.getLogger(__name__)
console = Console()

class Converter:
    def __init__(self, 
                 input_dir: str, 
                 output_file: str,
                 max_depth: int = 5,
                 excluded_types: Optional[Set[str]] = None,
                 max_workers: int = 4,
                 follow_paths: Optional[List[str]] = None,
                 show_progress: bool = True):
        """Initialize Converter with enhanced options.
        
        Args:
            input_dir (str): Path to the directory containing MDX/MD files
            output_file (str): Path where the output MD file will be saved
            max_depth (int): Maximum depth for crawling links (default: 5)
            excluded_types (Set[str]): File extensions to exclude (e.g. {'.pdf', '.zip'})
            max_workers (int): Number of parallel workers (default: 4)
            follow_paths (List[str]): List of paths to follow (e.g. ['/docs', '/blog'])
            show_progress (bool): Whether to show progress bars (default: True)
        """
        self.input_dir = Path(input_dir)
        # Create input directory if it doesn't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.file_handler = FileHandler(input_dir)
        self.output_file = output_path
        self.toc_entries = []
        self.visited_urls = set()
        self.base_url = None
        self.selected_paths = follow_paths or []
        self.max_depth = max_depth
        self.excluded_types = excluded_types or {'.pdf', '.zip', '.exe', '.dmg'}
        self.max_workers = max_workers
        self.show_progress = show_progress
        self.progress_bar = None
        
        # Initialize Selenium WebDriver
        self.driver = None
        self._setup_webdriver()

    def _setup_webdriver(self):
        """Set up Selenium WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # Use new headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')  # Set window size
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--log-level=3')  # Only show fatal errors
            
            # Add additional Chrome options for better performance
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            
            # Try to create Chrome driver without specifying the path
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.set_page_load_timeout(30)
                logger.debug("Chrome WebDriver setup completed successfully")
            except Exception as chrome_error:
                logger.error(f"Error creating Chrome driver: {str(chrome_error)}")
                # Try Firefox as fallback
                try:
                    from selenium.webdriver.firefox.options import Options as FirefoxOptions
                    firefox_options = FirefoxOptions()
                    firefox_options.add_argument('--headless')
                    firefox_options.add_argument('--width=1920')
                    firefox_options.add_argument('--height=1080')
                    self.driver = webdriver.Firefox(options=firefox_options)
                    self.driver.set_page_load_timeout(30)
                    logger.debug("Firefox WebDriver setup completed successfully")
                except Exception as firefox_error:
                    logger.error(f"Error creating Firefox driver: {str(firefox_error)}")
                    raise Exception("Failed to initialize any WebDriver")
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            raise

    def _get_page_content(self, url: str) -> Optional[str]:
        """Get page content using Selenium with proper error handling."""
        try:
            logger.debug(f"Fetching URL with Selenium: {url}")
            self.driver.get(url)
            
            # Wait for initial page load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for specific elements that indicate the page is fully loaded
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "a")) > 0
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for links to load: {str(e)}")
            
            # Additional wait for dynamic content
            time.sleep(5)  # Increased wait time
            
            # Scroll to bottom to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait after scrolling
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            
            # Get the page source after all content is loaded
            page_source = self.driver.page_source
            
            # Log the content length for debugging
            logger.debug(f"Retrieved page content length: {len(page_source)}")
            logger.debug(f"Number of <a> tags found: {len(self.driver.find_elements(By.TAG_NAME, 'a'))}")
            
            return page_source
            
        except Exception as e:
            logger.error(f"Error fetching page with Selenium: {str(e)}")
            return None

    def get_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all valid links from a BeautifulSoup object."""
        links = []
        try:
            logger.debug("Starting link extraction")
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                logger.debug(f"Found link: {href}")
                
                # Skip empty or javascript links
                if not href or href.startswith(('javascript:', '#', 'mailto:', 'tel:')):
                    continue
                    
                if href.startswith(('http://', 'https://')):
                    absolute_url = href
                else:
                    absolute_url = urljoin(self.base_url, href)
                
                logger.debug(f"Converted to absolute URL: {absolute_url}")
                
                if self.should_follow_link(absolute_url):
                    links.append(absolute_url)
                    logger.debug(f"Added link: {absolute_url}")
            
            unique_links = list(set(links))
            logger.debug(f"Total unique links found: {len(unique_links)}")
            return unique_links
            
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []

    def should_follow_link(self, url: str) -> bool:
        """Check if a link should be followed based on configuration.
        
        Args:
            url: URL to check
            
        Returns:
            True if the link should be followed, False otherwise
        """
        if url in self.visited_urls:
            return False
            
        parsed_url = urlparse(url)
        
        # Check if URL is from the same domain
        if parsed_url.netloc != urlparse(self.base_url).netloc:
            return False
            
        # Check if path matches selected paths
        if self.selected_paths:
            path = parsed_url.path
            return any(path.startswith(selected_path) for selected_path in self.selected_paths)
            
        return True

    def get_path_categories(self, links: List[str]) -> Set[str]:
        """Extract unique path categories from a list of links.
        
        Args:
            links: List of URLs to analyze
            
        Returns:
            Set of unique path categories found
        """
        categories = set()
        base_domain = urlparse(self.base_url).netloc
        
        for link in links:
            parsed = urlparse(link)
            if parsed.netloc == base_domain:
                path_parts = parsed.path.split('/')
                if len(path_parts) > 1:
                    # Add first path component (e.g., /docs, /api, etc.)
                    categories.add('/' + path_parts[1])
        
        return categories

    def is_valid_file_type(self, url: str) -> bool:
        """Check if the URL points to an allowed file type."""
        ext = Path(urlparse(url).path).suffix.lower()
        if ext in self.excluded_types:
            return False
        
        mime_type, _ = mimetypes.guess_type(url)
        if mime_type and not mime_type.startswith(('text/', 'application/json')):
            return False
            
        return True

    def process_single_url(self, url: str, depth: int) -> List[str]:
        """Process a single URL for parallel execution."""
        try:
            if not self.is_valid_file_type(url):
                return []

            response = self._make_request(url)
            if not response:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if not main_content:
                main_content = soup
            
            # Clean up content
            for tag in main_content.find_all(['script', 'style', 'iframe', 'noscript']):
                tag.decompose()
            
            # Convert to markdown
            title = soup.title.string.strip() if soup.title else urlparse(url).path
            markdown_content = f"# {title}\n\n"
            
            # Add metadata
            markdown_content += f"Source: {url}\n\n"
            
            # Convert HTML to markdown
            html_content = str(main_content)
            markdown_content += self._html_to_markdown(html_content)
            
            # Save the content
            try:
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    f.write(markdown_content + "\n\n---\n\n")
            except Exception as e:
                logger.error(f"Error saving content for {url}: {str(e)}")
            
            if self.progress_bar:
                self.progress_bar.update(1)
                
            if depth < self.max_depth:
                links = self.get_links(soup)
                return [link for link in links if self.should_follow_link(link)]
                
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
        
        return []

    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to markdown format.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            Converted markdown content
        """
        # Initialize html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # No wrapping
        
        # Convert to markdown
        markdown = h.handle(html_content)
        
        # Clean up the markdown
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Remove extra newlines
        markdown = markdown.strip()
        
        return markdown

    def _make_request(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """Make a request with proper error handling and SSL verification options."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            logger.debug(f"Attempting to fetch URL: {url}")
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=False,
                allow_redirects=True
            )
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                logger.debug(f"Content length: {len(response.text)}")
                logger.debug(f"Content type: {response.headers.get('content-type', 'unknown')}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error for {url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error for {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
        return None

    def convert_url_to_markdown(self, url: str):
        """Convert URL and its linked pages to markdown based on configuration."""
        if not self.base_url:
            self.base_url = url
            
            try:
                # Get links from the first page using Selenium
                logger.info(f"Fetching initial URL: {url}")
                page_content = self._get_page_content(url)
                
                if not page_content:
                    raise Exception(f"Failed to fetch content from {url}")
                
                logger.debug("Parsing HTML content")
                soup = BeautifulSoup(page_content, 'html.parser')
                
                logger.debug("Extracting links")
                links = self.get_links(soup)
                logger.info(f"Found {len(links)} links")
                
                categories = self.get_path_categories(links)
                logger.info(f"Found categories: {categories}")
                
                # Create a rich table
                table = Table(title="Discovered URLs from the first page", show_lines=True)
                table.add_column("No", justify="right", style="cyan", no_wrap=True)
                table.add_column("URL", style="green")
                table.add_column("Category", style="magenta")
                
                # Add rows to the table
                for i, link in enumerate(links, 1):
                    parsed = urlparse(link)
                    category = "/" + parsed.path.split('/')[1] if len(parsed.path.split('/')) > 1 else "/"
                    table.add_row(str(i), link, category)
                
                # Print the table
                console.print("\n")
                console.print(table)
                console.print(f"\n[bold cyan]Total URLs discovered:[/] [green]{len(links)}[/]")
                
                # If no paths specified, show available categories
                if not self.selected_paths and categories:
                    console.print("\n[bold]Available path categories:[/]")
                    for cat in sorted(categories):
                        console.print(f"[magenta]•[/] {cat}")
                    console.print("\n[yellow]Please specify paths when creating the Converter instance.[/]")
                    return

            except Exception as e:
                logger.error(f"Error analyzing first page: {str(e)}")
                raise
            finally:
                # Clean up Selenium WebDriver
                if self.driver:
                    self.driver.quit()

        # Process URLs in parallel
        depth = 0
        urls_to_process = [url]
        
        # Initialize progress bar if enabled
        if self.show_progress:
            # Initialize with at least 1 item (the starting URL)
            self.progress_bar = tqdm(total=1, desc="Processing pages")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while urls_to_process and depth < self.max_depth:
                future_to_url = {
                    executor.submit(self.process_single_url, url, depth): url 
                    for url in urls_to_process if url not in self.visited_urls
                }
                
                # Update progress bar total with new URLs found
                if self.show_progress and future_to_url:
                    self.progress_bar.total = len(future_to_url) + (self.progress_bar.n or 0)
                    self.progress_bar.refresh()
                
                urls_to_process = []
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        new_links = future.result()
                        urls_to_process.extend(new_links)
                        self.visited_urls.add(url)
                    except Exception as e:
                        logger.error(f"Error processing {url}: {str(e)}")
                
                depth += 1

        if self.progress_bar:
            self.progress_bar.close()

    def ask_for_configuration(self):
        """Ask user for crawler configuration."""
        questions = [
            inquirer.Text('max_depth',
                         message='Maximum crawling depth (default: 5)',
                         default='5'),
            inquirer.Text('max_workers',
                         message='Number of parallel workers (default: 4)',
                         default='4'),
            inquirer.Checkbox('excluded_types',
                            message='Select file types to exclude:',
                            choices=['.pdf', '.zip', '.exe', '.dmg', '.doc', '.docx'],
                            default=['.pdf', '.zip', '.exe', '.dmg'])
        ]
        
        answers = inquirer.prompt(questions)
        
        self.max_depth = int(answers['max_depth'])
        self.max_workers = int(answers['max_workers'])
        self.excluded_types = set(answers['excluded_types'])

    def convert(self) -> None:
        """Convert all MDX/MD files to a single MD file."""
        try:
            # Ask for configuration before starting
            self.ask_for_configuration()
            
            markdown_files = self.file_handler.find_markdown_files()
            
            with open(self.output_file, 'w', encoding='utf-8') as out_file:
                # Process each Markdown file
                content_blocks = []
                
                # Use tqdm for file processing progress
                for file_path in tqdm(markdown_files, desc="Processing markdown files"):
                    logger.info(f"Processing {file_path}")
                    metadata, content = self.file_handler.read_markdown_file(file_path)
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