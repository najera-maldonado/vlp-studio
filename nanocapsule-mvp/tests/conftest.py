"""Fixtures compartidas para los tests de humo de VLP Studio."""
import pytest

from src.web.app import app as flask_app


@pytest.fixture
def client():
    flask_app.config.update(TESTING=True)
    return flask_app.test_client()
