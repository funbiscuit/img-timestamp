from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Temporary directory with test files."""
    return tmp_path


@pytest.fixture
def photo_jpg(tmp_path: Path) -> Path:
    """Creates a minimal JPEG file."""
    path = tmp_path / 'photo.jpg'
    img = Image.new('RGB', (1, 1), color='red')
    img.save(str(path), 'JPEG')
    return path


@pytest.fixture
def photo_png(tmp_path: Path) -> Path:
    """Creates a minimal PNG file."""
    path = tmp_path / 'photo.png'
    img = Image.new('RGB', (1, 1), color='blue')
    img.save(str(path), 'PNG')
    return path


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Empty temporary directory."""
    d = tmp_path / 'empty'
    d.mkdir()
    return d
