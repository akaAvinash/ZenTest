from utils.api_client import ApiClient
from utils.api_helper import create_product

client = ApiClient()


def test_add_to_cart_exceeding_stock_returns_400():
    product_id = create_product("Limited Stock Item", 3.00, 2)

    res = client.add_to_cart(product_id, 5)
    assert res.status_code == 400
    assert "Only 2 units available" in res.json()["detail"]


def test_checkout_empty_cart_returns_400():
    # reset_cart autouse fixture in root conftest.py already empties
    # the cart before this test runs
    res = client.checkout()
    assert res.status_code == 400
    assert res.json()["detail"] == "Cart is empty"
