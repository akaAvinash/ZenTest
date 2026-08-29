import requests
from utils.config import API_URL


class ApiClient:
    """Wraps every backend endpoint call in one place. If a path,
    method, or payload shape ever changes, it changes here once —
    not in every test file that touches that endpoint."""

    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url

    # Products
    def get_products(self):
        return requests.get(f"{self.base_url}/api/products")

    def get_product(self, product_id: int):
        return requests.get(f"{self.base_url}/api/products/{product_id}")

    def create_product(self, name: str, price: float, stock: int):
        return requests.post(
            f"{self.base_url}/api/products",
            json={"name": name, "price": price, "stock": stock},
        )

    # Cart
    def add_to_cart(self, product_id: int, quantity: int):
        return requests.post(
            f"{self.base_url}/api/cart",
            json={"product_id": product_id, "quantity": quantity},
        )

    def get_cart(self):
        return requests.get(f"{self.base_url}/api/cart")

    def remove_from_cart(self, product_id: int):
        return requests.delete(f"{self.base_url}/api/cart/{product_id}")

    # Checkout
    def checkout(self):
        return requests.post(f"{self.base_url}/api/checkout")
