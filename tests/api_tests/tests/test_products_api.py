from utils.api_client import ApiClient

client = ApiClient()


def test_get_products_returns_list():
    """API-TC02"""
    res = client.get_products()
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_single_product_by_valid_id():
    """API-TC03"""
    created = client.create_product("Get By Valid ID", 6.50, 4)
    product_id = created.json()["product_id"]

    res = client.get_product(product_id)

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == product_id
    assert body["name"] == "Get By Valid ID"
    assert body["price"] == 6.50
    assert body["stock"] == 4


def test_get_single_product_by_invalid_id():
    """API-TC04"""
    res = client.get_product(999999)
    assert res.status_code == 404
    assert res.json()["detail"] == "Product not found"


def test_create_product_success():
    """API-TC05"""
    res = client.create_product("API Test Widget", 9.99, 5)
    assert res.status_code == 201
    assert "product_id" in res.json()


def test_create_product_missing_required_field_rejected():
    """API-TC06: omitting 'name' entirely triggers a Pydantic validation
    error, distinct from passing an invalid value for a present field."""
    res = client.create_product_raw({"price": 9.99, "stock": 5})
    assert res.status_code == 422


def test_create_product_price_zero_rejected():
    """API-TC07: price must be strictly > 0 (Pydantic Field(gt=0))."""
    res = client.create_product("Zero Price", 0, 5)
    assert res.status_code == 422


def test_create_product_invalid_price_rejected():
    """API-TC08: negative price rejected — the API accepts good input,
    not just rejects it (paired with the zero/negative-stock cases)."""
    res = client.create_product("Bad Product", -5, 5)
    assert res.status_code == 422


def test_create_product_negative_stock_rejected():
    """API-TC09: stock must be >= 0 (Pydantic Field(ge=0))."""
    res = client.create_product("Negative Stock", 5.0, -1)
    assert res.status_code == 422
