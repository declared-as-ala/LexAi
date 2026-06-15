import pytest

from app.services.ingestion.providers.registry import get_provider


def test_registry_returns_txt_provider():
    provider = get_provider("text/plain")
    assert provider.__class__.__name__ == "TxtProvider"


def test_registry_rejects_unknown_type():
    with pytest.raises(ValueError):
        get_provider("application/zip")
