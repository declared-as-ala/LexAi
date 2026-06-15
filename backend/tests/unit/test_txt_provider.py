from pathlib import Path

from app.services.ingestion.providers.txt import TxtProvider


def test_txt_provider_reads_utf8(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("bonjour monde", encoding="utf-8")

    result = TxtProvider().extract(path, "text/plain")

    assert result.error is None
    assert result.raw_text == "bonjour monde"
