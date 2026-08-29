from utils.api_client import ApiClient

client = ApiClient()


def test_get_products_returns_list():
    res = client.get_products()
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_create_product_success():
    res = client.create_product("API Test Widget", 9.99, 5)
    assert res.status_code == 201
    assert "product_id" in res.json()


def test_create_product_invalid_price_rejected():
    # price must be > 0 (Pydantic Field(gt=0) in ProductCreate) —
    # this checks the API rejects bad input, not just accepts good input.
    res = client.create_product("Bad Product", -5, 5)
    assert res.status_code == 422
