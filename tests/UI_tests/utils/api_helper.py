import requests
from config import API_URL

def create_product(name: str, price: float, stock: int) -> int:
    "Create product via API and returns product ID"
    res = requests.post(
        f"{API_URL}/api/products", json={"name": name, "price": price, "stock": stock}
    )
    res.raise_for_status()
    return res.json()["product_id"]

def clear_cart():
    requests.post(f"{API_URL}/api/checkout")