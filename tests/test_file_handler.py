import pytest
from pathlib import Path
from src.file_handler import FileHandler
import tempfile
import os

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_file_handler_initialization(temp_dir):
    handler = FileHandler(temp_dir)
    assert handler.input_dir == Path(temp_dir)

def test_file_handler_invalid_dir():
    with pytest.raises(ValueError):
        FileHandler("/nonexistent/directory")

def test_find_mdx_files(temp_dir):
    # Create some test files
    (Path(temp_dir) / "test1.mdx").touch()
    (Path(temp_dir) / "test2.txt").touch()
    os.makedirs(Path(temp_dir) / "subdir")
    (Path(temp_dir) / "subdir" / "test3.mdx").touch()
    
    handler = FileHandler(temp_dir)
    files = handler.find_mdx_files()
    
    assert len(files) == 2
    assert all(f.suffix == '.mdx' for f in files)

def test_create_heading_from_path(temp_dir):
    file_path = Path(temp_dir) / "dir1" / "dir2" / "test.mdx"
    os.makedirs(file_path.parent)
    file_path.touch()
    
    handler = FileHandler(temp_dir)
    heading = handler.create_heading_from_path(file_path)
    
    assert heading.startswith("###")  # Three levels deep
    assert "test" in heading 