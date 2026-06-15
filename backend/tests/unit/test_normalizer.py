from app.services.ingestion.normalizer import normalize
from app.services.ingestion.types import RawExtractionResult


def test_normalizer_preserves_paragraph_breaks():
    raw = RawExtractionResult(raw_text="A   line\n\n\nSecond\tline", warnings=["x"])
    normalized = normalize(raw)
    assert normalized.normalized_text == "A line\n\nSecond line"
    assert normalized.warnings == ["x"]
