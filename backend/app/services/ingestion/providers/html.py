"""
HTML provider: extract text and optional heading/section structure via BeautifulSoup.
"""

from pathlib import Path

from app.services.ingestion.providers.base import DocumentExtractorProvider
from app.services.ingestion.types import RawExtractionResult


class HtmlProvider(DocumentExtractorProvider):
    """Extract text from HTML; optional structure from headings and sections."""

    def extract(self, file_path: Path, mime_type: str, progress_callback=None) -> RawExtractionResult:
        """
        Parse HTML, strip tags to text, optionally build structure from h1-h6 and sections.
        """
        if not file_path.exists():
            return RawExtractionResult(raw_text="", error=f"File not found: {file_path}")
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return RawExtractionResult(
                raw_text="",
                error="BeautifulSoup4 is not installed; install with: pip install beautifulsoup4",
            )
        try:
            raw_bytes = file_path.read_bytes()
        except OSError as e:
            return RawExtractionResult(raw_text="", error=f"Cannot read file: {e}")
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                html_str = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return RawExtractionResult(
                raw_text="",
                error="Could not decode HTML with UTF-8, UTF-8-sig, latin-1, or cp1252",
            )
        try:
            soup = BeautifulSoup(html_str, "html.parser")
        except Exception as e:
            return RawExtractionResult(raw_text="", error=f"Failed to parse HTML: {e}")
        # Strip script/style
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Optional structure: headings
        structure_blocks: list[dict] = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            structure_blocks.append({
                "tag": tag.name,
                "text": tag.get_text(strip=True),
            })
        structure = None
        if structure_blocks:
            structure = {"type": "html", "headings": structure_blocks}
        return RawExtractionResult(raw_text=text, structure=structure)
