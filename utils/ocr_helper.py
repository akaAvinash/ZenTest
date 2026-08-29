"""
OCR helper for the framework — wraps pytesseract so tests can extract text
from images/screenshots where a DOM or API-level assertion isn't available
(canvas-rendered content, downloaded images, PDF page renders, etc).

Requires the Tesseract OCR engine installed on the machine — the
pytesseract package (in requirements.txt) is just a wrapper around it, it
doesn't bundle the engine itself. On Windows:
    winget install --id UB-Mannheim.TesseractOCR -e
"""

import io
import shutil
from pathlib import Path
from typing import Union

import pytesseract
from PIL import Image

from utils.logger import get_logger

logger = get_logger(__name__)

ImageLike = Union[str, Path, bytes, Image.Image]

# Fallback for a shell session whose PATH hasn't picked up a just-installed
# Tesseract yet (Windows only refreshes PATH for new sessions). Once the
# terminal/session is restarted, `tesseract` resolves via PATH directly and
# this fallback is simply unused.
_WINDOWS_FALLBACK_PATH = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

if not shutil.which("tesseract") and _WINDOWS_FALLBACK_PATH.exists():
    pytesseract.pytesseract.tesseract_cmd = str(_WINDOWS_FALLBACK_PATH)


def _to_image(image: ImageLike) -> Image.Image:
    if isinstance(image, Image.Image):
        return image
    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image))
    return Image.open(image)


def extract_text(image: ImageLike) -> str:
    """Run OCR on an image (file path, bytes, or PIL Image) and return the
    text Tesseract extracted from it."""
    text = pytesseract.image_to_string(_to_image(image))
    logger.debug("OCR extracted %d chars", len(text))
    return text


def assert_text_in_image(image: ImageLike, expected_text: str, case_sensitive: bool = False) -> bool:
    """Convenience check: does the OCR'd text from `image` contain
    `expected_text`? Logs the actual extracted text on a miss, to make a
    failing assertion easy to debug."""
    text = extract_text(image)
    haystack, needle = (text, expected_text) if case_sensitive else (text.lower(), expected_text.lower())
    found = needle in haystack
    if not found:
        logger.warning("OCR text did not contain %r. Got: %r", expected_text, text.strip())
    return found


def extract_text_from_screenshot(locator, path: "str | Path | None" = None) -> str:
    """Screenshot a Playwright Page or Locator and OCR the result.

    Useful for content a DOM selector can't reach directly — canvas
    drawings, embedded images, rendered PDF pages, etc. Pass `path` to also
    save the screenshot to disk; otherwise it's OCR'd in memory only.
    """
    screenshot_bytes = locator.screenshot(path=path) if path else locator.screenshot()
    return extract_text(screenshot_bytes)
