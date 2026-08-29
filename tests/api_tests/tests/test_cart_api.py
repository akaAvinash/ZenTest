from utils.api_client import ApiClient
from utils.api_helper import create_product

client = ApiClient()


def test_add_to_cart_within_stock_limit():
    """API-TC10"""
    product_id = create_product("Within Stock Item", 4.00, 10)

    res = client.add_to_cart(product_id, 5)

    assert res.status_code == 200
    body = res.json()
    assert body["product_id"] == product_id
    assert body["quantity"] == 5
    assert "message" in body


def test_add_to_cart_exceeding_stock_returns_400():
    """API-TC11"""
    product_id = create_product("Limited Stock Item", 3.00, 2)

    res = client.add_to_cart(product_id, 5)
    assert res.status_code == 400
    assert "Only 2 units available" in res.json()["detail"]


def test_add_nonexistent_product_to_cart_returns_404():
    """API-TC12"""
    res = client.add_to_cart(999999, 1)
    assert res.status_code == 404
    assert res.json()["detail"] == "Product not found"


def test_add_same_product_to_cart_twice_merges_quantity():
    """API-TC13: a second add for the same product updates the existing
    cart row's quantity instead of creating a duplicate row."""
    product_id = create_product("Merge Quantity Item", 2.00, 10)

    client.add_to_cart(product_id, 3)
    client.add_to_cart(product_id, 4)

    cart = client.get_cart().json()
    matching_rows = [item for item in cart["items"] if item["product_id"] == product_id]

    assert len(matching_rows) == 1
    assert matching_rows[0]["quantity"] == 7


def test_add_to_cart_quantity_zero_rejected():
    """API-TC14: quantity must be > 0 (Pydantic Field(gt=0))."""
    product_id = create_product("Zero Quantity Item", 2.00, 10)

    res = client.add_to_cart(product_id, 0)
    assert res.status_code == 422


def test_get_cart_returns_correct_totals():
    """API-TC15"""
    product_id = create_product("Cart Totals Item", 5.00, 10)
    client.add_to_cart(product_id, 3)

    cart = client.get_cart().json()
    matching = next(item for item in cart["items"] if item["product_id"] == product_id)

    assert matching["total"] == 5.00 * 3
    assert cart["cart_total"] == sum(item["total"] for item in cart["items"])


def test_get_cart_when_empty():
    """API-TC16: reset_cart autouse fixture already empties the cart
    before this test runs."""
    res = client.get_cart()
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["cart_total"] == 0


def test_remove_item_from_cart():
    """API-TC17"""
    product_id = create_product("Remove Me Item", 2.00, 10)
    client.add_to_cart(product_id, 1)

    res = client.remove_from_cart(product_id)
    assert res.status_code == 200
    assert "message" in res.json()

    cart = client.get_cart().json()
    assert all(item["product_id"] != product_id for item in cart["items"])


def test_remove_item_not_in_cart_returns_404():
    """API-TC18"""
    res = client.remove_from_cart(999999)
    assert res.status_code == 404
    assert res.json()["detail"] == "Product not found in cart"


def test_checkout_with_items_in_cart():
    """API-TC19"""
    product_id = create_product("Checkout Item", 2.00, 10)
    client.add_to_cart(product_id, 1)

    res = client.checkout()
    assert res.status_code == 200
    assert "message" in res.json()

    cart = client.get_cart().json()
    assert cart["items"] == []


def test_checkout_empty_cart_returns_400():
    """API-TC20: reset_cart autouse fixture in root conftest.py already
    empties the cart before this test runs."""
    res = client.checkout()
    assert res.status_code == 400
    assert res.json()["detail"] == "Cart is empty"
