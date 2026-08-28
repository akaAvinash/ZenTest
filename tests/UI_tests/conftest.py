import pytest
from utils.api_helper import clear_cart

@pytest.fixture(autouse=True)
def reset_cart():
    clear_cart()
    yield
    clear_cart()