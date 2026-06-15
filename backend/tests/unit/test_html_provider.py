from pathlib import Path

from app.services.ingestion.providers.html import HtmlProvider


def test_html_provider_extracts_text_and_headings(tmp_path: Path):
    path = tmp_path / "sample.html"
    path.write_text("<html><body><h1>Title</h1><p>Hello world</p></body></html>", encoding="utf-8")

    result = HtmlProvider().extract(path, "text/html")

    assert result.error is None
    assert "Title" in result.raw_text
    assert result.structure is not None
    assert result.structure["headings"][0]["text"] == "Title"
