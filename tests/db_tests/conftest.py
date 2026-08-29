import pytest


@pytest.fixture(autouse=True)
def reset_cart():
    """Override the root conftest's autouse reset_cart (which clears the
    cart over HTTP against config.API_URL) — db_tests talk to the local
    SQLite file directly and have nothing to do with the deployed app's
    cart, so there's nothing to reset here."""
    yield
